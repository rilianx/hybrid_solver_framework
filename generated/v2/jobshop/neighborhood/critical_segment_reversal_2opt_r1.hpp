// COMPONENT: {"name": "critical_segment_reversal_2opt", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 8]}, "extend": {"type": "int", "range": [0, 1]}}}
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

class CriticalSegmentReversal : public hsf::Neighborhood<Model> {
    using Sol = Model::Solution;
    const Model& md;
    CritSched sc;
    Sol cs, w;
    bool has = false, hasobj = false, schedOk = false;
    double cobj = 0;
    int maxLen, ext;
    void ensure(const Sol& s) {
        if (!has || s != cs) { cs = s; w = s; has = true; hasobj = false; schedOk = false; }
    }
    void ensureSched() { if (!schedOk) { sc.compute(cs); schedOk = true; } }
    int opAt(int m, int k) const { return md.op_index[(size_t)cs[m][k] * md.n_machines + m]; }
    static void push(std::vector<Move>& out, int m, int i, int j) { Move mv{}; mv[0] = m; mv[1] = i; mv[2] = j; out.push_back(mv); }
public:
    CriticalSegmentReversal(const Model& m, int ml, int e) : md(m), sc(m), maxLen(ml), ext(e) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        ensure(s); ensureSched();
        if (sc.feasible) {
            for (int m = 0; m < (int)cs.size(); ++m) {
                int L = (int)cs[m].size(), k = 0;
                while (k < L - 1) {
                    if (sc.critEdge(opAt(m, k))) {
                        int a = k;
                        while (k < L - 1 && sc.critEdge(opAt(m, k))) ++k;
                        int b = k;
                        int lo = std::max(0, a - ext), hi = std::min(L - 1, b + ext);
                        for (int i = lo; i <= hi; ++i)
                            for (int j = i + 1; j <= std::min(hi, i + maxLen - 1); ++j)
                                if (std::max(i, a) < std::min(j, b)) push(out, m, i, j);
                    } else ++k;
                }
            }
        }
        if (out.empty()) {
            for (int m = 0; m < (int)cs.size(); ++m) {
                int L = (int)cs[m].size();
                for (int i = 0; i < L; ++i)
                    for (int j = i + 1; j <= std::min(L - 1, i + maxLen - 1); ++j) push(out, m, i, j);
            }
        }
        if (out.empty()) out.push_back(Move{});
    }
    Sol apply(const Sol& s, const Move& mv) override {
        Sol t = s;
        if (mv[1] < mv[2]) std::reverse(t[mv[0]].begin() + mv[1], t[mv[0]].begin() + mv[2] + 1);
        return t;
    }
    double delta(const Sol& s, const Move& mv) override {
        ensure(s);
        if (!hasobj) { cobj = md.objective(cs); hasobj = true; }
        if (mv[1] >= mv[2]) return 0.0;
        auto& row = w[mv[0]];
        std::reverse(row.begin() + mv[1], row.begin() + mv[2] + 1);
        double v = md.objective(w);
        std::reverse(row.begin() + mv[1], row.begin() + mv[2] + 1);
        return v - cobj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ml = (int)params.get("max_len", 4);
    int e = (int)params.get("extend", 1);
    ml = std::max(2, std::min(8, ml));
    e = std::max(0, std::min(1, e));
    return std::make_unique<CriticalSegmentReversal>(model, ml, e);
}
