// COMPONENT: {"name": "granular_cross_exchange", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [1, 4]}}}
class GranularCrossExchange : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K, L;
    std::vector<int> nb, rof, pof;
    std::vector<int> b1, b2;
    size_t lastCount = 0;
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
    // m = {r1, p1, l1, r2, p2, l2, u}; r2 >= |s| significa ruta nueva (vacía)
    void build(const S& s, const hsf::Move& m, std::vector<int>& a, std::vector<int>& b) const {
        static const std::vector<int> empty;
        const auto& A = s[m[0]];
        const auto& B = m[3] < (int)s.size() ? s[m[3]] : empty;
        int p1 = m[1], l1 = m[2], p2 = m[4], l2 = m[5];
        a.assign(A.begin(), A.begin() + p1);
        a.insert(a.end(), B.begin() + p2, B.begin() + p2 + l2);
        a.insert(a.end(), A.begin() + p1 + l1, A.end());
        b.assign(B.begin(), B.begin() + p2);
        b.insert(b.end(), A.begin() + p1, A.begin() + p1 + l1);
        b.insert(b.end(), B.begin() + p2 + l2, B.end());
    }
public:
    GranularCrossExchange(const Model& m, int k, int l) : M(m), L(std::max(1, l)) {
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
        if (out.capacity() < lastCount) out.reserve(lastCount);
        int SZ = (int)s.size();
        for (int r = 0; r < SZ; ++r) {
            int len1 = (int)s[r].size();
            for (int p1 = 0; p1 < len1; ++p1) {
                int u = s[r][p1];
                if (!valid(u) || rof[u] != r || pof[u] != p1) continue;
                for (int t = 0; t < K; ++t) {
                    int v = nb[(size_t)u * K + t];
                    if (rof[v] < 0 || rof[v] == r) continue;
                    int r2 = rof[v], p2 = pof[v] + 1;
                    int len2 = (int)s[r2].size();
                    for (int l1 = 1; l1 <= L && p1 + l1 <= len1; ++l1)
                        for (int l2 = 0; l2 <= L && p2 + l2 <= len2; ++l2)
                            out.push_back({r, p1, l1, r2, p2, l2, u});
                }
            }
        }
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) { out.push_back({r, 0, 1, SZ, 0, 0, s[r][0]}); break; }
        }
        lastCount = out.size();
    }
    S apply(const S& s, const hsf::Move& m) override {
        S t = s;
        std::vector<int> a, b;
        build(s, m, a, b);
        int r1 = m[0], r2 = m[3];
        t[r1] = std::move(a);
        if (r2 >= (int)t.size()) { t.push_back(std::move(b)); r2 = (int)t.size() - 1; }
        else t[r2] = std::move(b);
        int hi = std::max(r1, r2), lo = std::min(r1, r2);
        if (t[hi].empty()) t.erase(t.begin() + hi);
        if (t[lo].empty()) t.erase(t.begin() + lo);
        return t;
    }
    inline double pen(double load) const {
        return load > M.capacity + 1e-9 ? M.penalty * (load - M.capacity) : 0.0;
    }
    // costo de enlace: depósito -> partes no vacías (first,last) -> depósito; 0 = parte vacía
    inline double link(int f0, int l0, int f1, int l1, int f2, int l2) const {
        double d = 0.0; int prev = 0; bool any = false;
        if (f0) { d += M.dist(prev, f0); prev = l0; any = true; }
        if (f1) { d += M.dist(prev, f1); prev = l1; any = true; }
        if (f2) { d += M.dist(prev, f2); prev = l2; any = true; }
        if (any) d += M.dist(prev, 0);
        return d;
    }
    double delta(const S& s, const hsf::Move& m) override {
        const int n = M.n;
        const double* dem = M.demand.data();
        int r1 = m[0], p1 = m[1], l1 = m[2], r2 = m[3], p2 = m[4], l2 = m[5];
        const auto& A = s[r1];
        const int* a = A.data();
        int lenA = (int)A.size();
        int af[3] = {0, 0, 0}, al[3] = {0, 0, 0};
        double loadA = 0.0, segA = 0.0;
        {
            int e1 = p1 + l1;
            for (int i = 0; i < p1; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; if (!af[0]) af[0] = c; al[0] = c;
            }
            for (int i = p1; i < e1; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; segA += dem[c]; if (!af[1]) af[1] = c; al[1] = c;
            }
            for (int i = e1; i < lenA; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; if (!af[2]) af[2] = c; al[2] = c;
            }
        }
        int bf[3] = {0, 0, 0}, bl[3] = {0, 0, 0};
        double loadB = 0.0, segB = 0.0;
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            const int* b = B.data();
            int lenB = (int)B.size();
            int e2 = p2 + l2;
            for (int i = 0; i < p2; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; if (!bf[0]) bf[0] = c; bl[0] = c;
            }
            for (int i = p2; i < e2; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; segB += dem[c]; if (!bf[1]) bf[1] = c; bl[1] = c;
            }
            for (int i = e2; i < lenB; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; if (!bf[2]) bf[2] = c; bl[2] = c;
            }
        }
        double oldL = link(af[0], al[0], af[1], al[1], af[2], al[2])
                    + link(bf[0], bl[0], bf[1], bl[1], bf[2], bl[2]);
        double newL = link(af[0], al[0], bf[1], bl[1], af[2], al[2])
                    + link(bf[0], bl[0], af[1], al[1], bf[2], bl[2]);
        double la = loadA - segA + segB;
        double lb = loadB - segB + segA;
        return (newL - oldL) + pen(la) + pen(lb) - pen(loadA) - pen(loadB);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-3, m[6], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 8);
    int l = (int)params.get("max_seg", 3);
    return std::make_unique<GranularCrossExchange>(model, k, l);
}
