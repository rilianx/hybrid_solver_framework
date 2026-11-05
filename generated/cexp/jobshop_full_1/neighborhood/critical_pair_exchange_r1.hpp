// COMPONENT: {"name": "critical_pair_exchange", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [2, 15]}, "pair": {"type": "cat", "values": ["one_critical", "both_critical"]}}}
struct JsCritX {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsCritX(const Model& m) : M(m) {
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
    int opAt(int i, int k) const { return M.op_of[cur[i][k]][i]; }
};

class CriticalPairExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCritX A;
    int W;
    bool both;
    std::vector<char> flag;
    static bool ok(const Sol& s, const Move& m) {
        if (m[0] < 0 || m[0] >= (int)s.size()) return false;
        int L = (int)s[m[0]].size();
        return m[1] >= 0 && m[2] >= 0 && m[1] < L && m[2] < L;
    }
public:
    CriticalPairExchange(const Model& m, int w, bool b) : M(m), A(m), W(w), both(b) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (A.feas) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                if (L < 3) continue;
                flag.assign(L, 0);
                bool any = false;
                for (int k = 0; k < L; ++k) { flag[k] = A.crit(A.opAt(i, k)) ? 1 : 0; any |= (bool)flag[k]; }
                if (!any) continue;
                for (int a = 0; a < L; ++a)
                    for (int b = a + 2; b < L && b <= a + W; ++b) {
                        bool take = both ? (flag[a] && flag[b]) : (flag[a] || flag[b]);
                        if (take) out.push_back(Move{i, a, b, 0, 0, 0, 0});
                    }
            }
        }
        if (out.empty())
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                for (int a = 0; a < L; ++a)
                    for (int b = a + 2; b < L && b <= a + W; ++b) out.push_back(Move{i, a, b, 0, 0, 0, 0});
            }
        if (out.empty())
            for (int i = 0; i < (int)s.size(); ++i)
                for (int a = 0; a + 1 < (int)s[i].size(); ++a) out.push_back(Move{i, a, a + 1, 0, 0, 0, 0});
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        if (ok(c, m)) std::swap(c[m[0]][m[1]], c[m[0]][m[2]]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        if (!ok(s, m) || m[1] == m[2]) return 0.0;
        A.ensure(s);
        auto& v = A.work[m[0]];
        std::swap(v[m[1]], v[m[2]]);
        double o2 = M.objective(A.work);
        std::swap(v[m[1]], v[m[2]]);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 6.0);
    if (w < 2) w = 2;
    bool b = params.text("pair", "one_critical") == "both_critical";
    return std::make_unique<CriticalPairExchange>(model, w, b);
}
