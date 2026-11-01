// COMPONENT: {"name": "granular_relocate_customer", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class GranularRelocate : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    GranularRelocate(const CVRP& m, int k) : M(m) {
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
            for (int i = 0; i < len; ++i) {
                int c = s[r1][i];
                if (c < 1 || c > M.n) continue;
                for (int v : nb[c]) {
                    int r2 = rof[v], q = pof[v];
                    if (r2 < 0) continue;
                    if (r2 != r1) {
                        out.push_back({r1, i, r2, q, 0, 0});
                        out.push_back({r1, i, r2, q + 1, 0, 0});
                    } else {
                        int qq = q < i ? q : q - 1;
                        if (qq != i) out.push_back({r1, i, r1, qq, 0, 0});
                        if (qq + 1 != i) out.push_back({r1, i, r1, qq + 1, 0, 0});
                    }
                }
                if (len > 1) out.push_back({r1, i, target, 0, 0, 0});
            }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        if (r2 >= (int)t.size()) t.emplace_back();
        int c = t[r1][i];
        t[r1].erase(t[r1].begin() + i);
        t[r2].insert(t[r2].begin() + j, c);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        const auto& A = s[r1];
        int len = (int)A.size();
        int c = A[i];
        int p = i > 0 ? A[i - 1] : 0, nx = i + 1 < len ? A[i + 1] : 0;
        double dd = M.dist(p, nx) - M.dist(p, c) - M.dist(c, nx);
        if (r1 == r2) {
            int mlen = len - 1;
            auto at = [&](int k) { return k < i ? A[k] : A[k + 1]; };
            int a = j > 0 ? at(j - 1) : 0, b = j < mlen ? at(j) : 0;
            return dd + M.dist(a, c) + M.dist(c, b) - M.dist(a, b);
        }
        int a = 0, b = 0;
        double L2 = 0.0;
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            a = j > 0 ? B[j - 1] : 0;
            b = j < (int)B.size() ? B[j] : 0;
            L2 = load(B);
        }
        dd += M.dist(a, c) + M.dist(c, b) - M.dist(a, b);
        double L1 = load(A), dc = M.demand[c], C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - dc - C) - std::max(0.0, L1 - C) +
                           std::max(0.0, L2 + dc - C) - std::max(0.0, L2 - C));
        return dd;
    }

    Move tabu_key(const Move& m) override { return {m[2], m[3], m[0], m[1], 0, 0}; }

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
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<GranularRelocate>(model, k);
}
