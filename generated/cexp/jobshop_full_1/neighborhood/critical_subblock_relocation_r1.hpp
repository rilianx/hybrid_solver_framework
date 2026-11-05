// COMPONENT: {"name": "critical_subblock_relocation", "slot": "neighborhood", "params": {"max_seg": {"type": "int", "range": [2, 8]}, "window": {"type": "int", "range": [1, 15]}, "seg": {"type": "cat", "values": ["block_ends", "any"]}}}
struct JsCritR {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsCritR(const Model& m) : M(m) {
        int T = M.total_ops;
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
        topo.assign(T, 0); seen.assign(T, 0); r.assign(T, 0); t.assign(T, 0);
        for (auto& v : M.machine_jobs) expected += (int)v.size();
    }
    void ensure(const Model::Solution& s) {
        if (valid && s == cur) return;
        cur = s; work = s; valid = true; compute(s);
    }
    void compute(const Model::Solution& s) {
        obj = M.objective(s);
        int T = M.total_ops;
        std::fill(mp.begin(), mp.end(), -1); std::fill(ms.begin(), ms.end(), -1);
        feas = ((int)s.size() == M.m);
        ++stamp;
        int present = 0;
        int lim = std::min((int)s.size(), M.m);
        for (int i = 0; i < lim; ++i) {
            int prev = -1;
            for (int k = 0; k < (int)s[i].size(); ++k) {
                int j = s[i][k];
                if (j < 0 || j >= M.n || M.op_of[j][i] < 0) { feas = false; continue; }
                int op = M.op_of[j][i];
                if (seen[op] == stamp) { feas = false; continue; }
                seen[op] = stamp; ++present;
                if (prev >= 0) { ms[prev] = op; mp[op] = prev; }
                prev = op;
            }
        }
        if (present != expected) feas = false;
        if (!feas) return;
        int qh = 0, qt = 0;
        for (int o = 0; o < T; ++o) {
            indeg[o] = (M.op_k[o] > 0 ? 1 : 0) + (mp[o] >= 0 ? 1 : 0);
            r[o] = 0;
            if (indeg[o] == 0) topo[qt++] = o;
        }
        cmax = 0;
        while (qh < qt) {
            int o = topo[qh++];
            long long e = r[o] + M.op_proc[o];
            if (e > cmax) cmax = e;
            int a = M.op_next[o];
            if (a >= 0) { if (r[a] < e) r[a] = e; if (--indeg[a] == 0) topo[qt++] = a; }
            int b = ms[o];
            if (b >= 0) { if (r[b] < e) r[b] = e; if (--indeg[b] == 0) topo[qt++] = b; }
        }
        if (qt < T) { feas = false; return; }
        for (int idx = T - 1; idx >= 0; --idx) {
            int o = topo[idx];
            long long best = 0;
            int a = M.op_next[o]; if (a >= 0) best = std::max(best, t[a]);
            int b = ms[o]; if (b >= 0) best = std::max(best, t[b]);
            t[o] = M.op_proc[o] + best;
        }
    }
    bool crit(int o) const { return r[o] + t[o] == cmax; }
    bool critArc(int u, int v) const { return crit(u) && crit(v) && r[u] + M.op_proc[u] == r[v]; }
    int opAt(int i, int k) const { return M.op_of[cur[i][k]][i]; }
};

static void relocate_seg(std::vector<int>& v, int a, int len, int to) {
    if (to < a) std::rotate(v.begin() + to, v.begin() + a, v.begin() + a + len);
    else if (to > a) std::rotate(v.begin() + a, v.begin() + a + len, v.begin() + to + len);
}

class CriticalSubblockRelocation : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCritR A;
    int maxSeg, W;
    bool anySeg;
    static bool ok(const Sol& s, const Move& m) {
        if (m[0] < 0 || m[0] >= (int)s.size()) return false;
        int L = (int)s[m[0]].size();
        int a = m[1], len = m[2], to = m[3];
        return len >= 1 && a >= 0 && a + len <= L && to >= 0 && to <= L - len;
    }
    void addTargets(int i, int L, int a, int len, int w, std::vector<Move>& out) {
        int lo = std::max(0, a - w), hi = std::min(L - len, a + w);
        for (int to = lo; to <= hi; ++to)
            if (to != a) out.push_back(Move{i, a, len, to, 0, 0, 0});
    }
public:
    CriticalSubblockRelocation(const Model& m, int ms_, int w, bool any)
        : M(m), A(m), maxSeg(ms_), W(w), anySeg(any) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (A.feas) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                int a = 0;
                while (a < L) {
                    int b = a;
                    while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                    if (b > a) {
                        int blen = b - a + 1;
                        int top = std::min(maxSeg, blen);
                        for (int len = 2; len <= top; ++len) {
                            if (anySeg) {
                                for (int st = a; st + len - 1 <= b; ++st) addTargets(i, L, st, len, W, out);
                            } else {
                                addTargets(i, L, a, len, W, out);
                                int st2 = b - len + 1;
                                if (st2 != a) addTargets(i, L, st2, len, W, out);
                            }
                        }
                    }
                    a = b + 1;
                }
            }
        }
        if (out.empty()) {
            int w = std::min(W, 3);
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                for (int len = 2; len <= maxSeg; ++len)
                    for (int st = 0; st + len <= L; ++st) addTargets(i, L, st, len, w, out);
            }
        }
        if (out.empty())
            for (int i = 0; i < (int)s.size(); ++i)
                for (int a = 0; a + 1 < (int)s[i].size(); ++a) out.push_back(Move{i, a, 1, a + 1, 0, 0, 0});
        if (out.empty()) out.push_back(Move{0, 0, 1, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        if (ok(c, m)) relocate_seg(c[m[0]], m[1], m[2], m[3]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        if (!ok(s, m) || m[1] == m[3]) return 0.0;
        A.ensure(s);
        auto& v = A.work[m[0]];
        relocate_seg(v, m[1], m[2], m[3]);
        double o2 = M.objective(A.work);
        relocate_seg(v, m[3], m[2], m[1]);
        return o2 - A.obj;
    }
    Move tabu_key(const Move& m) override { return Move{m[0], m[3], m[2], m[1], 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int ms_ = (int)params.get("max_seg", 3.0);
    if (ms_ < 2) ms_ = 2;
    int w = (int)params.get("window", 5.0);
    if (w < 1) w = 1;
    bool any = params.text("seg", "block_ends") == "any";
    return std::make_unique<CriticalSubblockRelocation>(model, ms_, w, any);
}
