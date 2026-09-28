    def score(self, partial, action) -> float:
        state = partial.state
        so, sd = int(action[0]), int(action[1])

        src = state[so]
        dst = state[sd]
        moving = src[-1]

        src_bad_before = self._misplaced_in_stack(src)
        dst_bad_before = self._misplaced_in_stack(dst)
        src_len = len(src)
        dst_len = len(dst)

        # Simulación local barata de la acción.
        new_src = src[:-1]
        new_dst = dst + (moving,)

        src_bad_after = self._misplaced_in_stack(new_src)
        dst_bad_after = self._misplaced_in_stack(new_dst)

        # Reducción del desorden: si mejora, baja el puntaje.
        delta_bad = (src_bad_after + dst_bad_after) - (src_bad_before + dst_bad_before)

        # Preferimos dejar más holgura y equilibrar alturas.
        new_heights = [len(st) for st in state]
        new_heights[so] -= 1
        new_heights[sd] += 1
        imbalance = max(new_heights) - min(new_heights)

        # Pequeña penalización por mover a una pila muy cargada.
        dst_fill = dst_len / max(self.inst.H, 1)

        if len(new_dst) >= 2 and new_dst[-2] < new_dst[-1]:
            lookahead_penalty = 1.0
        else:
            lookahead_penalty = 0.0

        return (
            float(delta_bad)
            + self.lookahead_weight * lookahead_penalty
            + self.balance_weight * imbalance
            + 0.1 * dst_fill
        )
