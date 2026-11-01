// COMPONENT: {"name": "granular_intra_route_oropt_segment_with_reversal", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [2, 5]}}}
class IntraOrOptRev : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    IntraOrOptRev(const CVRP& m, int k, int L) : M(m), Lmax(std::max(2, L)) {
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
        locR.assign(n + 1, -1);
        locP.assign(n + 1, 0);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        size_t base = out.size();
        for (int r = 0; r < cR; ++r) {
            int L = clen[r];
            if (!okr[r] || L < 3) continue;
            const auto& A = s[r];
            for (int i = 0; i < L; ++i) {
                for (int sl = 2; sl <= Lmax && i + sl < L + 1 && sl < L; ++sl) {
                    int f = A[i], l = A[i + sl - 1];
                    for (int side = 0; side < 2; ++side) {
                        int e = side ? l : f;
                        const int* nb = nbf.data() + (size_t)e * K;
                        for (int t = 0; t < K; ++t) {
                            int v = nb[t];
                            if (locR[v] != r) continue;
                            int pv = locP[v];
                            if (pv >= i && pv < i + sl) continue;
                            int pvp = pv < i ? pv : pv - sl;
                            int j = pvp + 1, rev = side ? 1 : 0;
                            if (!(j == i && rev == 0)) out.push_back({0, r, i, sl, j, rev, 0});
                            j = pvp; rev = side ? 0 : 1;
                            if (!(j == i && rev == 0)) out.push_back({0, r, i, sl, j, rev, 0});
                        }
                    }
                }
            }
        }
        std::sort(out.begin() + base, out.end());
        out.erase(std::unique(out.begin() + base, out.end()), out.end());
        if (out.size() == base) {
            for (int r1 = 0; r1 < cR; ++r1) {
                if (!okr[r1]) continue;
                const auto& A = s[r1];
                for (int i = 0; i < clen[r1]; ++i) {
                    const int* nb = nbf.data() + (size_t)A[i] * K;
                    for (int t = 0; t < K; ++t) {
                        int v = nb[t], r2 = locR[v];
                        if (r2 < 0 || r2 == r1) continue;
                        out.push_back({1, r1, i, r2, locP[v], 0, 0});
                        out.push_back({1, r1, i, r2, locP[v] + 1, 0, 0});
                    }
                }
            }
            if (out.size() == base)
                for (int r1 = 0; r1 < cR; ++r1)
                    for (int i = 0; i < clen[r1]; ++i)
                        for (int r2 = 0; r2 < cR; ++r2)
                            if (r2 != r1 && okr[r1] && okr[r2] && clen[r2] > 0)
                                out.push_back({1, r1, i, r2, 0, 0, 0});
            std::sort(out.begin() + base, out.end());
            out.erase(std::unique(out.begin() + base, out.end()), out.end());
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        if (m[0] == 0) {
            int r = m[1], i = m[2], sl = m[3], j = m[4], rev = m[5];
            const auto& A = s[r];
            std::vector<int> seg(A.begin() + i, A.begin() + i + sl);
            if (rev) std::reverse(seg.begin(), seg.end());
            std::vector<int> rest;
            rest.reserve(A.size());
            rest.insert(rest.end(), A.begin(), A.begin() + i);
            rest.insert(rest.end(), A.begin() + i + sl, A.end());
            rest.insert(rest.begin() + j, seg.begin(), seg.end());
            t[r] = std::move(rest);
            return t;
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        int c = t[r1][i];
        t[r1].erase(t[r1].begin() + i);
        t[r2].insert(t[r2].begin() + j, c);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        if (m[0] == 0) {
            int r = m[1], i = m[2], sl = m[3], j = m[4], rev = m[5];
            if (!okOf(s, r)) return full(s, m);
            const auto& A = s[r];
            int L = (int)A.size();
            int a = i > 0 ? A[i - 1] : 0, b = i + sl < L ? A[i + sl] : 0;
            int f = A[i], l = A[i + sl - 1];
            double dd = d(a, b) - d(a, f) - d(l, b);
            int mlen = L - sl;
            auto at = [&](int k) { return k < i ? A[k] : A[k + sl]; };
            int p = j > 0 ? at(j - 1) : 0, q = j < mlen ? at(j) : 0;
            int ff = rev ? l : f, ll = rev ? f : l;
            dd += d(p, ff) + d(ll, q) - d(p, q);
            return dd;
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        if (!okOf(s, r1) || !okOf(s, r2)) return full(s, m);
        const auto& A = s[r1];
        const auto& B = s[r2];
        int u = A[i];
        int a = i > 0 ? A[i - 1] : 0, b = i + 1 < (int)A.size() ? A[i + 1] : 0;
        double dd = d(a, b) - d(a, u) - d(u, b);
        int p = j > 0 ? B[j - 1] : 0, q = j < (int)B.size() ? B[j] : 0;
        dd += d(p, u) + d(u, q) - d(p, q);
        double L1 = loadOf(s, r1), L2 = loadOf(s, r2), du = M.demand[u], C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - du - C) + std::max(0.0, L2 + du - C) -
                           std::max(0.0, L1 - C) - std::max(0.0, L2 - C));
        return dd;
    }

private:
    const CVRP& M;
    int K, Lmax;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf, locR, locP, clen;
    std::vector<double> cl;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    int cR = 0;
    const Sol* cptr = nullptr;

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    void build(const Sol& s) {
        std::fill(locR.begin(), locR.end(), -1);
        cR = (int)s.size();
        cptr = &s;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR);
        for (int r = 0; r < cR; ++r) {
            const auto& A = s[r];
            clen[r] = (int)A.size();
            rptr[r] = A.data();
            double l = 0.0;
            char ok = 1;
            for (int c : A) {
                if (valid(c)) l += M.demand[c];
                else ok = 0;
            }
            cl[r] = l;
            okr[r] = ok;
            if (ok)
                for (int p = 0; p < clen[r]; ++p) { locR[A[p]] = r; locP[A[p]] = p; }
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
    int L = (int)params.get("max_seg", 3);
    return std::make_unique<IntraOrOptRev>(model, k, L);
}
