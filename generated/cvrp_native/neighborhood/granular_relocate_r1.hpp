// COMPONENT: {"name": "granular_relocate", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 40]}, "new_route": {"type": "int", "range": [0, 1]}}}
class GranularRelocate : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K;
    bool newRoute;
    std::vector<int> nb, rof, pof;
    std::vector<char> mark;
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
    bool canon(int c, int r, int p) const { return valid(c) && rof[c] == r && pof[c] == p; }
public:
    GranularRelocate(const Model& m, int k, bool nr) : M(m), newRoute(nr) {
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
        rof.assign(n + 1, -1); pof.assign(n + 1, -1); mark.assign(n + 1, 0);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        locate(s);
        int SZ = (int)s.size();
        for (int r = 0; r < SZ; ++r) {
            int len = (int)s[r].size();
            for (int p = 0; p < len; ++p) {
                int c = s[r][p];
                if (!canon(c, r, p)) continue;
                for (int t = 0; t < K; ++t) mark[nb[(size_t)c * K + t]] = 1;
                for (int t = 0; t < K; ++t) {
                    int v = nb[(size_t)c * K + t];
                    if (rof[v] < 0) continue;
                    int rv = rof[v], pv = pof[v];
                    if (rv != r) {
                        out.push_back({r, p, rv, pv + 1, c, 0, 0});
                        bool dup = false;
                        if (pv > 0) { int u = s[rv][pv - 1]; dup = valid(u) && mark[u] && canon(u, rv, pv - 1); }
                        if (!dup) out.push_back({r, p, rv, pv, c, 0, 0});
                    } else {
                        int pvr = pv > p ? pv - 1 : pv;
                        if (pvr + 1 != p) out.push_back({r, p, r, pvr + 1, c, 0, 0});
                        if (pvr != p) {
                            bool dup = false;
                            int pr = pvr - 1;
                            if (pr >= 0) {
                                int orig = pr >= p ? pr + 1 : pr;
                                int u = s[r][orig];
                                dup = valid(u) && mark[u] && canon(u, r, orig);
                            }
                            if (!dup) out.push_back({r, p, r, pvr, c, 0, 0});
                        }
                    }
                }
                for (int t = 0; t < K; ++t) mark[nb[(size_t)c * K + t]] = 0;
                if (newRoute && len > 1) out.push_back({r, p, SZ, 0, c, 0, 0});
            }
        }
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) {
                    if (s[r].size() > 1) out.push_back({r, 0, SZ, 0, s[r][0], 0, 0});
                    else out.push_back({r, 0, r, 0, s[r][0], 0, 0});
                    break;
                }
        }
    }
    S apply(const S& s, const hsf::Move& m) override {
        S t = s;
        int r1 = m[0], p1 = m[1], r2 = m[2], p2 = m[3];
        int c = t[r1][p1];
        t[r1].erase(t[r1].begin() + p1);
        if (r2 >= (int)t.size()) t.push_back({c});
        else t[r2].insert(t[r2].begin() + p2, c);
        if (t[r1].empty()) t.erase(t.begin() + r1);
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        int r1 = m[0], p1 = m[1], r2 = m[2], p2 = m[3];
        const auto& A = s[r1];
        int c = A[p1];
        b1.assign(A.begin(), A.end());
        b1.erase(b1.begin() + p1);
        if (r1 == r2) {
            b1.insert(b1.begin() + p2, c);
            return cost(b1) - cost(A);
        }
        if (r2 >= (int)s.size()) {
            b2.assign(1, c);
            return cost(b1) + cost(b2) - cost(A);
        }
        const auto& B = s[r2];
        b2.assign(B.begin(), B.end());
        b2.insert(b2.begin() + p2, c);
        return cost(b1) + cost(b2) - cost(A) - cost(B);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-1, m[4], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 12);
    int nr = (int)params.get("new_route", 1);
    return std::make_unique<GranularRelocate>(model, k, nr != 0);
}
