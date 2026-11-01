// COMPONENT: {"name": "granular_route_endpoint_merge_and_split", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class RouteMergeSplit : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    RouteMergeSplit(const CVRP& m, int k) : M(m) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        nbf.assign((size_t)(n + 1) * std::max(K, 1), 0);
        std::vector<int> idx;
        for (int c = 1; c <= n; ++c) {
            idx.clear();
            for (int o = 1; o <= n; ++o) if (o != c) idx.push_back(o);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) nbf[(size_t)c * K + t] = idx[t];
        }
        endR.assign(n + 1, -1);
        endI.assign(n + 1, 0);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        size_t base = out.size();
        const double C = M.capacity;
        for (int r1 = 0; r1 < cR; ++r1) {
            int len = clen[r1];
            if (len == 0 || !okr[r1]) continue;
            const auto& A = s[r1];
            int ne = len == 1 ? 1 : 2;
            for (int e1 = 0; e1 < ne; ++e1) {
                int x = e1 == 0 ? A.front() : A.back();
                const int* nb = nbf.data() + (size_t)x * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = endR[v];
                    if (r2 < 0 || r2 == r1) continue;
                    int e2 = endI[v];
                    if (r1 < r2) out.push_back({0, r1, e1, r2, e2, 0, 0});
                    else out.push_back({0, r2, e2, r1, e1, 0, 0});
                }
            }
        }
        std::sort(out.begin() + base, out.end());
        out.erase(std::unique(out.begin() + base, out.end()), out.end());
        if (out.size() == base) {
            for (int r1 = 0; r1 < cR; ++r1) {
                if (!clen[r1] || !okr[r1]) continue;
                for (int r2 = r1 + 1; r2 < cR; ++r2) {
                    if (!clen[r2] || !okr[r2]) continue;
                    out.push_back({0, r1, clen[r1] == 1 ? 0 : 1, r2, 0, 0, 0});
                }
            }
        }
        for (int r = 0; r < cR; ++r)
            if (okr[r] && clen[r] >= 2 && cl[r] > C + 1e-9)
                for (int p = 1; p < clen[r]; ++p) out.push_back({1, r, p, 0, 0, 0, 0});
        if (out.size() == base)
            for (int r = 0; r < cR; ++r)
                if (okr[r] && clen[r] >= 2)
                    for (int p = 1; p < clen[r]; ++p) out.push_back({1, r, p, 0, 0, 0, 0});
    }

    Sol apply(const Sol& s, const Move& m) override {
        if (m[0] == 0) {
            int r1 = m[1], e1 = m[2], r2 = m[3], e2 = m[4];
            const auto& A = s[r1];
            const auto& B = s[r2];
            std::vector<int> mg;
            mg.reserve(A.size() + B.size());
            if (e1 == 1) mg.insert(mg.end(), A.begin(), A.end());
            else mg.insert(mg.end(), A.rbegin(), A.rend());
            if (e2 == 0) mg.insert(mg.end(), B.begin(), B.end());
            else mg.insert(mg.end(), B.rbegin(), B.rend());
            Sol t;
            t.reserve(s.size());
            for (int r = 0; r < (int)s.size(); ++r) {
                if (r == r2) continue;
                if (r == r1) t.push_back(std::move(mg));
                else t.push_back(s[r]);
            }
            return t;
        }
        int r = m[1], p = m[2];
        Sol t = s;
        const auto& A = s[r];
        t[r].assign(A.begin(), A.begin() + p);
        t.emplace_back(A.begin() + p, A.end());
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        const double C = M.capacity, pen = M.penalty;
        if (m[0] == 0) {
            int r1 = m[1], e1 = m[2], r2 = m[3], e2 = m[4];
            const auto& A = s[r1];
            const auto& B = s[r2];
            if (A.empty() || B.empty() || !okOf(s, r1) || !okOf(s, r2)) return full(s, m);
            int x = e1 == 0 ? A.front() : A.back();
            int y = e2 == 0 ? B.front() : B.back();
            double LA = loadOf(s, r1), LB = loadOf(s, r2);
            double dd = d(x, y) - d(x, 0) - d(0, y);
            dd += pen * (std::max(0.0, LA + LB - C) - std::max(0.0, LA - C) - std::max(0.0, LB - C));
            return dd;
        }
        int r = m[1], p = m[2];
        const auto& A = s[r];
        if (!okOf(s, r)) return full(s, m);
        int a = A[p - 1], b = A[p];
        double P = 0.0;
        for (int k = 0; k < p; ++k) P += M.demand[A[k]];
        double L = loadOf(s, r);
        double dd = d(a, 0) + d(0, b) - d(a, b);
        dd += pen * (std::max(0.0, P - C) + std::max(0.0, L - P - C) - std::max(0.0, L - C));
        return dd;
    }

private:
    const CVRP& M;
    int K;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf, endR, endI, clen;
    std::vector<double> cl;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    int cR = 0;
    const Sol* cptr = nullptr;

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }

    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    void build(const Sol& s) {
        std::fill(endR.begin(), endR.end(), -1);
        cR = (int)s.size();
        cptr = &s;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR);
        for (int r = 0; r < cR; ++r) {
            const auto& A = s[r];
            int len = (int)A.size();
            clen[r] = len;
            rptr[r] = A.data();
            double l = 0.0;
            char ok = 1;
            for (int c : A) {
                if (valid(c)) l += M.demand[c];
                else ok = 0;
            }
            cl[r] = l;
            okr[r] = ok;
            if (ok && len > 0) {
                endR[A.front()] = r; endI[A.front()] = 0;
                if (len > 1) { endR[A.back()] = r; endI[A.back()] = 1; }
            }
        }
    }
    bool cached(const Sol& s, int r) const {
        if (&s != cptr || (int)s.size() != cR || r >= cR) return false;
        const auto& A = s[r];
        return A.data() == rptr[r] && (int)A.size() == clen[r];
    }
    double loadOf(const Sol& s, int r) const {
        if (cached(s, r)) return cl[r];
        return M.route_load(s[r]);
    }
    bool okOf(const Sol& s, int r) const {
        if (cached(s, r)) return okr[r];
        for (int c : s[r]) if (!valid(c)) return false;
        return true;
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<RouteMergeSplit>(model, k);
}
