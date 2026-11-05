// COMPONENT: {"name": "critical_block_pair_exchange", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [2, 15]}, "members": {"type": "cat", "values": ["ends", "all"]}}}
struct JsAnX {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnX(const Model& m) : M(m) {
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
                if (j < 0 || j >= M.n || i >= (int)M.op_of[j].size() || M.op_of[j][i] < 0) { feas = false; continue; }
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

class CriticalBlockPairExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnX A;
    int W;
    bool allMembers;
    bool validMove(const Sol& s, const Move& m) const {
        if (m[0] < 0 || m[0] >= (int)s.size()) return false;
        int L = (int)s[m[0]].size();
        return m[1] >= 0 && m[2] >= 0 && m[1] < L && m[2] < L;
    }
    void fallback(const Sol& s, std::vector<Move>& out) {
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            for (int x = 0; x < L; ++x)
                for (int y = x + 2; y <= std::min(L - 1, x + W); ++y) out.push_back(Move{i, x, y, 0, 0, 0, 0});
        }
        if (out.empty())
            for (int i = 0; i < (int)s.size(); ++i)
                for (int x = 0; x + 1 < (int)s[i].size(); ++x) out.push_back(Move{i, x, x + 1, 0, 0, 0, 0});
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
public:
    CriticalBlockPairExchange(const Model& m, int w, bool am) : M(m), A(m), W(w), allMembers(am) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (!A.feas) { fallback(s, out); return; }
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            int a = 0;
            while (a < L) {
                int b = a;
                while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                if (b > a) {
                    for (int x = a; x <= b; ++x) {
                        if (!allMembers && x != a && x != b) continue;
                        for (int y = std::max(0, x - W); y <= std::min(L - 1, x + W); ++y) {
                            if (std::abs(y - x) < 2) continue;
                            out.push_back(Move{i, std::min(x, y), std::max(x, y), 0, 0, 0, 0});
                        }
                    }
                }
                a = b + 1;
            }
        }
        if (out.empty()) { fallback(s, out); return; }
        std::sort(out.begin(), out.end());
        out.erase(std::unique(out.begin(), out.end()), out.end());
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        if (validMove(s, m)) std::swap(c[m[0]][m[1]], c[m[0]][m[2]]);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        if (!validMove(s, m)) return 0.0;
        A.ensure(s);
        auto& v = A.work[m[0]];
        std::swap(v[m[1]], v[m[2]]);
        double o2 = M.objective(A.work);
        std::swap(v[m[1]], v[m[2]]);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 4.0);
    if (w < 2) w = 2;
    bool am = params.text("members", "ends") == "all";
    return std::make_unique<CriticalBlockPairExchange>(model, w, am);
}
