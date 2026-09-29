COMPONENT = {'name': 'safe_sorted_insert', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 2.0}}}
from core.rules import RuleMachine

class SafeSortedInsertRule:
    """Permite solo inserciones seguras sobre pilas ya ordenadas."""
    name = 'safe_sorted_insert'
    priority = 100

    def __init__(self, problem, source_bad_weight: float=2.0, destination_slack_weight: float=0.25):
        self.problem = problem
        self.source_bad_weight = source_bad_weight
        self.destination_slack_weight = destination_slack_weight

    def init(self, partial):
        return ()

    def update(self, partial, memory, action):
        return memory

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            if partial.h(sd) == 0 or c <= partial.g(sd):
                if not partial.is_sorted_stack(so) or partial.ub(so) > 0:
                    allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        nxt = partial.copy(track=False)
        nxt.move(action.so, action.sd)
        score = float(nxt.bad()) * 1000.0
        score += float(nxt.ub(action.so)) * self.source_bad_weight
        score -= float(partial.sorted_n[action.sd]) * self.destination_slack_weight
        return score

def build_component(problem, **params):
    source_bad_weight = params.get('source_bad_weight', 2.0)
    destination_slack_weight = params.get('destination_slack_weight', 0.25)
    rule = SafeSortedInsertRule(problem, source_bad_weight=source_bad_weight, destination_slack_weight=destination_slack_weight)
    return RuleMachine(problem, [rule])
