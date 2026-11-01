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
        seenS.assign(n + 1, 0u);
        mk.assign(n + 1, 0u);
        pk.assign(n + 1, 0);
        Dp = M.D.data();
        S = (size_t)(n + 1);
        buf.assign((size_t)4 * std::max(K, 1) + 8, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        size_t base = out.size();
        if (!buildFast(s)) { movesFull(s, out); return; }
        if (cache.size() < (size_t)cR) cache.resize(cR);
        const bool doE = cR < 32768 && maxLen < 32768;
        size_t tot = 0;
        for (int r = 0; r < cR; ++r) {
            RC& c = cache[r];
            const auto& A = s[r];
            if (!c.valid || c.route.size() != A.size() ||
                (!A.empty() && std::memcmp(c.route.data(), A.data(), A.size() * sizeof(int)) != 0))
                regen(r, A, c);
            tot += c.mv.size();
        }
        if (tot == 0) { movesFull(s, out); return; }
        out.reserve(base + tot);
        ent.clear();
        for (int r = 0; r < cR; ++r) {
            const RC& c = cache[r];
            if (c.mv.empty()) continue;
            out.insert(out.end(), c.mv.begin(), c.mv.end());
            if (doE) ent.insert(ent.end(), c.en.begin(), c.en.end());
        }
        mbase = out.data() + base;
        mcount = doE ? ent.size() : 0;
    }

    void movesFull(const Sol& s, std::vector<Move>& out) {
        build(s);
        size_t base = out.size();
        ent.clear();
        int* bf = buf.data();
        const bool doE = cR < 32768 && maxLen < 32768;
        poff.resize(cR + 1);
        size_t run = 0;
        for (int r = 0; r < cR; ++r) { poff[r] = run; run += (size_t)clen[r]; }
        poff[cR] = run;
        const size_t KK = (size_t)K;
        if (fl.size() < run * KK) fl.resize(run * KK);
        if (fc.size() < run) fc.resize(run);
        {
            const int* LR = locR.data();
            const int* LP = locP.data();
            const int* NB = nbf.data();
            for (int r = 0; r < cR; ++r) {
                int L = clen[r];
                if (!okr[r] || L < 3) continue;
                const int* A = s[r].data();
                size_t pb = poff[r];
                for (int p = 0; p < L; ++p) {
                    const int* nb = NB + (size_t)A[p] * KK;
                    int* dst = fl.data() + (pb + p) * KK;
                    int cnt = 0;
                    for (int t = 0; t < K; ++t) {
                        int v = nb[t];
                        if (LR[v] == r) dst[cnt++] = LP[v];
                    }
                    fc[pb + p] = cnt;
                }
            }
        }
        for (int r = 0; r < cR; ++r) {
            int L = clen[r];
            if (!okr[r] || L < 3) continue;
            const int* A = s[r].data();
            const size_t pb = poff[r];
            for (int i = 0; i < L; ++i) {
                const int* fF = fl.data() + (pb + i) * KK;
                const int nF = fc[pb + i];
                for (int sl = 2; sl <= Lmax && i + sl < L + 1 && sl < L; ++sl) {
                    int f = A[i], l = A[i + sl - 1];
                    const int li = i + sl - 1;
                    const int* fL = fl.data() + (pb + li) * KK;
                    const int nL = fc[pb + li];
                    int nb = 0;
                    for (int x = 0; x < nF; ++x) {
                        int pv = fF[x];
                        if (pv >= i && pv < i + sl) continue;
                        int pvp = pv < i ? pv : pv - sl;
                        if (pvp + 1 != i) bf[nb++] = (pvp + 1) * 2;
                        bf[nb++] = pvp * 2 + 1;
                    }
                    for (int x = 0; x < nL; ++x) {
                        int pv = fL[x];
                        if (pv >= i && pv < i + sl) continue;
                        int pvp = pv < i ? pv : pv - sl;
                        bf[nb++] = (pvp + 1) * 2 + 1;
                        if (pvp != i) bf[nb++] = pvp * 2;
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
    std::vector<int> fl, fc;
    std::vector<size_t> poff;
    std::vector<double> cl;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    int cR = 0, maxLen = 0;
    const Sol* cptr = nullptr;
    struct Ent { unsigned long long k; double e; };
    std::vector<Ent> ent;
    const Move* mbase = nullptr;
    size_t mcount = 0;

    struct RC { bool valid = false; std::vector<int> route; std::vector<Move> mv; std::vector<Ent> en; };
    std::vector<RC> cache;
    std::vector<unsigned> seenS, mk;
    std::vector<int> pk, flr, fcr;
    unsigned sst = 0, gst = 0;

    bool buildFast(const Sol& s) {
        cR = (int)s.size();
        cptr = &s;
        maxLen = 0;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR); rf.resize(cR); rl.resize(cR);
        if (++sst == 0) { std::fill(seenS.begin(), seenS.end(), 0u); sst = 1; }
        unsigned* SS = seenS.data();
        const int n = M.n;
        const double* dem = M.demand.data();
        bool dup = false;
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
                if (c >= 1 && c <= n) {
                    l += dem[c];
                    if (SS[c] == sst) dup = true;
                    SS[c] = sst;
                } else ok = 0;
            }
            cl[r] = l;
            okr[r] = ok;
        }
        return !dup;
    }

    void regen(int r, const std::vector<int>& Av, RC& c) {
        c.route.assign(Av.begin(), Av.end());
        c.valid = true;
        c.mv.clear();
        c.en.clear();
        const int L = clen[r];
        if (!okr[r] || L < 3) return;
        const int* A = Av.data();
        if (++gst == 0) { std::fill(mk.begin(), mk.end(), 0u); gst = 1; }
        unsigned* MK = mk.data();
        int* PK = pk.data();
        for (int p = 0; p < L; ++p) { MK[A[p]] = gst; PK[A[p]] = p; }
        const size_t KK = (size_t)K;
        if (flr.size() < (size_t)L * KK + 1) flr.resize((size_t)L * KK + 1);
        if (fcr.size() < (size_t)L) fcr.resize(L);
        const int* NB = nbf.data();
        for (int p = 0; p < L; ++p) {
            const int* nb = NB + (size_t)A[p] * KK;
            int* dst = flr.data() + (size_t)p * KK;
            int cnt = 0;
            for (int t = 0; t < K; ++t) {
                int v = nb[t];
                if (MK[v] == gst) dst[cnt++] = PK[v];
            }
            fcr[p] = cnt;
        }
        int* bf = buf.data();
        for (int i = 0; i < L; ++i) {
            const int* fF = flr.data() + (size_t)i * KK;
            const int nF = fcr[i];
            for (int sl = 2; sl <= Lmax && i + sl < L + 1 && sl < L; ++sl) {
                int f = A[i], l = A[i + sl - 1];
                const int li = i + sl - 1;
                const int* fL = flr.data() + (size_t)li * KK;
                const int nL = fcr[li];
                int nb = 0;
                for (int x = 0; x < nF; ++x) {
                    int pv = fF[x];
                    if (pv >= i && pv < i + sl) continue;
                    int pvp = pv < i ? pv : pv - sl;
                    if (pvp + 1 != i) bf[nb++] = (pvp + 1) * 2;
                    bf[nb++] = pvp * 2 + 1;
                }
                for (int x = 0; x < nL; ++x) {
                    int pv = fL[x];
                    if (pv >= i && pv < i + sl) continue;
                    int pvp = pv < i ? pv : pv - sl;
                    bf[nb++] = (pvp + 1) * 2 + 1;
                    if (pvp != i) bf[nb++] = pvp * 2;
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
                    c.mv.push_back({0, r, i, sl, j, rev, 0});
                    int p = j > 0 ? ((j - 1) < i ? A[j - 1] : A[j - 1 + sl]) : 0;
                    int q = j < mlen ? (j < i ? A[j] : A[j + sl]) : 0;
                    int ff = rev ? l : f, ll = rev ? f : l;
                    double dd = part;
                    dd += d(p, ff) + d(ll, q) - d(p, q);
                    c.en.push_back({key(r, i, sl, j, rev), dd});
                }
            }
        }
    }

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
