// COMPONENT: {"name": "granular_cross_exchange", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [1, 4]}}}
class GranularCrossExchange : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K, L;
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
    double delta(const S& s, const hsf::Move& m) override {
        build(s, m, b1, b2);
        double old = cost(s[m[0]]);
        if (m[3] < (int)s.size()) old += cost(s[m[3]]);
        return cost(b1) + cost(b2) - old;
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-3, m[6], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 8);
    int l = (int)params.get("max_seg", 3);
    return std::make_unique<GranularCrossExchange>(model, k, l);
}
