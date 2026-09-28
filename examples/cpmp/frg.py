"""FRG: *fill-and-reduce greedy* para el CPMP (Araya y Toledo 2023, Oper. Res. 23:51).

    mientras el layout no esté ordenado:
        si no hay pila en reducción (sr = ∅) y existe un movimiento BG:
            hacer el BG de menor g(sd) − g(so)              # llenar pilas ordenadas
        si no:
            sr ← pila a reducir (si sr = ∅)                # menos veces elegida, menor altura, ...
            mover top(sr) a select_destination              # o a su asignación A[c] (v2)
            si stopping_reduction_criterion: sr ← ∅

Es un componente de referencia escrito a mano, como `setup_flip` en el CLSP: entra al
catálogo como constructor (`frg`) y como puntaje (`frg_policy`, en `construction.py`), y
contra él se comparan los puntajes que genere el LLM. La vista constructiva no lo conoce.
El estado propio de FRG (pila en reducción sr, asignación A, destinos Sd, veces que se
redujo cada pila) va en `FRGState`, aparte del `Layout` neutral.

Mejoras de la §4.3, en `FRGConfig`: `prevent` (no generar pilas ordenadas de altura
máxima cuando quedan menos de M = N/S pilas con espacio, y sacar el tope de una cuando
quedan menos de M/2) y `assignment` (`unblocking_assignment` + `gen_seq`: repartir la pila
que se reduce sin que sus contenedores se bloqueen entre sí). FRG⁻ es
`FRGConfig(prevent=False, assignment="never")`.

La asignación está reconstruida desde el texto del paper (el pseudocódigo de los Alg. 5–7
no está completo en la versión de texto) y no reproduce su efecto: en instancias al estilo
CVS evita que FRG no termine (3×5: 0 fallos de 30 contra 5 sin ella) pero cuesta
movimientos donde FRG⁻ ya termina (3×5: 22,8 contra 12,8; 5×7: 45,8 contra 36,4). Por eso
el default es `assignment="fallback"`: `frg` corre sin asignación y, si no ordena el
layout, repite desde el mismo punto con ella. `"always"` es la variante del paper tal como
está aquí.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .layout import Layout

ASSIGNMENT = ("fallback", "always", "never")


@dataclass(frozen=True)
class FRGConfig:
    r: int = 1  # holgura del criterio de parada de la reducción (§4.1)
    prevent: bool = True  # §4.3.1
    assignment: str = "fallback"  # §4.3.2: "fallback" | "always" | "never"

    def __post_init__(self):
        if self.assignment not in ASSIGNMENT:
            raise ValueError(f"assignment desconocido {self.assignment!r}; opciones: {ASSIGNMENT}")


DEFAULT = FRGConfig()
FRG_MINUS = FRGConfig(prevent=False, assignment="never")


@dataclass
class FRGState:
    """Estado interno de FRG. Un movimiento hecho por otro (p.ej. la beam search) lo
    invalida: se sigue con `FRGState()` (sr = ∅), como en el paper."""

    sr: int | None = None
    A: dict = field(default_factory=dict)  # posición (desde abajo) en sr → pila destino
    Sd: set | None = None  # destinos que quedan para los no asignados
    reduced: list = field(default_factory=list)  # veces que se eligió cada pila para reducir
    dead: bool = False

    def copy(self) -> "FRGState":
        return FRGState(self.sr, dict(self.A), None if self.Sd is None else set(self.Sd), list(self.reduced), self.dead)

    def reset_reduction(self) -> None:
        self.sr, self.A, self.Sd = None, {}, None


# --- reglas de la §3 ------------------------------------------------------------------
def destination_rank(L: Layout, c: int, sd: int) -> tuple:
    """Orden de `select_destination` (Alg. 1) para poner el contenedor de grupo c en sd:
    XG minimizando g(sd) − c; XB a una desordenada con g(sd) ≤ c minimizando c − g(sd); XB
    a una ordenada (bloquea bien puestos) de menor altura; XB a una desordenada de menor altura."""
    gd = L.g(sd)
    if L.is_sorted_stack(sd):
        return (0, gd - c, sd) if gd >= c else (2, L.h(sd), sd)
    return (1, c - gd, sd) if gd <= c else (3, L.h(sd), sd)


def ranked_destinations(L: Layout, so: int, allowed=None) -> list[int]:
    c = L.g(so)
    cands = [sd for sd in range(L.S) if sd != so and L.e(sd) > 0 and (allowed is None or sd in allowed)]
    return sorted(cands, key=lambda sd: destination_rank(L, c, sd))


def select_destination(L: Layout, so: int, allowed=None) -> int | None:
    ranked = ranked_destinations(L, so, allowed)
    return ranked[0] if ranked else None


def select_bg_move(L: Layout, prevent: bool = True) -> tuple[int, int] | None:
    """Alg. 2: el BG de menor g(sd) − g(so). Con `prevent`, si quedan menos de M = N/S pilas
    con espacio no se crean pilas ordenadas de altura máxima, y con menos de M/2 se admiten
    GG que sacan el tope de una ordenada llena (`prevent`)."""
    M = L.N / L.S
    nonfull = sum(1 for i in range(L.S) if L.e(i) > 0)
    decrease = prevent and nonfull < M / 2
    prevent = prevent and nonfull < M
    best, best_d = None, None
    for so in range(L.S):
        if not L.stacks[so]:
            continue
        sorted_so = L.is_sorted_stack(so)
        if sorted_so and not (decrease and L.h(so) == L.H):
            continue
        c = L.g(so)
        for sd in range(L.S):
            if sd == so or L.e(sd) == 0 or not L.is_sorted_stack(sd) or L.g(sd) < c:
                continue
            if prevent and L.h(sd) + 1 == L.H:
                continue
            d = L.g(sd) - c
            if best_d is None or d < best_d:
                best, best_d = (so, sd), d
    return best


# --- reducción (§4, §4.3) -------------------------------------------------------------
def select_reduce_stack(L: Layout, reduced: list[int]) -> int | None:
    """La menos veces elegida; empate: menor altura; empate: desordenada de mayor grupo
    medio, si no, ordenada de menor grupo medio."""
    cands = [i for i in range(L.S) if L.stacks[i]]
    if not cands:
        return None

    def key(i):
        avg = sum(L.stacks[i]) / L.h(i)
        return (reduced[i], L.h(i), 0 if not L.is_sorted_stack(i) else 1,
                -avg if not L.is_sorted_stack(i) else avg)

    return min(cands, key=key)


def stop_reduction(L: Layout, sr: int, r: int = 1) -> bool:
    """§4.1, con S' = pilas desordenadas distintas de sr: (1) g(sr) ≥ max g(s), s ∈ S'; o
    (2) Σ ub(s) sobre s ∈ S' con g(s) ≤ g(sr) llena al menos e(sr) − r huecos de sr. Solo
    cuando sr ya está ordenada (si no, no puede recibir bien puestos)."""
    if not L.is_sorted_stack(sr):
        return False
    others = [s for s in range(L.S) if s != sr and not L.is_sorted_stack(s)]
    gsr = L.g(sr)
    if all(L.g(s) <= gsr for s in others):
        return True
    return sum(L.ub(s) for s in others if L.g(s) <= gsr) >= L.e(sr) - r


def gen_seq(vals: list[int], min_sz: int) -> list[int]:
    """Alg. 7: índices de la subsecuencia no creciente de `vals` lexicográficamente mayor
    con largo ≥ min_sz ([] si no existe). `lds[i]`: la más larga que empieza en i."""
    n = len(vals)
    lds = [1] * n
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n):
            if vals[j] <= vals[i] and lds[j] + 1 > lds[i]:
                lds[i] = lds[j] + 1
    if not n or max(lds) < min_sz:
        return []
    seq: list[int] = []
    last, last_v = -1, None
    while True:
        pick = None
        for i in range(last + 1, n):
            if (last_v is None or vals[i] <= last_v) and len(seq) + lds[i] >= min_sz:
                if pick is None or vals[i] > vals[pick]:
                    pick = i
        if pick is None:
            return seq
        seq.append(pick)
        last, last_v = pick, vals[pick]


def unblocking_assignment(L: Layout, sr: int) -> tuple[dict[int, int], set[int]]:
    """Alg. 6: asigna los contenedores de sr (en orden de salida, del tope hacia abajo) a
    pilas destino en secuencias no crecientes, para que no se bloqueen entre sí. Devuelve
    (A: posición en sr → destino, Sd: destinos que quedan para los no asignados)."""
    C = list(range(L.h(sr) - 1, -1, -1))  # posiciones desde abajo, en orden de salida
    Sd = {s for s in range(L.S) if s != sr and L.e(s) > 0}
    A: dict[int, int] = {}
    while C and Sd:
        e_total = sum(L.e(s) for s in Sd)
        min_sz = len(C) - e_total + min(L.e(s) for s in Sd)
        vals = [L.stacks[sr][p] for p in C]
        seq = gen_seq(vals, max(min_sz, 1))
        if not seq:
            break
        first = vals[seq[0]]
        options = []
        for sd in Sd:
            m = min(L.e(sd), len(seq))
            if len(C) - m <= e_total - L.e(sd):
                options.append((0 if L.e(sd) == len(seq) else 1, destination_rank(L, first, sd), sd, m))
        if not options:
            break
        _, _, sd, m = min(options)
        chosen = set(seq[:m])
        for j in chosen:
            A[C[j]] = sd
        C = [p for j, p in enumerate(C) if j not in chosen]
        Sd.discard(sd)
    return A, Sd


def start_reduction(L: Layout, st: FRGState, sr: int, assignment: bool = False) -> None:
    if not st.reduced:
        st.reduced = [0] * L.S
    st.sr = sr
    st.reduced[sr] += 1
    st.A, st.Sd = {}, None
    nonfull_others = sum(1 for s in range(L.S) if s != sr and L.e(s) > 0)
    if assignment and nonfull_others < L.h(sr):
        st.A, st.Sd = unblocking_assignment(L, sr)


def reduction_move(L: Layout, st: FRGState, assignment: bool = False) -> tuple[int, int] | None:
    """Alg. 4 / 5: (sr, destino) para el tope de la pila en reducción."""
    if st.sr is None:
        sr = select_reduce_stack(L, st.reduced or [0] * L.S)
        if sr is None:
            return None
        start_reduction(L, st, sr, assignment)
    sr = st.sr
    if not L.stacks[sr]:
        return None
    sd = st.A.get(L.h(sr) - 1)
    if sd is None or sd == sr or L.e(sd) == 0:
        sd = select_destination(L, sr, st.Sd) if st.Sd else None
        if sd is None:
            sd = select_destination(L, sr)
    return None if sd is None else (sr, sd)


# --- algoritmo ------------------------------------------------------------------------
def frg_step(L: Layout, st: FRGState, cfg: FRGConfig = DEFAULT, assignment: bool | None = None) -> tuple[int, int] | None:
    """Una iteración de FRG (Alg. 3) sobre L y st, en su lugar. Devuelve el movimiento hecho,
    o None si no pudo mover (st.dead). `assignment` None: el de `cfg` ("fallback" cuenta
    como sin asignación en una iteración suelta)."""
    use = cfg.assignment == "always" if assignment is None else assignment
    if st.sr is None:
        m = select_bg_move(L, cfg.prevent)
        if m is not None:
            L.move(*m)
            return m
    m = reduction_move(L, st, use)
    if m is None:
        st.reset_reduction()
        st.dead = True
        return None
    L.move(*m)
    if not L.stacks[st.sr] or stop_reduction(L, st.sr, cfg.r):
        st.reset_reduction()
    return m


def default_max_moves(L: Layout) -> int:
    return 20 * L.N + 50


def _run(L: Layout, cfg: FRGConfig, assignment: bool, limit: int) -> bool:
    """False si se traba, pasa el límite de movimientos o entra en ciclo: el mismo layout
    (con la misma pila en reducción) más de S veces. La rotación de la pila a reducir
    (§4.2) puede romper un ciclo, así que se toleran algunas repeticiones."""
    st = FRGState()
    seen: dict = {}
    while not L.is_sorted():
        k = (L.state(), st.sr)
        seen[k] = seen.get(k, 0) + 1
        if seen[k] > L.S or len(L.moves) >= limit or frg_step(L, st, cfg, assignment) is None:
            return False
    return True


def frg(L: Layout, cfg: FRGConfig = DEFAULT, max_moves: int | None = None) -> tuple[Layout, bool]:
    """Corre FRG desde L (sin modificarlo): (layout final, ¿quedó ordenado?). Con
    `assignment="fallback"` se intenta primero sin asignación y, si falla, con ella desde L."""
    extra = default_max_moves(L) if max_moves is None else max_moves
    limit = len(L.moves) + extra
    modes = {"never": [False], "always": [True], "fallback": [False, True]}[cfg.assignment]
    q = L
    for use in modes:
        q = L.copy(track=False)
        if _run(q, cfg, use, limit):
            return q, True
    return q, False


__all__ = ["FRGConfig", "FRGState", "DEFAULT", "FRG_MINUS", "destination_rank", "ranked_destinations",
           "select_destination", "select_bg_move", "select_reduce_stack", "stop_reduction", "gen_seq",
           "unblocking_assignment", "start_reduction", "reduction_move", "frg_step", "frg", "default_max_moves"]
