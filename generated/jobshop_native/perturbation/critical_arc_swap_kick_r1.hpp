// COMPONENT: {"name": "critical_arc_swap_kick", "slot": "perturbation", "params": {"swaps_per_strength": {"type": "float", "range": [0.5, 4.0]}, "random_swap_prob": {"type": "float", "range": [0.0, 0.5]}}}
class CriticalArcSwapKick : public hsf::Perturbation<JobShop> {
    using Sol = JobShop::Solution;
    const JobShop& M;
    double sps, rprob;
    std::vector<int> start, L, opMach, opIdx, mpred, ptime, eligible;
    std::vector<std::pair<int, int>> arcs;

    Sol repair(const Sol& s) {
        int mk;
        M.schedule(s, start, mk);
        L.resize(M.n_ops);
        std::iota(L.begin(), L.end(), 0);
        std::sort(L.begin(), L.end(), [&](int a, int b) {
            if (start[a] != start[b]) return start[a] < start[b];
            int ka = a - M.off[M.job_of[a]], kb = b - M.off[M.job_of[b]];
            if (ka != kb) return ka < kb;
            return a < b;
        });
        Sol out(M.m);
        for (int op : L) {
            int j = M.job_of[op];
            out[M.routes[j][op - M.off[j]].first].push_back(j);
        }
        return out;
    }
    bool ok(const Sol& c) {
        int mk;
        return M.schedule(c, start, mk) == 0;
    }
    bool random_swap(Sol& cur, Rng& rng, int tries) {
        if (eligible.empty()) return false;
        for (int t = 0; t < tries; ++t) {
            int mm = eligible[rng.below((int)eligible.size())];
            int i = rng.below((int)cur[mm].size() - 1);
            std::swap(cur[mm][i], cur[mm][i + 1]);
            if (ok(cur)) return true;
            std::swap(cur[mm][i], cur[mm][i + 1]);
        }
        return false;
    }
    bool critical_swap(Sol& cur, Rng& rng) {
        int mk;
        M.schedule(cur, start, mk);
        std::fill(mpred.begin(), mpred.end(), -1);
        for (int mm = 0; mm < M.m; ++mm)
            for (int i = 0; i < (int)cur[mm].size(); ++i) {
                int j = cur[mm][i], op = M.off[j] + M.opk[j][mm];
                opMach[op] = mm, opIdx[op] = i;
                if (i > 0) { int pj = cur[mm][i - 1]; mpred[op] = M.off[pj] + M.opk[pj][mm]; }
            }
        int endop = -1, cnt = 0;
        for (int j = 0; j < M.n; ++j) {
            if (M.routes[j].empty()) continue;
            int op = M.off[j + 1] - 1;
            if (start[op] + ptime[op] == mk && rng.below(++cnt) == 0) endop = op;
        }
        if (endop < 0) return false;
        arcs.clear();
        int op = endop;
        while (true) {
            int j = M.job_of[op], k = op - M.off[j];
            int jp = k > 0 ? op - 1 : -1, mp = mpred[op];
            bool cj = jp >= 0 && start[jp] + ptime[jp] == start[op];
            bool cm = mp >= 0 && start[mp] + ptime[mp] == start[op];
            if (!cj && !cm) break;
            if (cm && (!cj || rng.uniform() < 0.5)) { arcs.push_back({opMach[op], opIdx[mp]}); op = mp; }
            else op = jp;
        }
        if (arcs.empty()) return false;
        auto [mm, i] = arcs[rng.below((int)arcs.size())];
        std::swap(cur[mm][i], cur[mm][i + 1]);
        if (ok(cur)) return true;
        std::swap(cur[mm][i], cur[mm][i + 1]);
        return false;
    }

public:
    CriticalArcSwapKick(const JobShop& model, double a, double b) : M(model), sps(a), rprob(b) {
        opMach.assign(M.n_ops, 0), opIdx.assign(M.n_ops, 0), mpred.assign(M.n_ops, -1), ptime.assign(M.n_ops, 0);
        for (int j = 0; j < M.n; ++j)
            for (int k = 0; k < (int)M.routes[j].size(); ++k) ptime[M.off[j] + k] = M.routes[j][k].second;
        for (int mm = 0; mm < M.m; ++mm) if (M.jobs_on(mm).size() >= 2) eligible.push_back(mm);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol cur;
        int mk;
        if (M.sequence_errors(s) == 0 && M.schedule(s, start, mk) == 0) cur = s;
        else cur = repair(s);
        int moves = std::max(1, (int)std::lround(strength * sps));
        for (int t = 0; t < moves; ++t) {
            bool done = false;
            if (rng.uniform() >= rprob) done = critical_swap(cur, rng);
            if (!done) random_swap(cur, rng, 20);
        }
        for (int t = 0; t < 50 && cur == s; ++t) random_swap(cur, rng, 1);
        if (cur == s)
            for (int t = 0; t < 50; ++t) { Sol r = M.random(rng); if (r != s) return r; }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<CriticalArcSwapKick>(model, params.get("swaps_per_strength", 1.5),
                                                 params.get("random_swap_prob", 0.1));
}
