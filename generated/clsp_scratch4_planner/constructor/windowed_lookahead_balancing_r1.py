from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "windowed_lookahead_balancing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [2, 5]},
    },
}


class WindowedLookaheadBalancing:
    """Constructor por ventanas con anticipación limitada.

    Recorre los ítems y asigna bloques contiguos de demanda a setups ubicados en
    períodos con holgura, mirando una ventana corta hacia delante. La idea es
    concentrar producción en períodos menos cargados y reservar capacidad en los
    picos, equilibrando setups e inventario.
    """

    def __init__(self, problem, window: int = 3):
        self.problem = problem
        self.window = window

    def build(self, inst, rng: Random):
        n_items = inst.n_items
        n_periods = inst.n_periods

        # Holgura disponible por período: capacidad total menos la carga de setups
        # ya comprometida.
        remaining = [float(c) for c in inst.capacity]
        y = [[False] * n_periods for _ in range(n_items)]

        # Ítems en orden determinista, con un pequeño sesgo aleatorio estable
        # para desempatar entre ítems con patrones similares.
        items = list(range(n_items))
        rng.shuffle(items)

        # Prioriza ítems "caros" o con setups más pesados: si van a usar capacidad,
        # mejor asignarlos antes a períodos con mucha holgura.
        items.sort(
            key=lambda i: (
                -sum(inst.demand[i]),
                -inst.setup_time[i],
                -inst.setup_cost[i],
            )
        )

        for i in items:
            demands = inst.demand[i]
            t = 0

            while t < n_periods:
                # Saltar períodos sin demanda pendiente.
                while t < n_periods and demands[t] <= 0.0:
                    t += 1
                if t >= n_periods:
                    break

                # Ventana corta con anticipación limitada.
                end = min(n_periods - 1, t + self.window - 1)
                candidates = [p for p in range(t, end + 1) if remaining[p] > inst.setup_time[i] + 1e-9]
                if not candidates:
                    # Ampliar la búsqueda a todo el horizonte restante si la ventana no alcanza.
                    candidates = [p for p in range(t, n_periods) if remaining[p] > inst.setup_time[i] + 1e-9]

                if not candidates:
                    # Último recurso: el mejor período disponible aunque esté muy justo.
                    candidates = list(range(t, n_periods))

                # Elegir el período con mayor capacidad residual; en empate, uno más cercano
                # al bloque actual para no retrasar demasiado la producción.
                candidates.sort(key=lambda p: (remaining[p], -p), reverse=True)
                chosen = candidates[0]

                # Construir el bloque contiguo de demanda que cabrá en ese setup.
                available = remaining[chosen] - inst.setup_time[i]
                if available <= 1e-9:
                    # Si no cabe producción adicional aquí, probar el siguiente candidato.
                    placed = False
                    for alt in candidates[1:]:
                        available_alt = remaining[alt] - inst.setup_time[i]
                        if available_alt > 1e-9:
                            chosen = alt
                            available = available_alt
                            placed = True
                            break
                    if not placed:
                        # No hay hueco útil: forzar el mejor candidato y seguir.
                        chosen = candidates[0]
                        available = max(0.0, remaining[chosen] - inst.setup_time[i])

                # Acumular demanda hasta agotar la capacidad residual del período elegido.
                q = t
                block_demand = 0.0
                while q < n_periods and block_demand + demands[q] <= available + 1e-9:
                    block_demand += demands[q]
                    q += 1

                if q == t:
                    # La demanda del período actual no cabe completa: reservar al menos
                    # la demanda inmediata y seguir. En instancias válidas esto suele
                    # evitarse, pero dejamos un mínimo bloque para no estancarnos.
                    block_demand = demands[t]
                    q = t + 1

                y[i][chosen] = True
                remaining[chosen] -= block_demand + inst.setup_time[i]

                # Avanzar al primer período aún no cubierto por este bloque.
                t = q

        sol = tuple(tuple(row) for row in y)

        # Reparación conservadora: si la solución no es factible, añadimos setups
        # en períodos con más holgura para ítems con demanda pendiente, sin mutar la
        # solución original. Repetimos unas pocas veces.
        if not self.problem.is_feasible(sol):
            for _ in range(4):
                if self.problem.is_feasible(sol):
                    break

                # Detectar ítems sin ningún setup y forzar uno en un período con mayor holgura.
                rows = [list(r) for r in sol]
                changed = False
                for i in range(n_items):
                    if any(rows[i]):
                        continue
                    best_t = max(range(n_periods), key=lambda p: (remaining[p], -p))
                    rows[i][best_t] = True
                    changed = True

                if changed:
                    sol = tuple(tuple(row) for row in rows)
                    continue

                # Si sigue siendo infactible, activar un setup adicional para ítems
                # con mucha demanda acumulada en los períodos de mayor holgura.
                rows = [list(r) for r in sol]
                for i in range(n_items):
                    if self.problem.is_feasible(tuple(tuple(row) for row in rows)):
                        break
                    best_t = max(range(n_periods), key=lambda p: (remaining[p], -p))
                    rows[i][best_t] = True
                sol = tuple(tuple(row) for row in rows)

        # Último recurso: si todavía no es factible, construir una solución más densa
        # con un setup en cada período con demanda, repartiendo según holgura.
        if not self.problem.is_feasible(sol):
            rows = [[False] * n_periods for _ in range(n_items)]
            for i in range(n_items):
                for t in range(n_periods):
                    if inst.demand[i][t] > 0:
                        rows[i][t] = True
            sol = tuple(tuple(row) for row in rows)

            # Si aun así no es factible, hacer un intento final de diversificación
            # marcando todos los períodos donde queda capacidad residual.
            if not self.problem.is_feasible(sol):
                rows = [list(r) for r in sol]
                for i in range(n_items):
                    if any(rows[i]):
                        continue
                    best_t = max(range(n_periods), key=lambda p: (inst.capacity[p], -p))
                    rows[i][best_t] = True
                sol = tuple(tuple(row) for row in rows)

        return sol


def build_component(problem, window: int = 3):
    return WindowedLookaheadBalancing(problem, window=window)
