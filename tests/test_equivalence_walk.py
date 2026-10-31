"""La equivalencia de un vecindario optimizado sigue una trayectoria: una caché que no reconoce la solución que
devolvió `apply` cambia las salidas aunque cada solución suelta dé lo mismo."""

from core.validation.equivalence import check_component_equivalent


class Exact:
    def moves(self, s):
        return [0, 1, 2]

    def apply(self, s, m):
        return s + m + 1

    def delta(self, s, m):
        return float(s * 3 - m)


class StaleCache(Exact):
    """Guarda lo que calculó en la primera solución que ve y lo sigue usando."""

    def __init__(self):
        self.base = None

    def delta(self, s, m):
        if self.base is None:
            self.base = s
        return float(self.base * 3 - m)


def test_walk_detects_stale_cache():
    assert check_component_equivalent("neighborhood", Exact(), Exact(), None, [5]).passed
    rep = check_component_equivalent("neighborhood", Exact(), StaleCache(), None, [5])
    assert not rep.passed and "trayectoria" in rep.feedback()
