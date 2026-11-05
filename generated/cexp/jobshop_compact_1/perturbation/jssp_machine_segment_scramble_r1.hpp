// COMPONENT: {"name": "jssp_machine_segment_scramble", "slot": "perturbation", "params": {"seg_max": {"type": "int", "range": [2, 8]}, "moves_scale": {"type": "float", "range": [0.5, 3.0]}, "scramble_mode": {"type": "cat", "values": ["shuffle", "reverse"]}, "max_tries": {"type": "int", "range": [3, 30]}}}
struct JCoreC {
    using Sol = Model::Solution;
    const Model& md;
    int n, m, N;
    std::vector<int> opJob, opMach, opPrev, opNext, opProc;
    std::vector<int> mp, ms, indeg, topo, pos;
    std::vector<long long> head;
    explicit JCoreC(const Model& mod) : md(mod), n(mod.n), m(mod.m), N(mod.total_ops) {
        opJob.assign(N, -1); opMach.assign(N, -1); opPrev.assign(N, -1); opNext.assign(N, -1); opProc.assign(N, 0);
        for (int j = 0; j < n; ++j) {
            int prev = -1;
            for (const auto& pr : md.routes[j]) {
                int o = md.op_of[j][pr.first];
                opJob[o] = j; opMach[o] = pr.first; opProc[o] = pr.second; opPrev[o] = prev;
                if (prev >= 0) opNext[prev] = o;
                prev = o;
            }
        }
        mp.assign(N, -1); ms.assign(N, -1); indeg.assign(N, 0); pos.assign(N, 0);
        head.assign(N, 0); topo.reserve(N);
    }
    bool load(const Sol& s) {
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        std::fill(indeg.begin(), indeg.end(), 0);
        if ((int)s.size() != m) return false;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            int prev = -1;
            for (int j : s[i]) {
                if (j < 0 || j >= n) return false;
                int o = md.op_of[j][i];
                if (o < 0 || indeg[o]) return false;
                indeg[o] = 1;
                mp[o] = prev; if (prev >= 0) ms[prev] = o; prev = o; ++cnt;
            }
        }
        return cnt == N;
    }
    bool times() {
        topo.clear();
        for (int o = 0; o < N; ++o) {
            indeg[o] = (opPrev[o] >= 0) + (mp[o] >= 0);
            if (!indeg[o]) topo.push_back(o);
        }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = opNext[o];
            if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            a = ms[o];
            if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
        }
        if ((int)topo.size() != N) return false;
        for (int t = 0; t < N; ++t) pos[topo[t]] = t;
        return true;
    }
    bool minspan_swap(Sol& cur) const {
        int best = std::numeric_limits<int>::max(), bi = -1, bt = -1;
        for (int i = 0; i < m; ++i)
            for (int t = 0; t + 1 < (int)cur[i].size(); ++t) {
                int u = md.op_of[cur[i][t]][i], v = md.op_of[cur[i][t + 1]][i];
                int d = pos[v] - pos[u];
                if (d < best) { best = d; bi = i; bt = t; }
            }
        if (bi < 0) return false;
        std::swap(cur[bi][bt], cur[bi][bt + 1]);
        return true;
    }
};

class MachineSegmentScramble : public hsf::Perturbation<Model> {
    JCoreC g; int segMax; double scale; bool rev; int maxTries;
    std::vector<int> cands, saved, perm;

    // round-robin by route index over a random job permutation: always acyclic
    Model::Solution construct(Rng& rng) {
        Model::Solution r(g.m);
        perm.resize(g.n);
        std::iota(perm.begin(), perm.end(), 0);
        std::shuffle(perm.begin(), perm.end(), rng.g);
        size_t maxlen = 0;
        for (int j = 0; j < g.n; ++j) maxlen = std::max(maxlen, g.md.routes[j].size());
        for (size_t k = 0; k < maxlen; ++k)
            for (int j : perm)
                if (k < g.md.routes[j].size()) r[g.md.routes[j][k].first].push_back(j);
        return r;
    }
public:
    MachineSegmentScramble(const Model& md, int sm, double sc, bool rv, int mt)
        : g(md), segMax(std::max(2, sm)), scale(sc), rev(rv), maxTries(std::max(1, mt)) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        bool ok = g.load(s) && g.times();
        if (!ok) return construct(rng);
        cands.clear();
        for (int i = 0; i < g.m; ++i) if (s[i].size() >= 2) cands.push_back(i);
        if (cands.empty()) return s;
        Model::Solution cur = s;
        int moves = std::max(1, (int)std::lround(scale * strength));
        for (int mv = 0; mv < moves; ++mv) {
            for (int tr = 0; tr < maxTries; ++tr) {
                int i = cands[rng.below((int)cands.size())];
                auto& row = cur[i];
                int sz = (int)row.size();
                int L = 2 + rng.below(std::min(segMax, sz) - 1);
                int st = rng.below(sz - L + 1);
                saved.assign(row.begin() + st, row.begin() + st + L);
                if (rev) std::reverse(row.begin() + st, row.begin() + st + L);
                else {
                    std::shuffle(row.begin() + st, row.begin() + st + L, rng.g);
                    if (std::equal(saved.begin(), saved.end(), row.begin() + st)) std::swap(row[st], row[st + 1]);
                }
                if (g.load(cur) && g.times()) break;
                std::copy(saved.begin(), saved.end(), row.begin() + st);
            }
        }
        if (cur == s) {
            g.load(s); g.times();
            g.minspan_swap(cur);
        }
        return cur;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int sm = (int)params.get("seg_max", 4);
    double sc = params.get("moves_scale", 1.0);
    bool rv = params.text("scramble_mode", "shuffle") == "reverse";
    int mt = (int)params.get("max_tries", 10);
    return std::make_unique<MachineSegmentScramble>(model, sm, sc, rv, mt);
}
