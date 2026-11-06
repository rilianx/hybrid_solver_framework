// COMPONENT: {"name": "critical_arc_adjacent_swap_n1", "slot": "neighborhood", "params": {"use_estimate": {"type": "cat", "values": ["yes", "no"]}, "scale_estimate": {"type": "cat", "values": ["yes", "no"]}}}
struct CritSched {
    const Model& md;
    int M = 0, N = 0;
    std::vector<int> jprev, jnext, mprev, mnext, pos, indeg, order;
    std::vector<long long> r, q;
    long long cmax = 0;
    bool feasible = false;
    explicit CritSched(const Model& m) : md(m) {
        M = m.n_machines; N = m.n_ops;
        jprev.assign(N, -1); jnext.assign(N, -1);
        for (int j = 0; j < m.n_jobs; ++j)
            for (int k = 0; k < m.job_len[j]; ++k) {
                int o = m.job_off[j] + k;
                if (k > 0) jprev[o] = o - 1;
                if (k + 1 < m.job_len[j]) jnext[o] = o + 1;
            }
        mprev.assign(N, -1); mnext.assign(N, -1); pos.assign(N, -1); indeg.assign(N, 0);
        r.assign(N, 0); q.assign(N, 0); order.reserve(N);
    }
    long long P(int o) const { return (long long)md.op_proc[o]; }
    void compute(const std::vector<std::vector<int>>& s) {
        feasible = false; cmax = 0;
        std::fill(mprev.begin(), mprev.end(), -1);
        std::fill(mnext.begin(), mnext.end(), -1);
        std::fill(pos.begin(), pos.end(), -1);
        if ((int)s.size() != M) return;
        for (int m = 0; m < M; ++m) {
            int last = -1;
            for (int k = 0; k < (int)s[m].size(); ++k) {
                int j = s[m][k];
                if (j < 0 || j >= md.n_jobs) return;
                int o = md.op_index[(size_t)j * M + m];
                if (o < 0 || pos[o] != -1) return;
                pos[o] = k; mprev[o] = last;
                if (last >= 0) mnext[last] = o;
                last = o;
            }
        }
        order.clear();
        for (int o = 0; o < N; ++o) {
            if (pos[o] < 0) return;
            indeg[o] = (jprev[o] >= 0) + (mprev[o] >= 0);
            r[o] = 0;
            if (indeg[o] == 0) order.push_back(o);
        }
        size_t head = 0;
        while (head < order.size()) {
            int o = order[head++];
            long long f = r[o] + P(o);
            int a = jnext[o];
            if (a >= 0) { if (r[a] < f) r[a] = f; if (--indeg[a] == 0) order.push_back(a); }
            a = mnext[o];
            if (a >= 0) { if (r[a] < f) r[a] = f; if (--indeg[a] == 0) order.push_back(a); }
        }
        if ((int)order.size() < N) return;
        for (int idx = N - 1; idx >= 0; --idx) {
            int o = order[idx];
            long long t = 0;
            int a = jnext[o]; if (a >= 0) t = std::max(t, q[a] + P(a));
            a = mnext[o]; if (a >= 0) t = std::max(t, q[a] + P(a));
            q[o] = t;
            cmax = std::max(cmax, r[o] + P(o) + t);
        }
        feasible = true;
    }
    bool critEdge(int u) const {
        int v = mnext[u];
        if (v < 0) return false;
        return r[u] + P(u) == r[v] && r[u] + P(u) + q[u] == cmax && r[v] + P(v) + q[v] == cmax;
    }
};

class CriticalAdjacentSwap : public hsf::Neighborhood<Model> {
    using Sol = Model::Solution;
    const Model& md;
    CritSched sc;
    Sol cs, w;
    bool has = false, hasobj = false, schedOk = false;
    double cobj = 0;
    bool useEst, scaleEst;
    void ensure(const Sol& s) {
        if (!has || s != cs) { cs = s; w = s; has = true; hasobj = false; schedOk = false; }
    }
    void ensureSched() { if (!schedOk) { sc.compute(cs); schedOk = true; } }
    double objS() { if (!hasobj) { cobj = md.objective(cs); hasobj = true; } return cobj; }
    int opAt(int m, int k) const { return md.op_index[(size_t)cs[m][k] * md.n_machines + m]; }
public:
    CriticalAdjacentSwap(const Model& m, bool ue, bool se) : md(m), sc(m), useEst(ue), scaleEst(se) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        ensure(s); ensureSched();
        if (sc.feasible) {
            for (int m = 0; m < (int)cs.size(); ++m)
                for (int k = 0; k + 1 < (int)cs[m].size(); ++k)
                    if (sc.critEdge(opAt(m, k))) { Move mv{}; mv[0] = m; mv[1] = k; mv[2] = k + 1; out.push_back(mv); }
        }
        if (out.empty())
            for (int m = 0; m < (int)cs.size(); ++m)
                for (int k = 0; k + 1 < (int)cs[m].size(); ++k) { Move mv{}; mv[0] = m; mv[1] = k; mv[2] = k + 1; out.push_back(mv); }
        if (out.empty()) out.push_back(Move{});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        if (mv[1] != mv[2]) std::swap(t[mv[0]][mv[1]], t[mv[0]][mv[2]]);
        return t;
    }
    double delta(const Sol& s, const Move& mv) override {
        ensure(s);
        double base = objS();
        if (mv[1] == mv[2]) return 0.0;
        std::swap(w[mv[0]][mv[1]], w[mv[0]][mv[2]]);
        double v = md.objective(w);
        std::swap(w[mv[0]][mv[1]], w[mv[0]][mv[2]]);
        return v - base;
    }
    bool has_estimate() const override { return useEst; }
    double estimate(const Sol& s, const Move& mv) override {
        ensure(s); ensureSched();
        int m = mv[0], i = mv[1], j = mv[2];
        if (i == j) return 0.0;
        if (!sc.feasible || j != i + 1) return delta(s, mv);
        int u = opAt(m, i), v = opAt(m, j);
        int a = sc.mprev[u], b = sc.mnext[v];
        long long rv = a >= 0 ? sc.r[a] + sc.P(a) : 0;
        int jp = sc.jprev[v]; if (jp >= 0) rv = std::max(rv, sc.r[jp] + sc.P(jp));
        long long ru = rv + sc.P(v);
        jp = sc.jprev[u]; if (jp >= 0) ru = std::max(ru, sc.r[jp] + sc.P(jp));
        long long qu = b >= 0 ? sc.q[b] + sc.P(b) : 0;
        int js = sc.jnext[u]; if (js >= 0) qu = std::max(qu, sc.q[js] + sc.P(js));
        long long qv = qu + sc.P(u);
        js = sc.jnext[v]; if (js >= 0) qv = std::max(qv, sc.q[js] + sc.P(js));
        long long nl = std::max(rv + sc.P(v) + qv, ru + sc.P(u) + qu);
        double scale = 1.0;
        if (scaleEst && sc.cmax > 0) scale = objS() / (double)sc.cmax;
        return (double)(nl - sc.cmax) * scale;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool ue = params.text("use_estimate", "yes") == "yes";
    bool se = params.text("scale_estimate", "yes") == "yes";
    return std::make_unique<CriticalAdjacentSwap>(model, ue, se);
}
