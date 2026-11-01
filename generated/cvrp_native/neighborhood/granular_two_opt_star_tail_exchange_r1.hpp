// COMPONENT: {"name": "granular_two_opt_star_tail_exchange", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class TwoOptStar : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    TwoOptStar(const CVRP& m, int k) : M(m) {
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
        int R = (int)s.size(), empty = -1;
        for (int r = 0; r < R; ++r) {
            if (s[r].empty() && empty < 0) empty = r;
            for (int p = 0; p < (int)s[r].size(); ++p) {
                int c = s[r][p];
                if (c >= 1 && c <= M.n) rof[c] = r, pof[c] = p;
            }
        }
        int target = empty < 0 ? R : empty;
        for (int r1 = 0; r1 < R; ++r1) {
            int len = (int)s[r1].size();
            for (int p = 0; p < len; ++p) {
                int u = s[r1][p];
                if (u < 1 || u > M.n) continue;
                for (int v : nb[u]) {
                    int r2 = rof[v], q = pof[v];
                    if (r2 < 0) continue;
                    if (r2 == r1) {
                        if (q > p + 1) out.push_back({0, r1, p + 1, q, 0, 0});
                        else if (q + 1 < p) out.push_back({0, r1, q + 1, p, 0, 0});
                    } else {
                        add(s, out, r1, p + 1, r2, q);
                        add(s, out, r1, p, r2, q + 1);
                    }
                }
            }
            if (len >= 2 && load(s[r1]) > M.capacity + 1e-9)
                for (int i = 1; i < len; ++i) out.push_back({1, r1, i, target, 0, 0});
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        if (m[0] == 0) {
            auto& r = t[m[1]];
            std::reverse(r.begin() + m[2], r.begin() + m[3] + 1);
            return t;
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        if (r2 >= (int)t.size()) t.emplace_back();
        const auto& A = s[r1];
        std::vector<int> B = r2 < (int)s.size() ? s[r2] : std::vector<int>();
        std::vector<int> na(A.begin(), A.begin() + i), nbv(B.begin(), B.begin() + j);
        na.insert(na.end(), B.begin() + j, B.end());
        nbv.insert(nbv.end(), A.begin() + i, A.end());
        t[r1] = std::move(na);
        t[r2] = std::move(nbv);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        if (m[0] == 0) {
            const auto& r = s[m[1]];
            int i = m[2], j = m[3], len = (int)r.size();
            int a = i > 0 ? r[i - 1] : 0, b = j + 1 < len ? r[j + 1] : 0;
            return M.dist(a, r[j]) + M.dist(r[i], b) - M.dist(a, r[i]) - M.dist(r[j], b);
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        static const std::vector<int> E;
        const auto& A = s[r1];
        const auto& B = r2 < (int)s.size() ? s[r2] : E;
        int l1 = (int)A.size(), l2 = (int)B.size();
        int a1 = i > 0 ? A[i - 1] : 0, b1 = i < l1 ? A[i] : 0;
        int a2 = j > 0 ? B[j - 1] : 0, b2 = j < l2 ? B[j] : 0;
        double dd = M.dist(a1, b2) + M.dist(a2, b1) - M.dist(a1, b1) - M.dist(a2, b2);
        double pre1 = 0, suf1 = 0, pre2 = 0, suf2 = 0;
        for (int k = 0; k < l1; ++k) (k < i ? pre1 : suf1) += M.demand[A[k]];
        for (int k = 0; k < l2; ++k) (k < j ? pre2 : suf2) += M.demand[B[k]];
        double C = M.capacity;
        dd += M.penalty * (std::max(0.0, pre1 + suf2 - C) + std::max(0.0, pre2 + suf1 - C) -
                           std::max(0.0, pre1 + suf1 - C) - std::max(0.0, pre2 + suf2 - C));
        return dd;
    }

private:
    const CVRP& M;
    int K;
    std::vector<std::vector<int>> nb;
    std::vector<int> rof, pof;
    double load(const std::vector<int>& r) const {
        double l = 0.0;
        for (int c : r) if (c >= 1 && c <= M.n) l += M.demand[c];
        return l;
    }
    void add(const Sol& s, std::vector<Move>& out, int r1, int i, int r2, int j) {
        int l1 = (int)s[r1].size(), l2 = (int)s[r2].size();
        if (i < 0 || j < 0 || i > l1 || j > l2) return;
        if ((i == 0 && j == 0) || (i == l1 && j == l2)) return;
        if (r1 > r2) std::swap(r1, r2), std::swap(i, j);
        out.push_back({1, r1, i, r2, j, 0});
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<TwoOptStar>(model, k);
}
