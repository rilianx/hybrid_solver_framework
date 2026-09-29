
COMPONENT = {"name": "minimal", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine


def build_component(problem):
    """Máquina mínima: sin reglas todavía; cada paso lo decide el comodín del framework."""
    return RuleMachine(problem, [])
