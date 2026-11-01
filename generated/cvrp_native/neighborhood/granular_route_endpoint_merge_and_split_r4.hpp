// COMPONENT: {"name": "granular_route_endpoint_merge_and_split", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class RouteMergeSplit : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    RouteMergeSplit(const CVRP& m, int k) : M(m) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        Dp = M.D.data();
        S = (size_t)(n + 1);
        size_t KK = (size_t)std::max(K, 1);
        nbf.assign((size_t)(n + 1) * KK, 0);
        nbd.assign((size_t)(n + 1) * KK, 0.0);
        nbr.assign((size_t)(n + 1) * KK, 0.0);
        std::vector<int> idx;
        for (int c = 1; c <= n; ++c) {
            idx.clear();
            for (int o = 1; o <= n; ++o) if (o != c) idx.push_back(o);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) {
                int v = idx[t];
                nbf[(size_t)c * K + t] = v;
                nbd[(size_t)c * K + t] = d(c, v);
                nbr[(size_t)c * K + t] = d(v, c);
            }
        }
        endC.assign(n + 1, -1);
        dTo0.assign(n + 1, 0.0);
        dFrom0.assign(n + 1, 0.0);
        for (int c = 0; c <= n; ++c) { dTo0[c] = d(c, 0); dFrom0[c] = d(0, c); }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        size_t base = out.size();
        if (hasC && cacheHit(s)) {
            out.insert(out.end(), cm.begin(), cm.begin() + cmN);
            mbase = out.data() + base;
            return;
        }
        build(s);
        const double C = M.capacity, pen = M.penalty;
        const int E = 2 * cR;
        const int* EC = endC.data();
        const int Kc = K;
        size_t maxp = (size_t)E * (size_t)Kc;
        if (pa.size() < maxp) { pa.resize(maxp); pb.resize(maxp); pdv.resize(maxp); }
        int* PA = pa.data();
        int* PB = pb.data();
        double* PD = pdv.data();
        size_t np = 0;
        for (int r1 = 0; r1 < cR; ++r1) {
            int len = clen[r1];
            if (len == 0 || !okr[r1]) continue;
            const int* A = rptr[r1];
            int ne = len == 1 ? 1 : 2;
            for (int e1 = 0; e1 < ne; ++e1) {
                int x = e1 == 0 ? A[0] : A[len - 1];
                const int* nb = nbf.data() + (size_t)x * Kc;
                const double* ndp = nbd.data() + (size_t)x * Kc;
                const double* nrp = nbr.data() + (size_t)x * Kc;
                const int a = 2 * r1 + e1;
                for (int t = 0; t < Kc; ++t) {
                    int code = EC[nb[t]];
                    if (code < 0 || (code >> 1) == r1) continue;
                    if (code > a) { PA[np] = a; PB[np] = code; PD[np] = ndp[t]; }
                    else { PA[np] = code; PB[np] = a; PD[np] = nrp[t]; }
                    ++np;
                }
            }
        }
        size_t pairsAll = cR > 1 ? (size_t)cR * (size_t)(cR - 1) / 2 : 0;
        size_t bound = std::max(np, pairsAll) + totalC + 2;
        if (cm.size() < bound) { cm.resize(bound); ekey.resize(bound); eest.resize(bound); }
        Move* MV = cm.data();
        unsigned long long* KP = ekey.data();
        double* ES = eest.data();
        size_t w = 0;
        const bool doE = cR < 32768 && maxLen < 32768;
        const int* EP = epc.data();
        const double* CL = cl.data();
        const double* OV = ov.data();
        const double* T0 = dTo0.data();
        const double* F0 = dFrom0.data();
        if (np) {
            cnt.assign(E + 1, 0);
            int* cp = cnt.data();
            for (size_t i = 0; i < np; ++i) ++cp[PA[i] + 1];
            for (int i = 0; i < E; ++i) cp[i + 1] += cp[i];
            if (sb.size() < np) { sb.resize(np); sd.resize(np); }
            int* sp = sb.data();
            double* sdp = sd.data();
            for (size_t i = 0; i < np; ++i) {
                int pos = cp[PA[i]]++;
                sp[pos] = PB[i];
                sdp[pos] = PD[i];
            }
            int beg = 0;
            for (int a = 0; a < E; ++a) {
                int end = cp[a];
                if (end > beg) {
                    for (int i = beg + 1; i < end; ++i) {
                        int v = sp[i];
                        double vd = sdp[i];
                        int j = i - 1;
                        while (j >= beg && sp[j] > v) { sp[j + 1] = sp[j]; sdp[j + 1] = sdp[j]; --j; }
                        sp[j + 1] = v;
                        sdp[j + 1] = vd;
                    }
                    int ra = a >> 1, ea = a & 1, last = -1;
                    const int x = EP[a];
                    const double LA = CL[ra], oa = OV[ra], tx = T0[x];
                    for (int i = beg; i < end; ++i) {
                        int b = sp[i];
                        if (b != last) {
                            int rb = b >> 1, eb = b & 1;
                            MV[w] = Move{0, ra, ea, rb, eb, 0, 0};
                            KP[w] = key(0, ra, ea, rb, eb);
                            double dd = sdp[i] - tx - F0[EP[b]];
                            dd += pen * (std::max(0.0, LA + CL[rb] - C) - oa - OV[rb]);
                            ES[w] = dd;
                            ++w;
                        }
                        last = b;
                    }
                }
                beg = end;
            }
        }
        if (w == 0) {
            for (int r1 = 0; r1 < cR; ++r1) {
                if (!clen[r1] || !okr[r1]) continue;
                int e1 = clen[r1] == 1 ? 0 : 1;
                const int x = EP[2 * r1 + e1];
                const double* Dx = Dp + (size_t)x * S;
                const double tx = T0[x], LA = CL[r1], oa = OV[r1];
                for (int r2 = r1 + 1; r2 < cR; ++r2) {
                    if (!clen[r2] || !okr[r2]) continue;
                    MV[w] = Move{0, r1, e1, r2, 0, 0, 0};
                    KP[w] = key(0, r1, e1, r2, 0);
                    int y = EP[2 * r2];
                    double dd = Dx[y] - tx - F0[y];
                    dd += pen * (std::max(0.0, LA + CL[r2] - C) - oa - OV[r2]);
                    ES[w] = dd;
                    ++w;
                }
            }
        }
        const double* dem = M.demand.data();
        auto emitSplits = [&](int r) {
            const int* A = rptr[r];
            int len = clen[r];
            double L = CL[r];
            double oL = OV[r];
            double P = 0.0;
            for (int p = 1; p < len; ++p) {
                int a = A[p - 1], b = A[p];
                P += dem[a];
                MV[w] = Move{1, r, p, 0, 0, 0, 0};
                KP[w] = key(1, r, p, 0, 0);
                double dd = T0[a] + F0[b] - Dp[(size_t)a * S + b];
                dd += pen * (std::max(0.0, P - C) + std::max(0.0, L - P - C) - oL);
                ES[w] = dd;
                ++w;
            }
        };
        for (int r = 0; r < cR; ++r)
            if (okr[r] && clen[r] >= 2 && cl[r] > C + 1e-9) emitSplits(r);
        if (w == 0)
            for (int r = 0; r < cR; ++r)
                if (okr[r] && clen[r] >= 2) emitSplits(r);
        out.insert(out.end(), MV, MV + w);
        mbase = out.data() + base;
        mcount = doE ? w : 0;
        cmN = w;
        hasC = true;
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
        Sol t;
        t.reserve(s.size() + 1);
        for (int q = 0; q < (int)s.size(); ++q) {
            if (q == r) t.emplace_back(s[r].begin(), s[r].begin() + p);
            else t.push_back(s[q]);
        }
        const auto& A = s[r];
        t.emplace_back(A.begin() + p, A.end());
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        if (&s == cptr && (int)s.size() == cR) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move) && (unsigned)m[0] < 2u &&
                ((unsigned)(m[1] | m[2] | m[3] | m[4]) < 32768u)) {
                size_t idx = dpos / sizeof(Move);
                if (ekey[idx] == key(m[0], m[1], m[2], m[3], m[4])) {
                    if (m[0] == 0) {
                        if (sameR(s, m[1]) && sameR(s, m[3])) return eest[idx];
                    } else {
                        if (sameR(s, m[1])) return eest[idx];
                    }
                }
            }
        }
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

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        if (&s == cptr && (int)s.size() == cR) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move) && (unsigned)m[0] < 2u &&
                ((unsigned)(m[1] | m[2] | m[3] | m[4]) < 32768u)) {
                size_t idx = dpos / sizeof(Move);
                if (ekey[idx] == key(m[0], m[1], m[2], m[3], m[4])) return eest[idx];
            }
        }
        return delta(s, m);
    }

private:
    const CVRP& M;
    int K;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf, endC, touched, pa, pb, cnt, sb, clen, epc, flat;
    std::vector<double> nbd, nbr, dTo0, dFrom0, pdv, sd;
    std::vector<double> cl, ov;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    std::vector<Move> cm;
    size_t cmN = 0;
    bool hasC = false;
    size_t totalC = 0;
    int cR = 0;
    int maxLen = 0;
    const Sol* cptr = nullptr;
    std::vector<unsigned long long> ekey;
    std::vector<double> eest;
    const Move* mbase = nullptr;
    size_t mcount = 0;

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }

    static inline unsigned long long key(int t, int a, int b, int c, int e) {
        return (unsigned long long)(unsigned)a | ((unsigned long long)(unsigned)b << 15) |
               ((unsigned long long)(unsigned)c << 30) | ((unsigned long long)(unsigned)e << 45) |
               ((unsigned long long)(unsigned)t << 60);
    }

    bool cacheHit(const Sol& s) const {
        if (&s != cptr || (int)s.size() != cR) return false;
        for (int r = 0; r < cR; ++r) {
            const auto& R = s[r];
            if (R.data() != rptr[r] || (int)R.size() != clen[r]) return false;
        }
        const int* f = flat.data();
        for (int r = 0; r < cR; ++r) {
            int len = clen[r];
            if (len && !std::equal(f, f + len, s[r].data())) return false;
            f += len;
        }
        return true;
    }

    inline bool sameR(const Sol& s, int r) const {
        const auto& R = s[r];
        int len = (int)R.size();
        if (len == 0 || len != clen[r] || R.data() != rptr[r]) return false;
        return R[0] == epc[2 * r] && R[len - 1] == epc[2 * r + 1];
    }

    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    void build(const Sol& s) {
        int* ec = endC.data();
        for (int c : touched) ec[c] = -1;
        touched.clear();
        cR = (int)s.size();
        cptr = &s;
        clen.resize(cR); cl.resize(cR); ov.resize(cR); okr.resize(cR); rptr.resize(cR);
        epc.resize(2 * (size_t)cR + 2);
        size_t tot = 0;
        for (int r = 0; r < cR; ++r) tot += s[r].size();
        totalC = tot;
        flat.resize(tot);
        int* fl = flat.data();
        const double* dem = M.demand.data();
        const unsigned n = (unsigned)M.n;
        const double C = M.capacity;
        int mx = 0;
        for (int r = 0; r < cR; ++r) {
            const auto& A = s[r];
            int len = (int)A.size();
            if (len > mx) mx = len;
            const int* ap = A.data();
            clen[r] = len;
            rptr[r] = ap;
            double l = 0.0;
            char ok = 1;
            for (int k = 0; k < len; ++k) {
                int c = ap[k];
                fl[k] = c;
                if ((unsigned)(c - 1) < n) l += dem[c];
                else ok = 0;
            }
            fl += len;
            cl[r] = l;
            ov[r] = std::max(0.0, l - C);
            okr[r] = ok;
            if (len > 0) {
                epc[2 * r] = ap[0];
                epc[2 * r + 1] = ap[len - 1];
            } else {
                epc[2 * r] = epc[2 * r + 1] = -1;
            }
            if (ok && len > 0) {
                ec[ap[0]] = 2 * r; touched.push_back(ap[0]);
                if (len > 1) { ec[ap[len - 1]] = 2 * r + 1; touched.push_back(ap[len - 1]); }
            }
        }
        maxLen = mx;
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
