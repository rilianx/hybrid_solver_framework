from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "items_cronicos",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
    },
}


class ItemsCronicosDestruction:
    """Libera uno o varios ítems completos, o casi completos, a lo largo del horizonte.

    La idea es reestructurar longitudinalmente la política de lotificación de los
    productos más "crónicos" (con más setups), dejando que el reparador replantee
    dónde conviene producirlos y con qué frecuencia.
    """

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods

        # Medimos "cronía" como número de setups activos y, secundariamente,
        # dispersión temporal (span). Queremos atacar ítems completos.
        item_stats = []
        for i in range(n_items):
            periods = [t for t in range(n_periods) if sol[i][t]]
            k = len(periods)
            if k == 0:
                continue
            span = periods[-1] - periods[0] if k > 1 else 0
            item_stats.append((k, span, rng.random(), i))

        # Si no hay setups activos, liberamos al menos una variable al azar.
        if not item_stats:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            free_vars = {var_name(i, t)}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        # Orden: más setups, más dispersión, un pequeño desempate aleatorio.
        item_stats.sort(key=lambda x: (-x[0], -x[1], x[2]))

        target_free = max(1, int(round(ratio * total_vars)))
        free_vars = set()
        chosen_items = []

        for k, span, _, i in item_stats:
            chosen_items.append(i)
            for t in range(n_periods):
                if sol[i][t]:
                    free_vars.add(var_name(i, t))
            if len(free_vars) >= target_free:
                break

        # Si aún no alcanzamos el tamaño deseado y faltan setups activos,
        # añadimos otro ítem crónico completo.
        if len(free_vars) < 1:
            i = item_stats[0][3]
            free_vars.add(var_name(i, next(t for t in range(n_periods) if sol[i][t])))

        # "Casi todos": si el último ítem seleccionado aporta demasiado,
        # podemos dejar algunos setups fijos al azar para no vaciarlo siempre.
        # Mantenemos la intención longitudinal liberando la mayoría de sus setups.
        if chosen_items:
            last_i = chosen_items[-1]
            last_setups = [t for t in range(n_periods) if sol[last_i][t]]
            if len(last_setups) > 2:
                keep_count = 1 if len(last_setups) <= 4 else 2
                to_keep = set(rng.sample(last_setups, k=keep_count))
                for t in last_setups:
                    v = var_name(last_i, t)
                    if v in free_vars and t in to_keep:
                        free_vars.remove(v)

        # Garantía final: al menos una variable liberada.
        if not free_vars:
            i = item_stats[0][3]
            t = next(t for t in range(n_periods) if sol[i][t])
            free_vars.add(var_name(i, t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ItemsCronicosDestruction(problem, problem.inst)
