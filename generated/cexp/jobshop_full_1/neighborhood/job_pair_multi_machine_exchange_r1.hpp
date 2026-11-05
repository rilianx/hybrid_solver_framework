// COMPONENT: {"name": "job_pair_multi_machine_exchange", "slot": "neighborhood", "params": {"scope": {"type": "cat", "values": ["critical_arcs", "critical_blocks", "all"]}, "span": {"type": "cat", "values": ["adjacent_only", "all_shared"]}}}
struct JsCritJ {
    const Model& M;
    Model::Solution cur, work;
    bool valid = false, feas = false;
    double obj = 0; long long cmax = 0;
    int expected = 0, stamp = 0;
    std::vector<int> mp, ms, indeg, topo, seen, posOf;
    std::vector<long long> r, t;
    explicit JsCritJ(const Model& m) : M(m) {
        int T = M.total_ops;
        mp.assign(T, -1); ms.assign(T, -1); indeg.assign(T, 0);
        topo.assign(T, 0); seen.assign(T, 0); r.assign(T, 0); t.assign(T, 0);
        posOf.assign((size_t)M.m * M.n, -1);
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
        std::fill(posOf.begin(), posOf.end(), -1);
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
                posOf[(size_t)i * M.n + j] = k;
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

class JobPairMultiMachineExchange : public hsf::Neighborhood<Model> {
    const Model& M;
    JsCritJ A;
    int scope;      // 0 arcs, 1 blocks, 2 all
    bool allShared;
    std::vector<char> mark;
    std::vector<int> undo;
    bool okJobs(const Move& m) const {
        return m[0] >= 0 && m[1] >= 0 && m[0] < M.n && m[1] < M.n && m[0] != m[1];
    }
    void add(int x, int y, std::vector<Move>& out) {
        if (x == y || x < 0 || y < 0 || x >= M.n || y >= M.n) return;
        if (x > y) std::swap(x, y);
        char& f = mark[(size_t)x * M.n + y];
        if (!f) { f = 1; out.push_back(Move{x, y, 0, 0, 0, 0, 0}); }
    }
public:
    JobPairMultiMachineExchange(const Model& m, int sc, bool as) : M(m), A(m), scope(sc), allShared(as) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        A.ensure(s);
        mark.assign((size_t)M.n * M.n, 0);
        if (A.feas && scope < 2) {
            for (int i = 0; i < (int)s.size(); ++i) {
                int L = (int)s[i].size();
                int a = 0;
                while (a < L) {
                    int b = a;
                    while (b + 1 < L && A.critArc(A.opAt(i, b), A.opAt(i, b + 1))) ++b;
                    if (b > a) {
                        if (scope == 0) {
                            for (int k = a; k < b; ++k) add(s[i][k], s[i][k + 1], out);
                        } else {
                            for (int p = a; p <= b; ++p)
                                for (int q = p + 1; q <= b; ++q) {
                                    if (!allShared && q != p + 1) continue;
                                    add(s[i][p], s[i][q], out);
                                }
                        }
                    }
                    a = b + 1;
                }
            }
        }
        if (out.empty()) {
            int lim = std::min((int)s.size(), M.m);
            if (!allShared) {
                for (int i = 0; i < lim; ++i)
                    for (int k = 0; k + 1 < (int)s[i].size(); ++k) add(s[i][k], s[i][k + 1], out);
            } else {
                for (int i = 0; i < M.m; ++i) {
                    auto& v = M.machine_jobs[i];
                    for (int p = 0; p < (int)v.size(); ++p)
                        for (int q = p + 1; q < (int)v.size(); ++q) add(v[p], v[q], out);
                }
            }
        }
        if (out.empty()) out.push_back(Move{0, 0, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol c = s;
        if (!okJobs(m)) return c;
        int j1 = m[0], j2 = m[1];
        int lim = std::min((int)c.size(), M.m);
        for (int i = 0; i < lim; ++i) {
            if (M.op_of[j1][i] < 0 || M.op_of[j2][i] < 0) continue;
            int p1 = -1, p2 = -1;
            auto& v = c[i];
            for (int k = 0; k < (int)v.size(); ++k) {
                if (v[k] == j1) { if (p1 < 0) p1 = k; }
                else if (v[k] == j2) { if (p2 < 0) p2 = k; }
                if (p1 >= 0 && p2 >= 0) break;
            }
            if (p1 >= 0 && p2 >= 0 && (allShared || std::abs(p1 - p2) == 1)) std::swap(v[p1], v[p2]);
        }
        return c;
    }
    double delta(const Sol& s, const Move& m) override {
        if (!okJobs(m)) return 0.0;
        A.ensure(s);
        int j1 = m[0], j2 = m[1];
        int lim = std::min((int)s.size(), M.m);
        undo.clear();
        for (int i = 0; i < lim; ++i) {
            int p1 = A.posOf[(size_t)i * M.n + j1], p2 = A.posOf[(size_t)i * M.n + j2];
            if (p1 >= 0 && p2 >= 0 && (allShared || std::abs(p1 - p2) == 1)) {
                std::swap(A.work[i][p1], A.work[i][p2]);
                undo.push_back(i);
            }
        }
        if (undo.empty()) return 0.0;
        double o2 = M.objective(A.work);
        for (int i : undo) {
            int p1 = A.posOf[(size_t)i * M.n + j1], p2 = A.posOf[(size_t)i * M.n + j2];
            std::swap(A.work[i][p1], A.work[i][p2]);
        }
        return o2 - A.obj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string sc = params.text("scope", "critical_arcs");
    int scope = sc == "all" ? 2 : (sc == "critical_blocks" ? 1 : 0);
    bool as = params.text("span", "adjacent_only") == "all_shared";
    return std::make_unique<JobPairMultiMachineExchange>(model, scope, as);
}
