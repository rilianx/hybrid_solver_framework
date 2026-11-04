// COMPONENT: {"name": "critical_arc_adjacent_swap", "slot": "neighborhood", "params": {"scope": {"type": "cat", "values": ["critical", "all"]}}}
struct JsAnalysisA {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, pos, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnalysisA(const Model& m) : M(m) {
        int T = M.total_ops;
        mp.assign(T, -1); ms.assign(T, -1); pos.assign(T, 0); indeg.assign(T, 0);
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
                if (j < 0 || j >= M.n || i >= (int)M.op_of[j].size() || M.op_of[j][i] < 0) { feas = false; continue; }
                int op = M.op_of[j][i];
                if (seen[op] == stamp) { feas = false; continue; }
                seen[op] = stamp; pos[op] = k; ++present;
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

class CriticalArcSwap : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnalysisA A;
    bool all;
public:
    CriticalArcSwap(const Model& m, bool a) : M(m), A(m), all(a) {}
    void allSwaps(const Sol& s, std::vector<Move>& out) {
        for (int i = 0; i < (int)s.size(); ++i)
            for (int k = 0; k + 1 < (int)s[i].size(); ++k) out.push_back(Move{i, k, 0, 0, 0, 0, 0});
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (!A.feas || all) { allSwaps(s, out); return; }
        for (int i = 0; i < (int)s.size(); ++i)
            for (int k = 0; k + 1 < (int)s[i].size(); ++k) {
                int u = A.opAt(i, k), v = A.opAt(i, k + 1);
                if (A.critArc(u, v)) out.push_back(Move{i, k, 0, 0, 0, 0, 0});
            }
        if (out.empty()) allSwaps(s, out);
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        std::swap(c[m[0]][m[1]], c[m[0]][m[1] + 1]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        auto& v = A.work[m[0]];
        std::swap(v[m[1]], v[m[1] + 1]);
        double o2 = M.objective(A.work);
        std::swap(v[m[1]], v[m[1] + 1]);
        return o2 - A.obj;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override {
        A.ensure(s);
        if (!A.feas) return delta(s, m);
        int i = m[0], k = m[1];
        int u = A.opAt(i, k), v = A.opAt(i, k + 1);
        auto rr = [&](int x) -> long long { return x >= 0 ? A.r[x] + M.op_proc[x] : 0; };
        auto tt = [&](int x) -> long long { return x >= 0 ? A.t[x] : 0; };
        int jpu = M.op_k[u] > 0 ? u - 1 : -1, jpv = M.op_k[v] > 0 ? v - 1 : -1;
        long long rv = std::max(rr(jpv), rr(A.mp[u]));
        long long ru = std::max(rr(jpu), rv + M.op_proc[v]);
        long long tu = M.op_proc[u] + std::max(tt(M.op_next[u]), tt(A.ms[v]));
        long long tv = M.op_proc[v] + std::max(tt(M.op_next[v]), tu);
        return (double)(std::max(rv + tv, ru + tu) - A.cmax);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool all = params.text("scope", "critical") == "all";
    return std::make_unique<CriticalArcSwap>(model, all);
}
