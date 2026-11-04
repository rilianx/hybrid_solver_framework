// COMPONENT: {"name": "critical_segment_reversal", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [3, 12]}}}
struct JsAnalysisC {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnalysisC(const Model& m) : M(m) {
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
    int opAt(int i, int k) const { return M.op_of[cur[i][k]][i]; }
};

class CriticalSegmentReversal : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnalysisC A;
    int maxLen;
public:
    CriticalSegmentReversal(const Model& m, int L) : M(m), A(m), maxLen(L) {}
    std::vector<char> cflag;
    void allRev(const Sol& s, std::vector<Move>& out, int minLen) {
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            for (int a = 0; a < L; ++a)
                for (int len = minLen; len <= maxLen && a + len - 1 < L; ++len)
                    out.push_back(Move{i, a, a + len - 1, 0, 0, 0, 0});
        }
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        if (!A.feas) {
            allRev(s, out, 3);
            if (out.empty()) allRev(s, out, 2);
            return;
        }
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            if (L < 3) continue;
            cflag.assign(L, 0);
            bool any = false;
            for (int k = 0; k < L; ++k) { cflag[k] = A.crit(A.opAt(i, k)) ? 1 : 0; any |= (bool)cflag[k]; }
            if (!any) continue;
            for (int a = 0; a + 2 < L; ++a) {
                for (int len = 3; len <= maxLen && a + len - 1 < L; ++len) {
                    int b = a + len - 1;
                    if (cflag[a] || cflag[b])
                        out.push_back(Move{i, a, b, 0, 0, 0, 0});
                }
            }
        }
        if (out.empty()) {
            allRev(s, out, 3);
            if (out.empty()) allRev(s, out, 2);
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        auto& v = c[m[0]];
        std::reverse(v.begin() + m[1], v.begin() + m[2] + 1);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        auto& v = A.work[m[0]];
        std::reverse(v.begin() + m[1], v.begin() + m[2] + 1);
        double o2 = M.objective(A.work);
        std::reverse(v.begin() + m[1], v.begin() + m[2] + 1);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)params.get("max_len", 5.0);
    if (L < 3) L = 3;
    return std::make_unique<CriticalSegmentReversal>(model, L);
}
