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
        buf.assign((size_t)4 * std::max(K, 1) + 8, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        size_t base = out.size();
        ent.clear();
        int* bf = buf.data();
        const bool doE = cR < 32768 && maxLen < 32768;
        for (int r = 0; r < cR; ++r) {
            int L = clen[r];
            if (!okr[r] || L < 3) continue;
            const int* A = s[r].data();
            for (int i = 0; i < L; ++i) {
                for (int sl = 2; sl <= Lmax && i + sl < L + 1 && sl < L; ++sl) {
                    int f = A[i], l = A[i + sl - 1];
                    int nb = 0;
                    for (int side = 0; side < 2; ++side) {
                        int e = side ? l : f;
                        const int* nbp = nbf.data() + (size_t)e * K;
                        for (int t = 0; t < K; ++t) {
                            int v = nbp[t];
                            if (locR[v] != r) continue;
                            int pv = locP[v];
                            if (pv >= i && pv < i + sl) continue;
                            int pvp = pv < i ? pv : pv - sl;
                            int j = pvp + 1, rev = side ? 1 : 0;
                            if (!(j == i && rev == 0)) bf[nb++] = j * 2 + rev;
                            j = pvp; rev = side ? 0 : 1;
                            if (!(j == i && rev == 0)) bf[nb++] = j * 2 + rev;
                        }
                    }
                    if (nb == 0) continue;
                    for (int x = 1; x < nb; ++x) {
                        int v = bf[x], y = x - 1;
                        while (y >= 0 && bf[y] > v) { bf[y + 1] = bf[y]; --y; }
                        bf[y + 1] = v;
                    }
                    int a = i > 0 ? A[i - 1] : 0, b = i + sl < L ? A[i + sl] : 0;
                    double part = d(a, b) - d(a, f) - d(l, b);
                    int mlen = L - sl;
                    int prevc = -1;
                    for (int x = 0; x < nb; ++x) {
                        int code = bf[x];
                        if (code == prevc) continue;
                        prevc = code;
                        int j = code >> 1, rev = code & 1;
                        out.push_back({0, r, i, sl, j, rev, 0});
                        if (doE) {
                            int p = j > 0 ? ((j - 1) < i ? A[j - 1] : A[j - 1 + sl]) : 0;
                            int q = j < mlen ? (j < i ? A[j] : A[j + sl]) : 0;
                            int ff = rev ? l : f, ll = rev ? f : l;
                            double dd = part;
                            dd += d(p, ff) + d(ll, q) - d(p, q);
                            ent.push_back({key(r, i, sl, j, rev), dd});
                        }
                    }
                }
            }
        }
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
            mbase = nullptr;
            mcount = 0;
        } else {
            mbase = out.data() + base;
            mcount = doE ? ent.size() : 0;
        }
    }

    bool has_estimate() const { return true; }
    bool has_estimate() { return true; }

    double estimate(const Sol& s, const Move& m) const {
        if (m[0] == 0 && &s == cptr && mcount) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move)) {
                if ((unsigned)(m[1] | m[2] | m[4]) < 32768u && (unsigned)m[3] < 16u && (unsigned)m[5] < 2u) {
                    const Ent& e = ent[dpos / sizeof(Move)];
                    if (e.k == key(m[1], m[2], m[3], m[4], m[5])) return e.e;
                }
            }
        }
        return const_cast<IntraOrOptRev*>(this)->delta(s, m);
    }
    double estimate(const Sol& s, const Move& m) {
        return static_cast<const IntraOrOptRev*>(this)->estimate(s, m);
    }

    Sol apply(const Sol& s, const Move& m) override {
        if (m[0] == 0) {
            int r = m[1], i = m[2], sl = m[3], j = m[4], rev = m[5];
            const auto& A = s[r];
            int L = (int)A.size();
            std::vector<int> nr;
            nr.reserve(L);
            const int* Ap = A.data();
            for (int k = 0; k < j; ++k) nr.push_back(k < i ? Ap[k] : Ap[k + sl]);
            if (rev) for (int k = i + sl - 1; k >= i; --k) nr.push_back(Ap[k]);
            else for (int k = i; k < i + sl; ++k) nr.push_back(Ap[k]);
            int mlen = L - sl;
            for (int k = j; k < mlen; ++k) nr.push_back(k < i ? Ap[k] : Ap[k + sl]);
            Sol t;
            t.reserve(s.size());
            for (int k = 0; k < (int)s.size(); ++k) {
                if (k == r) t.push_back(std::move(nr));
                else t.push_back(s[k]);
            }
            return t;
        }
        Sol t = s;
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        int c = t[r1][i];
        t[r1].erase(t[r1].begin() + i);
        t[r2].insert(t[r2].begin() + j, c);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        if (m[0] == 0 && &s == cptr && mcount) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move)) {
                int r = m[1];
                if ((unsigned)(r | m[2] | m[4]) < 32768u && (unsigned)m[3] < 16u && (unsigned)m[5] < 2u) {
                    const Ent& e = ent[dpos / sizeof(Move)];
                    if (e.k == key(r, m[2], m[3], m[4], m[5]) && cached(s, r) && okr[r]) {
                        const auto& A = s[r];
                        int L = clen[r];
                        if (L > 0 && A[0] == rf[r] && A[L - 1] == rl[r]) return e.e;
                    }
                }
            }
        }
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
    std::vector<int> nbf, locR, locP, clen, rf, rl, buf;
    std::vector<double> cl;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    int cR = 0, maxLen = 0;
    const Sol* cptr = nullptr;
    struct Ent { unsigned long long k; double e; };
    std::vector<Ent> ent;
    const Move* mbase = nullptr;
    size_t mcount = 0;

    static inline unsigned long long key(int r, int i, int sl, int j, int rev) {
        return (unsigned long long)(unsigned)r | ((unsigned long long)(unsigned)i << 15) |
               ((unsigned long long)(unsigned)sl << 30) | ((unsigned long long)(unsigned)j << 34) |
               ((unsigned long long)(unsigned)rev << 49);
    }

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    void build(const Sol& s) {
        std::fill(locR.begin(), locR.end(), -1);
        cR = (int)s.size();
        cptr = &s;
        maxLen = 0;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR); rf.resize(cR); rl.resize(cR);
        const int n = M.n;
        const double* dem = M.demand.data();
        for (int r = 0; r < cR; ++r) {
            const auto& A = s[r];
            int len = (int)A.size();
            clen[r] = len;
            if (len > maxLen) maxLen = len;
            rptr[r] = A.data();
            rf[r] = len > 0 ? A[0] : 0;
            rl[r] = len > 0 ? A[len - 1] : 0;
            double l = 0.0;
            char ok = 1;
            for (int c : A) {
                if (c >= 1 && c <= n) l += dem[c];
                else ok = 0;
            }
            cl[r] = l;
            okr[r] = ok;
            if (ok)
                for (int p = 0; p < len; ++p) { locR[A[p]] = r; locP[A[p]] = p; }
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
