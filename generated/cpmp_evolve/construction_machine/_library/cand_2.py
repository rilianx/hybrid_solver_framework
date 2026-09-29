COMPONENT = {'name': 'repair_bad_top_move_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'allow_relax': {'type': 'bool', 'default': True}, 'tighten_factor': {'type': 'float', 'range': [0.0, 5.0], 'default': 1.0}}}
from core.rules import RuleMachine

class RepairBadTopMoveRefined:
    """Mueve un tope mal puesto a una pila donde quede mejor situado.

    La memoria es hashable: se guarda como un entero (índice de pila) o -1.
    """
    name = 'repair_bad_top_move'

    def __init__(self, prefer_empty=True, allow_relax=True, tighten_factor=1.0, source_penalty=0.5, dest_penalty=0.25):
        self.prefer_empty = bool(prefer_empty)
        self.allow_relax = bool(allow_relax)
        self.tighten_factor = float(tighten_factor)
        self.source_penalty = float(source_penalty)
        self.dest_penalty = float(dest_penalty)

    def start(self, partial, memory):
        stacks = partial.stacks
        h = partial.h
        best = None
        for i in range(partial.S):
            if h(i) <= 1:
                continue
            top = stacks[i][-1]
            below = stacks[i][-2]
            if below < top:
                score = (h(i), -partial.sorted_n[i], i)
                if best is None or score < best[0]:
                    best = (score, i)
        return -1 if best is None else int(best[1])

    def update(self, partial, memory, action):
        source = int(memory) if memory is not None else -1
        if source < 0:
            return -1
        if hasattr(action, 'so') and action.so == source:
            return source
        stacks = partial.stacks
        h = partial.h
        if source >= partial.S or h(source) <= 1:
            return -1
        top = stacks[source][-1]
        below = stacks[source][-2]
        if below >= top:
            return -1
        return source

    def done(self, partial, memory):
        source = int(memory) if memory is not None else -1
        if source < 0:
            return True
        if source >= partial.S:
            return True
        stacks = partial.stacks
        h = partial.h
        if h(source) <= 1:
            return True
        top = stacks[source][-1]
        below = stacks[source][-2]
        return below >= top

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        stacks = partial.stacks
        h = partial.h
        G = partial.G
        source = int(memory) if memory is not None else -1

        def top_group(i):
            return G if h(i) == 0 else stacks[i][-1]

        def is_bad_top_source(so):
            if h(so) <= 1:
                return False
            return stacks[so][-2] < stacks[so][-1]
        strict = []
        relaxed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if h(so) == 0 or h(sd) >= partial.H:
                continue
            if source >= 0 and so != source:
                continue
            if not is_bad_top_source(so):
                continue
            moved = stacks[so][-1]
            dest_top = top_group(sd)
            if h(sd) == 0 or dest_top >= moved:
                strict.append(a)
            elif self.allow_relax:
                if h(sd) == 0 or dest_top >= moved - 1:
                    relaxed.append(a)
        pool = strict if strict else relaxed
        if not pool:
            return []

        def key(a):
            so = a.so
            sd = a.sd
            moved = stacks[so][-1]
            dest_top = top_group(sd)
            empty_score = 0 if self.prefer_empty and h(sd) == 0 else 1
            tighten = abs(dest_top - moved)
            source_rank = (-partial.sorted_n[so], h(so), so)
            dest_rank = (h(sd), sd)
            relax_flag = 0 if a in strict else 1
            return (relax_flag, empty_score, self.tighten_factor * tighten, self.source_penalty * source_rank[0], self.dest_penalty * dest_rank[0], source_rank[1], dest_rank[1])
        pool.sort(key=key)
        return pool

def build_component(problem, **params):
    return RuleMachine(problem, [RepairBadTopMoveRefined(prefer_empty=params.get('prefer_empty', True), allow_relax=params.get('allow_relax', True), tighten_factor=params.get('tighten_factor', 1.0), source_penalty=params.get('source_penalty', 0.5), dest_penalty=params.get('dest_penalty', 0.25))])
