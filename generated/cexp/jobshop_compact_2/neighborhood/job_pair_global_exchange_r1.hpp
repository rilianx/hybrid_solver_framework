// COMPONENT: {"name": "job_pair_global_exchange", "slot": "neighborhood", "params": {"mode": {"type": "cat", "values": ["critical_arcs", "critical_window"]}, "window": {"type": "int", "range": [1, 6]}}}
struct JsInfoP {
    const Model& M;
    int N = 0, NM = 0, T = 0;
    std::vector<int> opJob, opMach, opProc, jPred, jSucc;
    std::vector<std::vector<int>> opOf;
    Model::Solution cur;
    bool valid = false, feas = false;
    double obj = 0;
    long long cmax = 0;
    std::vector<int> mp, ms, pos, indeg, topo;
    std::vector<long long> r, q;
    explicit JsInfoP(const Model& m) : M(m) {
        N = m.n; NM = m.m;
        opOf.assign(N, std::vector<int>(NM, -1));
        for (int j = 0; j < N; ++j) {
            int prev = -1;
            for (const auto& pr : m.routes[j]) {
                int id = T++;
                opJob.push_back(j); opMach.push_back(pr.first); opProc.push_back(pr.second);
                jPred.push_back(prev); jSucc.push_back(-1);
                if (prev >= 0) jSucc[prev] = id;
                if (pr.first >= 0 && pr.first < NM) opOf[j][pr.first] = id;
                prev = id;
            }
        }
        mp.assign(T, -1); ms.assign(T, -1); pos.assign(T, -1); indeg.assign(T, 0);
        r.assign(T, 0); q.assign(T, 0); topo.reserve(T);
    }
    int opAt(const Model::Solution& s, int i, int k) const { return opOf[s[i][k]][i]; }
    void ensure(const Model::Solution& s) { if (!valid || s != cur) compute(s); }
    void compute(const Model::Solution& s) {
        cur = s; valid = true; obj = M.objective(s);
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1); std::fill(pos.begin(), pos.end(), -1);
        for (int i = 0; i < (int)s.size() && i < NM; ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int j = s[i][k]; if (j < 0 || j >= N) continue;
                int o = opOf[j][i]; if (o < 0) continue;
                pos[o] = k;
                if (prev >= 0) { mp[o] = prev; ms[prev] = o; }
                prev = o;
            }
        }
        for (int o = 0; o < T; ++o) indeg[o] = (jPred[o] >= 0) + (mp[o] >= 0);
        topo.clear();
        for (int o = 0; o < T; ++o) if (indeg[o] == 0) topo.push_back(o);
        for (size_t h = 0; h < topo.size(); ++h) {
            int o = topo[h];
            int a = jSucc[o]; if (a >= 0 && --indeg[a] == 0) topo.push_back(a);
            int b = ms[o]; if (b >= 0 && --indeg[b] == 0) topo.push_back(b);
        }
        feas = (int)topo.size() == T;
        cmax = 0;
        if (feas) {
            for (int o : topo) {
                long long v = 0;
                if (jPred[o] >= 0) v = r[jPred[o]] + opProc[jPred[o]];
                if (mp[o] >= 0) v = std::max(v, r[mp[o]] + opProc[mp[o]]);
                r[o] = v; cmax = std::max(cmax, v + opProc[o]);
            }
            for (int h = T - 1; h >= 0; --h) {
                int o = topo[h]; long long v = 0;
                if (jSucc[o] >= 0) v = q[jSucc[o]] + opProc[jSucc[o]];
                if (ms[o] >= 0) v = std::max(v, q[ms[o]] + opProc[ms[o]]);
                q[o] = v;
            }
        } else {
            for (int o = 0; o < T; ++o) r[o] = jPred[o] >= 0 ? r[jPred[o]] + opProc[jPred[o]] : 0;
            for (int o = T - 1; o >= 0; --o) q[o] = jSucc[o] >= 0 ? q[jSucc[o]] + opProc[jSucc[o]] : 0;
            for (int o = 0; o < T; ++o) cmax = std::max(cmax, r[o] + opProc[o] + q[o]);
        }
    }
    bool crit(int o) const { return r[o] + opProc[o] + q[o] == cmax; }
    bool critArc(int u, int v) const { return crit(u) && crit(v) && ms[u] == v && r[u] + opProc[u] == r[v]; }
};

class JobPairGlobalExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsInfoP A;
    int mode, W;
    Sol work;
    std::vector<char> mark;
    std::vector<int> touched;

    void build(const Sol& s, const Move& mv, Sol& out) {
        out = s;
        int a = mv[0], b = mv[1];
        for (auto& seq : out) {
            int pa = -1, pb = -1;
            for (int k = 0; k < (int)seq.size(); ++k) {
                if (seq[k] == a) pa = k; else if (seq[k] == b) pb = k;
            }
            if (pa >= 0 && pb >= 0) std::swap(seq[pa], seq[pb]);
        }
    }
public:
    JobPairGlobalExchange(const Model& m, int md, int w) : M(m), A(m), mode(md), W(w) {
        mark.assign((size_t)std::max(1, A.N) * std::max(1, A.N), 0);
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        auto add = [&](int a, int b) {
            if (a == b) return;
            if (a > b) std::swap(a, b);
            size_t idx = (size_t)a * A.N + b;
            if (!mark[idx]) {
                mark[idx] = 1; touched.push_back((int)idx);
                Move mv{}; mv[0] = a; mv[1] = b; out.push_back(mv);
            }
        };
        if (A.feas) {
            for (int i = 0; i < (int)s.size(); ++i) {
                const auto& seq = s[i]; int L = seq.size();
                if (mode == 0) {
                    for (int k = 1; k < L; ++k)
                        if (A.critArc(A.opAt(s, i, k - 1), A.opAt(s, i, k))) add(seq[k - 1], seq[k]);
                } else {
                    for (int k = 0; k < L; ++k) {
                        if (!A.crit(A.opAt(s, i, k))) continue;
                        for (int d = 1; d <= W; ++d) {
                            if (k + d < L) add(seq[k], seq[k + d]);
                            if (k - d >= 0) add(seq[k], seq[k - d]);
                        }
                    }
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < (int)s.size(); ++i)
                for (int k = 1; k < (int)s[i].size(); ++k) add(s[i][k - 1], s[i][k]);
        }
        for (int idx : touched) mark[idx] = 0;
        touched.clear();
    }
    Sol apply(const Sol& s, const Move& m) override { Sol r; build(s, m, r); return r; }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        double base = A.obj;
        build(s, m, work);
        return M.objective(work) - base;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string md = params.text("mode", "critical_arcs");
    int w = (int)params.get("window", 2);
    w = std::max(1, std::min(6, w));
    return std::make_unique<JobPairGlobalExchange>(model, md == "critical_window" ? 1 : 0, w);
}
