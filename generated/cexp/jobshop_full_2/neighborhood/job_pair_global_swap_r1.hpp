// COMPONENT: {"name": "job_pair_global_swap", "slot": "neighborhood", "params": {"scope": {"type": "cat", "values": ["block_pairs", "adjacent"]}, "window": {"type": "int", "range": [1, 10]}}}
struct JsAnG {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen;
    std::vector<long long> r, t;
    explicit JsAnG(const Model& m) : M(m) {
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

class JobPairGlobalSwap : public hsf::Neighborhood<Model> {
    const Model& M;
    JsAnG A;
    bool blockScope;
    int W;
    std::vector<int> mark;
    int mstamp = 0;
    std::vector<char> share;
    std::vector<std::pair<int, int>> rec;
public:
    JobPairGlobalSwap(const Model& m, bool bs, int w) : M(m), A(m), blockScope(bs), W(w) {
        int n = M.n;
        mark.assign((size_t)n * n, 0);
        share.assign((size_t)n * n, 0);
        for (int x = 0; x < n; ++x)
            for (int y = x + 1; y < n; ++y)
                for (int i = 0; i < M.m; ++i)
                    if (i < (int)M.op_of[x].size() && i < (int)M.op_of[y].size() &&
                        M.op_of[x][i] >= 0 && M.op_of[y][i] >= 0) { share[(size_t)x * n + y] = 1; break; }
    }
    void addPair(int x, int y, std::vector<Move>& out) {
        if (x == y || x < 0 || y < 0 || x >= M.n || y >= M.n) return;
        if (x > y) std::swap(x, y);
        size_t id = (size_t)x * M.n + y;
        if (mark[id] == mstamp) return;
        mark[id] = mstamp;
        out.push_back(Move{x, y, 0, 0, 0, 0, 0});
    }
    void allPairs(std::vector<Move>& out) {
        for (int x = 0; x < M.n; ++x)
            for (int y = x + 1; y < M.n; ++y)
                if (share[(size_t)x * M.n + y]) addPair(x, y, out);
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        ++mstamp;
        if (!A.feas) { allPairs(out); return; }
        for (int i = 0; i < (int)s.size(); ++i) {
            int L = (int)s[i].size();
            int a = 0;
            while (a < L) {
                int b = a;
                while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                if (b > a) {
                    for (int k = a; k < b; ++k) {
                        int hi = blockScope ? std::min(b, k + W) : k + 1;
                        for (int l = k + 1; l <= hi; ++l) addPair(s[i][k], s[i][l], out);
                    }
                }
                a = b + 1;
            }
        }
        if (out.empty()) allPairs(out);
        if (out.empty() && M.n >= 2) out.push_back(Move{0, 1, 0, 0, 0, 0, 0});
    }
    void swapJobs(Sol& c, int x, int y, bool record) {
        if (record) rec.clear();
        for (auto& v : c) {
            int pa = -1, pb = -1;
            for (int k = 0; k < (int)v.size(); ++k) {
                if (pa < 0 && v[k] == x) pa = k;
                else if (pb < 0 && v[k] == y) pb = k;
                if (pa >= 0 && pb >= 0) break;
            }
            if (pa >= 0 && pb >= 0) {
                std::swap(v[pa], v[pb]);
                if (record) rec.push_back({pa, pb});
            } else if (record) rec.push_back({-1, -1});
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        swapJobs(c, m[0], m[1], false);
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        A.ensure(s);
        swapJobs(A.work, m[0], m[1], true);
        double o2 = M.objective(A.work);
        for (int i = 0; i < (int)rec.size(); ++i)
            if (rec[i].first >= 0) std::swap(A.work[i][rec[i].first], A.work[i][rec[i].second]);
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool bs = params.text("scope", "block_pairs") == "block_pairs";
    int w = (int)params.get("window", 3.0);
    if (w < 1) w = 1;
    return std::make_unique<JobPairGlobalSwap>(model, bs, w);
}
