from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "batch_covering_merge",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "merge_window": {"type": "int", "range": [1, 8]},
        "inventory_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class Constructor:
    """Constructor simple: crea setups en bloques de demanda y garantiza cobertura prefix por ítem."""

    def __init__(self, merge_window: int = 2, inventory_bias: float = 0.4):
        self.merge_window = merge_window
        self.inventory_bias = inventory_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        max_single_cap = []
        for i in range(n_items):
            best = 0.0
            for t in range(n_periods):
                best = max(best, float(inst.capacity[t]) - float(inst.setup_time[i]))
            max_single_cap.append(max(best, 0.0))

        for i in range(n_items):
            demand = inst.demand[i]
            total_demand = sum(demand)
            if total_demand <= 1e-12:
                continue

            # Bloques de demanda: cada bloque no debe exceder la mejor capacidad de un único período
            # para ese ítem; así, si la demanda acumulada supera ese umbral, abrimos otro setup.
            block_limit = max(max_single_cap[i], 1e-12)
            acc = 0.0
            first_in_block = None

            for t in range(n_periods):
                dt = float(demand[t])
                if dt <= 1e-12:
                    continue

                if first_in_block is None:
                    first_in_block = t
                    sol[i][t] = True
                    acc = dt
                    continue

                # Si el bloque actual ya no cabe "en un solo período" para este ítem,
                # abrimos un nuevo setup en el propio período de demanda.
                if acc + dt > block_limit + 1e-12:
                    sol[i][t] = True
                    acc = dt
                    first_in_block = t
                else:
                    acc += dt

            # Refuerzo local: si hay huecos de demanda largos, permitimos un segundo setup dentro de la ventana
            # para repartir producción sin hacer movimientos compuestos.
            if self.merge_window > 1:
                last_setup = None
                for t in range(n_periods):
                    if sol[i][t]:
                        if last_setup is not None and t - last_setup > self.merge_window:
                            # Si existe una demanda intermedia, abrir otro setup en el primer período demandado
                            # posterior al último setup, manteniendo movimientos elementales.
                            for k in range(last_setup + 1, t):
                                if demand[k] > 1e-12:
                                    sol[i][k] = True
                                    break
                        last_setup = t

            # Asegura que todo período con demanda quede no más tarde que algún setup del mismo ítem.
            # Si un período demandado quedó antes del primer setup, se abre allí.
            setups = [t for t in range(n_periods) if sol[i][t]]
            if setups:
                first_setup = setups[0]
                for t in range(n_periods):
                    if demand[t] > 1e-12 and t < first_setup:
                        sol[i][t] = True
                        first_setup = t
            else:
                first = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first is not None:
                    sol[i][first] = True

        sol_tuple = tuple(tuple(row) for row in sol)

        # Reparación ligera: si alguna demanda de un ítem supera la capacidad de un solo bloque,
        # añade setups adicionales en períodos demandados para repartir producción.
        sol_tuple = self._repair(inst, sol_tuple, rng)

        return sol_tuple

    def _repair(self, inst: CLSPInstance, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        solm = [list(row) for row in sol]

        for i in range(n_items):
            demand = inst.demand[i]
            if sum(demand) <= 1e-12:
                continue

            max_single = 0.0
            for t in range(n_periods):
                max_single = max(max_single, float(inst.capacity[t]) - float(inst.setup_time[i]))
            max_single = max(max_single, 1e-12)

            # Asegura al menos un setup en el primer período con demanda.
            if not any(solm[i]):
                first = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first is not None:
                    solm[i][first] = True

            # Si la demanda acumulada entre setups excede la mejor capacidad de un solo período,
            # se introduce otro setup en el siguiente período demandado.
            setups = [t for t in range(n_periods) if solm[i][t]]
            if not setups:
                continue

            start = setups[0]
            acc = 0.0
            last_setup = start
            for t in range(start, n_periods):
                dt = float(demand[t])
                if dt <= 1e-12:
                    continue
                acc += dt
                if acc > max_single + 1e-12:
                    # Abrir un nuevo setup en el propio período t para repartir el lote.
                    solm[i][t] = True
                    last_setup = t
                    acc = dt

            # Evita dejar demanda estrictamente antes del primer setup.
            first_setup = next((t for t in range(n_periods) if solm[i][t]), None)
            if first_setup is not None:
                first_dem = next((t for t in range(n_periods) if demand[t] > 1e-12), None)
                if first_dem is not None and first_dem < first_setup:
                    solm[i][first_dem] = True

        return tuple(tuple(row) for row in solm)


def build_component(problem, merge_window: int = 2, inventory_bias: float = 0.4):
    return Constructor(merge_window=merge_window, inventory_bias=inventory_bias)
