// COMPONENT: {"name": "job_pair_global_exchange", "slot": "neighborhood", "params": {"scope": {"type": "cat", "values": ["critical", "all"]}}}
struct JsCoreG {
    const Model& M;
    int n, m, T;
    std::vector<int> jp, jn;
    std::vector<long long> p;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0; long long version = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, q;
    int stamp = 0;
    explicit JsCoreG(const Model& md) : M(md), n(md.n), m(md.m), T(md.total_ops) {
        jp.assign(T, -1); jn.assign(T, -1); p.assign(T, 0);
        for (int j = 0; j < n; ++j) {
            const auto& R = M.routes[j]; int prev = -1;
            for (size_t k = 0; k < R.size(); ++k) {
                int o = M.op_of[j][R[k].first];
                p[o] = R[k].second; jp[o] = prev; if (prev >= 0) jn[prev] = o; prev = o;
            }
        }
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0); seen.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    int op(int i, int j) const { return (i >= 0 && i < m && j >= 0 && j < n) ? M.opflat[(size_t)i * n + j] : -1; }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; ++version; obj = M.objective(s); feas = false; cmax = 0;
        ++stamp;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        if ((int)s.size() != m) return;
        int cnt = 0;
        for (int i = 0; i < m; ++i) {
            const auto& seq = s[i];
            for (int k = 0; k < (int)seq.size(); ++k) {
                int o = op(i, seq[k]);
                if (o < 0 || seen[o] == stamp) return;
                seen[o] = stamp; ++cnt;
                if (k > 0) { int pr = op(i, seq[k - 1]); mp[o] = pr; ms[pr] = o; }
            }
        }
        if (cnt != T) return;
        topo.clear();
        for (int o = 0; o < T; ++o) { indeg[o] = (jp[o] >= 0) + (mp[o] >= 0); if (!indeg[o]) topo.push_back(o); }
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jn[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        if ((int)topo.size() != T) return;
        for (int o : topo) {
            long long a = 0;
            if (jp[o] >= 0) a = r[jp[o]] + p[jp[o]];
            if (mp[o] >= 0) a = std::max(a, r[mp[o]] + p[mp[o]]);
            r[o] = a; cmax = std::max(cmax, a + p[o]);
        }
        for (int h = T - 1; h >= 0; --h) {
            int o = topo[h]; long long b = 0;
            if (jn[o] >= 0) b = q[jn[o]] + p[jn[o]];
            if (ms[o] >= 0) b = std::max(b, q[ms[o]] + p[ms[o]]);
            q[o] = b;
        }
        feas = true;
    }
    bool critArc(int u, int v) const { return r[u] + p[u] == r[v] && r[v] + p[v] + q[v] == cmax; }
};

class JobPairGlobalExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCoreG A;
    bool allPairs;
    Sol work; long long workVer = -1;
    std::vector<char> mark;
    std::vector<std::array<int, 3>> undo;

    void exchange(Sol& x, int a, int b, bool rec) {
        if (rec) undo.clear();
        if (a == b) return;
        for (int i = 0; i < (int)x.size(); ++i) {
            auto& seq = x[i]; int ia = -1, ib = -1;
            for (int k = 0; k < (int)seq.size(); ++k) {
                if (seq[k] == a) ia = k; else if (seq[k] == b) ib = k;
            }
            if (ia >= 0 && ib >= 0) { std::swap(seq[ia], seq[ib]); if (rec) undo.push_back({i, ia, ib}); }
        }
    }
public:
    JobPairGlobalExchange(const Model& md, bool all) : M(md), A(md), allPairs(all) {
        mark.assign((size_t)std::max(1, md.n * md.n), 0);
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        int n = A.n;
        if (A.feas && !allPairs) {
            std::vector<int> touched;
            for (int i = 0; i < A.m; ++i) {
                const auto& seq = s[i];
                for (int k = 0; k + 1 < (int)seq.size(); ++k) {
                    int u = A.op(i, seq[k]), v = A.op(i, seq[k + 1]);
                    if (u < 0 || v < 0 || !A.critArc(u, v)) continue;
                    int a = std::min(seq[k], seq[k + 1]), b = std::max(seq[k], seq[k + 1]);
                    int key = a * n + b;
                    if (mark[key]) continue;
                    mark[key] = 1; touched.push_back(key);
                    out.push_back(Move{a, b, 0, 0, 0, 0, 0});
                }
            }
            for (int key : touched) mark[key] = 0;
        }
        if (out.empty()) {
            for (int a = 0; a < n; ++a)
                for (int b = a + 1; b < n; ++b) out.push_back(Move{a, b, 0, 0, 0, 0, 0});
        }
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        exchange(r, mv[0], mv[1], false);
        return r;
    }
    double delta(const Sol& s, const Move& mv) override {
        A.ensure(s);
        if (workVer != A.version) { work = s; workVer = A.version; }
        exchange(work, mv[0], mv[1], true);
        double v = M.objective(work);
        for (int t = (int)undo.size() - 1; t >= 0; --t) std::swap(work[undo[t][0]][undo[t][1]], work[undo[t][0]][undo[t][2]]);
        undo.clear();
        return v - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool all = params.text("scope", "critical") == "all";
    return std::make_unique<JobPairGlobalExchange>(model, all);
}
