// COMPONENT: {"name": "granular_two_opt_star", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 40]}, "use_reversed": {"type": "int", "range": [0, 1]}}}
class GranularTwoOptStar : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K;
    bool useRev;
    std::vector<int> nb, rof, pof;
    std::vector<int> b1, b2;
    bool valid(int c) const { return c >= 1 && c <= M.n; }
    double cost(const std::vector<int>& r) const {
        double d = 0.0, load = 0.0; int prev = 0; bool any = false;
        for (int c : r) {
            if (!valid(c)) continue;
            d += M.dist(prev, c); load += M.demand[c]; prev = c; any = true;
        }
        if (any) d += M.dist(prev, 0);
        if (load > M.capacity + 1e-9) d += M.penalty * (load - M.capacity);
        return d;
    }
    void locate(const S& s) {
        std::fill(rof.begin(), rof.end(), -1);
        for (int r = 0; r < (int)s.size(); ++r)
            for (int p = 0; p < (int)s[r].size(); ++p) {
                int c = s[r][p];
                if (valid(c) && rof[c] < 0) { rof[c] = r; pof[c] = p; }
            }
    }
    // construye las dos rutas nuevas de un movimiento inter-ruta
    void build(const S& s, const hsf::Move& m, std::vector<int>& a, std::vector<int>& b) const {
        const auto& R1 = s[m[1]]; const auto& R2 = s[m[3]];
        int i = m[2], j = m[4];
        a.assign(R1.begin(), R1.begin() + (i + 1));
        b.clear();
        if (m[0] == 1) {
            a.insert(a.end(), R2.begin() + (j + 1), R2.end());
            b.assign(R2.begin(), R2.begin() + (j + 1));
            b.insert(b.end(), R1.begin() + (i + 1), R1.end());
        } else {
            for (int t = j; t >= 0; --t) a.push_back(R2[t]);
            for (int t = (int)R1.size() - 1; t > i; --t) b.push_back(R1[t]);
            b.insert(b.end(), R2.begin() + (j + 1), R2.end());
        }
    }
public:
    GranularTwoOptStar(const Model& m, int k, bool ur) : M(m), useRev(ur) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        nb.assign((size_t)(n + 1) * std::max(K, 1), 0);
        std::vector<int> cand;
        for (int c = 1; c <= n && K > 0; ++c) {
            cand.clear();
            for (int v = 1; v <= n; ++v) if (v != c) cand.push_back(v);
            std::partial_sort(cand.begin(), cand.begin() + K, cand.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) nb[(size_t)c * K + t] = cand[t];
        }
        rof.assign(n + 1, -1); pof.assign(n + 1, -1);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        locate(s);
        int SZ = (int)s.size();
        for (int r = 0; r < SZ; ++r) {
            for (int i = 0; i < (int)s[r].size(); ++i) {
                int u = s[r][i];
                if (!valid(u) || rof[u] != r || pof[u] != i) continue;
                for (int t = 0; t < K; ++t) {
                    int v = nb[(size_t)u * K + t];
                    if (rof[v] < 0) continue;
                    int r2 = rof[v], q = pof[v];
                    if (r2 == r) {
                        if (i + 1 < q) out.push_back({0, r, i + 1, q, 0, u, v});
                        else if (q + 1 < i) out.push_back({0, r, q + 1, i, 0, u, v});
                    } else {
                        out.push_back({1, r, i, r2, q - 1, u, v});
                        if (useRev) out.push_back({2, r, i, r2, q, u, v});
                    }
                }
            }
        }
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (s[r].size() >= 2) { out.push_back({0, r, 0, (int)s[r].size() - 1, 0, 0, 0}); break; }
            if (out.empty() && SZ >= 2) out.push_back({1, 0, (int)s[0].size() - 1, 1, -1, 0, 0});
            if (out.empty() && SZ >= 1) out.push_back({0, 0, 0, 0, 0, 0, 0});
        }
    }
    S apply(const S& s, const hsf::Move& m) override {
        S t = s;
        if (m[0] == 0) {
            std::reverse(t[m[1]].begin() + m[2], t[m[1]].begin() + m[3] + 1);
            return t;
        }
        std::vector<int> a, b;
        build(s, m, a, b);
        int r1 = m[1], r2 = m[3];
        t[r1] = std::move(a);
        t[r2] = std::move(b);
        int hi = std::max(r1, r2), lo = std::min(r1, r2);
        if (t[hi].empty()) t.erase(t.begin() + hi);
        if (t[lo].empty()) t.erase(t.begin() + lo);
        return t;
    }
    inline double pen(double load) const {
        return load > M.capacity + 1e-9 ? M.penalty * (load - M.capacity) : 0.0;
    }
    double delta(const S& s, const hsf::Move& m) override {
        const int n = M.n;
        const double* dem = M.demand.data();
        if (m[0] == 0) {
            const auto& A = s[m[1]];
            const int* a = A.data();
            int L = (int)A.size();
            int lo = m[2], hi = m[3];
            if (L == 0 || lo > hi || hi >= L) return 0.0;
            int f = -1, l = -1;
            for (int t = lo; t <= hi; ++t) { int c = a[t]; if (c >= 1 && c <= n) { f = c; break; } }
            if (f < 0) return 0.0;
            for (int t = hi; t >= lo; --t) { int c = a[t]; if (c >= 1 && c <= n) { l = c; break; } }
            int pa = 0, na = 0;
            for (int t = lo - 1; t >= 0; --t) { int c = a[t]; if (c >= 1 && c <= n) { pa = c; break; } }
            for (int t = hi + 1; t < L; ++t) { int c = a[t]; if (c >= 1 && c <= n) { na = c; break; } }
            return M.dist(pa, l) + M.dist(f, na) - M.dist(pa, f) - M.dist(l, na);
        }
        const auto& R1 = s[m[1]]; const auto& R2 = s[m[3]];
        const int* a = R1.data(); const int* b = R2.data();
        int L1 = (int)R1.size(), L2 = (int)R2.size();
        int i = m[2], j = m[4];
        int p1 = 0, s1 = 0, p2 = 0, s2 = 0;
        double t1 = 0.0, t2 = 0.0;
        for (int x = 0; x <= i; ++x) { int c = a[x]; if (c >= 1 && c <= n) { t1 += dem[c]; p1 = c; } }
        double pre1 = t1;
        for (int x = i + 1; x < L1; ++x) { int c = a[x]; if (c >= 1 && c <= n) { t1 += dem[c]; if (!s1) s1 = c; } }
        for (int x = 0; x <= j; ++x) { int c = b[x]; if (c >= 1 && c <= n) { t2 += dem[c]; p2 = c; } }
        double pre2 = t2;
        for (int x = j + 1; x < L2; ++x) { int c = b[x]; if (c >= 1 && c <= n) { t2 += dem[c]; if (!s2) s2 = c; } }
        double la, lb, dd;
        if (m[0] == 1) {
            la = pre1;
            for (int x = j + 1; x < L2; ++x) { int c = b[x]; if (c >= 1 && c <= n) la += dem[c]; }
            lb = pre2;
            for (int x = i + 1; x < L1; ++x) { int c = a[x]; if (c >= 1 && c <= n) lb += dem[c]; }
            dd = M.dist(p1, s2) + M.dist(p2, s1) - M.dist(p1, s1) - M.dist(p2, s2);
        } else {
            la = pre1;
            for (int x = j; x >= 0; --x) { int c = b[x]; if (c >= 1 && c <= n) la += dem[c]; }
            lb = 0.0;
            for (int x = L1 - 1; x > i; --x) { int c = a[x]; if (c >= 1 && c <= n) lb += dem[c]; }
            for (int x = j + 1; x < L2; ++x) { int c = b[x]; if (c >= 1 && c <= n) lb += dem[c]; }
            dd = M.dist(p1, p2) + M.dist(s1, s2) - M.dist(p1, s1) - M.dist(p2, s2);
        }
        return dd + pen(la) + pen(lb) - pen(t1) - pen(t2);
    }
    hsf::Move tabu_key(const hsf::Move& m) override {
        return {-2, std::min(m[5], m[6]), std::max(m[5], m[6]), 0, 0, 0, 0};
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    int ur = (int)params.get("use_reversed", 1);
    return std::make_unique<GranularTwoOptStar>(model, k, ur != 0);
}
