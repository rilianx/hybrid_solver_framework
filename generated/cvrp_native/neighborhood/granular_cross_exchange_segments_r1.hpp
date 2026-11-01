// COMPONENT: {"name": "granular_cross_exchange_segments", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 20]}, "max_seg": {"type": "int", "range": [1, 4]}}}
class CrossExchange : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    CrossExchange(const CVRP& m, int k, int L) : M(m), L(std::max(1, L)) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        nb.assign(n + 1, {});
        std::vector<int> idx;
        for (int c = 1; c <= n; ++c) {
            idx.clear();
            for (int o = 1; o <= n; ++o) if (o != c) idx.push_back(o);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            nb[c].assign(idx.begin(), idx.begin() + K);
        }
        rof.assign(n + 1, -1);
        pof.assign(n + 1, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        std::fill(rof.begin(), rof.end(), -1);
        int R = (int)s.size();
        for (int r = 0; r < R; ++r)
            for (int p = 0; p < (int)s[r].size(); ++p) {
                int c = s[r][p];
                if (c >= 1 && c <= M.n) rof[c] = r, pof[c] = p;
            }
        for (int r1 = 0; r1 < R; ++r1) {
            int len1 = (int)s[r1].size();
            for (int p = 0; p < len1; ++p) {
                int u = s[r1][p];
                if (u < 1 || u > M.n) continue;
                for (int v : nb[u]) {
                    int r2 = rof[v], q = pof[v];
                    if (r2 < 0 || r2 == r1) continue;
                    int len2 = (int)s[r2].size();
                    // nueva arista u -> v: el segmento de r2 que empieza en v va tras u
                    int i = p + 1, j = q;
                    for (int a = 0; a <= std::min(L, len1 - i); ++a)
                        for (int b = 1; b <= std::min(L, len2 - j); ++b) out.push_back({r1, i, a, r2, j, b});
                    // nueva arista v -> u: el segmento de r2 que termina en v va antes de u
                    for (int a = 0; a <= std::min(L, p); ++a)
                        for (int b = 1; b <= std::min(L, q + 1); ++b)
                            out.push_back({r1, p - a, a, r2, q - b + 1, b});
                }
            }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        int r1 = m[0], i = m[1], a = m[2], r2 = m[3], j = m[4], b = m[5];
        const auto& A = s[r1];
        const auto& B = s[r2];
        std::vector<int> na(A.begin(), A.begin() + i);
        na.insert(na.end(), B.begin() + j, B.begin() + j + b);
        na.insert(na.end(), A.begin() + i + a, A.end());
        std::vector<int> nbv(B.begin(), B.begin() + j);
        nbv.insert(nbv.end(), A.begin() + i, A.begin() + i + a);
        nbv.insert(nbv.end(), B.begin() + j + b, B.end());
        t[r1] = std::move(na);
        t[r2] = std::move(nbv);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        int r1 = m[0], i = m[1], a = m[2], r2 = m[3], j = m[4], b = m[5];
        const auto& A = s[r1];
        const auto& B = s[r2];
        int la = (int)A.size(), lb = (int)B.size();
        int p1 = i > 0 ? A[i - 1] : 0, n1 = i + a < la ? A[i + a] : 0;
        int f1 = a ? A[i] : 0, l1 = a ? A[i + a - 1] : 0;
        int p2 = j > 0 ? B[j - 1] : 0, n2 = j + b < lb ? B[j + b] : 0;
        int f2 = b ? B[j] : 0, l2 = b ? B[j + b - 1] : 0;
        double old1 = a ? M.dist(p1, f1) + M.dist(l1, n1) : M.dist(p1, n1);
        double new1 = b ? M.dist(p1, f2) + M.dist(l2, n1) : M.dist(p1, n1);
        double old2 = b ? M.dist(p2, f2) + M.dist(l2, n2) : M.dist(p2, n2);
        double new2 = a ? M.dist(p2, f1) + M.dist(l1, n2) : M.dist(p2, n2);
        double dd = new1 + new2 - old1 - old2;
        double s1 = 0, s2 = 0, L1 = 0, L2 = 0;
        for (int k = 0; k < la; ++k) { double d = M.demand[A[k]]; L1 += d; if (k >= i && k < i + a) s1 += d; }
        for (int k = 0; k < lb; ++k) { double d = M.demand[B[k]]; L2 += d; if (k >= j && k < j + b) s2 += d; }
        double C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - s1 + s2 - C) + std::max(0.0, L2 - s2 + s1 - C) -
                           std::max(0.0, L1 - C) - std::max(0.0, L2 - C));
        return dd;
    }

    Move tabu_key(const Move& m) override { return {m[0], m[1], m[5], m[3], m[4], m[2]}; }

private:
    const CVRP& M;
    int K, L;
    std::vector<std::vector<int>> nb;
    std::vector<int> rof, pof;
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 8);
    int L = (int)params.get("max_seg", 2);
    return std::make_unique<CrossExchange>(model, k, L);
}
