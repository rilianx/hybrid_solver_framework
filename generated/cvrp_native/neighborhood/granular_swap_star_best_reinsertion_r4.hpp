// COMPONENT: {"name": "granular_swap_star_best_reinsertion", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 25]}}}
class SwapStar : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    SwapStar(const CVRP& m, int k) : M(m) {
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
        {
            std::vector<std::vector<int>> rv(n + 1);
            for (int c = 1; c <= n; ++c)
                for (int t = 0; t < K; ++t) rv[nbf[(size_t)c * K + t]].push_back(c);
            adjS.assign(n + 2, 0);
            std::vector<int> mk(n + 1, 0);
            maxDeg = 0;
            for (int c = 1; c <= n; ++c) {
                adjS[c] = (int)adjV.size();
                for (int t = 0; t < K; ++t) {
                    int v = nbf[(size_t)c * K + t];
                    if (mk[v] != c) { mk[v] = c; adjV.push_back(v); }
                }
                for (int v : rv[c]) if (mk[v] != c) { mk[v] = c; adjV.push_back(v); }
                maxDeg = std::max(maxDeg, (int)adjV.size() - adjS[c]);
            }
            adjS[n + 1] = (int)adjV.size();
            tmpv.assign((size_t)maxDeg + K + 1, 0);
        }
        locR.assign(n + 1, -1);
        locP.assign(n + 1, 0);
        fo.assign(n + 1, 0);
        fos.assign(n + 1, 0u);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        mcount = 0;
        size_t base = out.size();
        if (cR >= 32768 || maxLen >= 32768) { slowMoves(s, out, base); return; }
        if (dupF) { movesOld(s, out, base); return; }
        size_t ecap = adjV.size() + (size_t)cR * K + 1;
        if (ek.size() < ecap) { ek.resize(ecap); ek2.resize(ecap); eest.resize(ecap); }
        out.reserve(base + ecap);
        unsigned long long* EK = ek.data();
        unsigned* EK2 = ek2.data();
        double* EE = eest.data();
        size_t w = 0;
        const double Cc = M.capacity, pen = M.penalty;
        const double* dem = M.demand.data();
        const int* ND = nodes.data();
        const int* AS = adjS.data();
        const int* AV = adjV.data();
        const int* LR = locR.data();
        const int* LP = locP.data();
        int* T = tmpv.data();
        for (int r1 = 0; r1 < cR; ++r1) {
            if (!okr[r1]) continue;
            const int l1 = clen[r1];
            const int o1 = off[r1] + 1;
            for (int i = 0; i < l1; ++i) {
                int g1 = o1 + i, u = ND[g1];
                int m = 0;
                for (int a = AS[u], ae = AS[u + 1]; a < ae; ++a) {
                    int v = AV[a], r2 = LR[v];
                    if (r2 <= r1) continue;
                    if (l1 == 1 && clen[r2] == 1) continue;
                    int x = off[r2] + 1 + LP[v], b = m - 1;
                    while (b >= 0 && T[b] > x) { T[b + 1] = T[b]; --b; }
                    T[b + 1] = x;
                    ++m;
                }
                for (int a = 0; a < m; ++a) {
                    int g2 = T[a];
                    int r2 = gr[g2], j = g2 - off[r2] - 1, v = ND[g2];
                    int pu = fastIns(s, r2, j, u);
                    int pv = fastIns(s, r1, i, v);
                    out.push_back({0, r1, i, r2, j, pu, pv});
                    double dd = partN(ND + off[r1], i, v, pv) + partN(ND + off[r2], j, u, pu);
                    double L1 = cl[r1], L2 = cl[r2], du = dem[u], dv = dem[v];
                    dd += pen * (std::max(0.0, L1 - du + dv - Cc) + std::max(0.0, L2 - dv + du - Cc) -
                                 std::max(0.0, L1 - Cc) - std::max(0.0, L2 - Cc));
                    EK[w] = keyA(0, r1, i, r2, j);
                    EK2[w] = keyB(pu, pv);
                    EE[w] = dd;
                    ++w;
                }
            }
        }
        for (int r1 = 0; r1 < cR; ++r1) {
            if (!okr[r1] || clen[r1] != 1) continue;
            int u = ND[off[r1] + 1];
            const int* nb = nbf.data() + (size_t)u * K;
            int m = 0;
            for (int t = 0; t < K; ++t) {
                int v = nb[t], r2 = LR[v];
                if (r2 < 0 || r2 == r1) continue;
                int b = m - 1;
                while (b >= 0 && T[b] > r2) { T[b + 1] = T[b]; --b; }
                T[b + 1] = r2;
                ++m;
            }
            int last = -1;
            for (int a = 0; a < m; ++a) {
                if (T[a] == last) continue;
                last = T[a];
                int ps = fastIns(s, last, -1, u);
                out.push_back({1, r1, last, ps, 0, 0, 0});
                const int* n2 = ND + off[last];
                int p = n2[ps], q = n2[ps + 1];
                double dd = d(p, u) + d(u, q) - d(p, q) - d(0, u) - d(u, 0);
                double L2 = cl[last], du = dem[u];
                dd += pen * (std::max(0.0, L2 + du - Cc) - std::max(0.0, L2 - Cc) - std::max(0.0, du - Cc));
                EK[w] = keyA(1, r1, last, ps, 0);
                EK2[w] = 0u;
                EE[w] = dd;
                ++w;
            }
        }
        if (w == 0) { slowMoves(s, out, base); return; }
        mbase = out.data() + base;
        mcount = w;
    }

    void movesOld(const Sol& s, std::vector<Move>& out, size_t base) {
        plo.clear(); phi.clear(); t1r.clear(); t1s.clear();
        for (int r1 = 0; r1 < cR; ++r1) {
            if (!okr[r1]) continue;
            const int l1 = clen[r1];
            const int o1 = off[r1] + 1;
            const int* nd = nodes.data() + o1;
            for (int i = 0; i < l1; ++i) {
                int u = nd[i];
                int g1 = o1 + i;
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t], r2 = locR[v];
                    if (r2 < 0 || r2 == r1) continue;
                    if (l1 == 1 && clen[r2] == 1) continue;
                    int g2 = off[r2] + 1 + locP[v];
                    if (r1 < r2) { plo.push_back(g1); phi.push_back(g2); }
                    else { plo.push_back(g2); phi.push_back(g1); }
                }
                if (l1 == 1) {
                    t1s.push_back((int)t1r.size());
                    t1r.push_back(r1);
                    size_t st = t1r.size();
                    for (int t = 0; t < K; ++t) {
                        int v = nb[t], r2 = locR[v];
                        if (r2 < 0 || r2 == r1) continue;
                        t1r.push_back(r2);
                    }
                    t1r[st - 1] = (int)(t1r.size() - st);  // count stored at header
                }
            }
        }
        size_t P = plo.size();
        bool any1 = false;
        for (size_t z = 0; z < t1s.size(); ++z) if (t1r[t1s[z]] > 0) { any1 = true; break; }
        if (P == 0 && !any1) { slowMoves(s, out, base); return; }
        const int G = off[cR];
        cnt.assign((size_t)G + 1, 0);
        for (size_t z = 0; z < P; ++z) ++cnt[plo[z] + 1];
        for (int g = 0; g < G; ++g) cnt[g + 1] += cnt[g];
        buf.resize(P);
        pos.assign(cnt.begin(), cnt.end());
        for (size_t z = 0; z < P; ++z) buf[pos[plo[z]]++] = phi[z];
        out.reserve(base + P + t1r.size());
        size_t ecap = P + t1r.size();
        if (ek.size() < ecap) { ek.resize(ecap); ek2.resize(ecap); eest.resize(ecap); }
        unsigned long long* EK = ek.data();
        unsigned* EK2 = ek2.data();
        double* EE = eest.data();
        size_t w = 0;
        const double Cc = M.capacity, pen = M.penalty;
        const double* dem = M.demand.data();
        int* B = buf.data();
        const int* ND = nodes.data();
        for (int g1 = 0; g1 < G; ++g1) {
            int st = cnt[g1], en = cnt[g1 + 1];
            if (st == en) continue;
            for (int a = st + 1; a < en; ++a) {
                int x = B[a], b = a - 1;
                while (b >= st && B[b] > x) { B[b + 1] = B[b]; --b; }
                B[b + 1] = x;
            }
            int r1 = gr[g1], i = g1 - off[r1] - 1, u = ND[g1];
            int last = -1;
            for (int a = st; a < en; ++a) {
                int g2 = B[a];
                if (g2 == last) continue;
                last = g2;
                int r2 = gr[g2], j = g2 - off[r2] - 1, v = ND[g2];
                int pu = fastIns(s, r2, j, u);
                int pv = fastIns(s, r1, i, v);
                out.push_back({0, r1, i, r2, j, pu, pv});
                double dd = partN(ND + off[r1], i, v, pv) + partN(ND + off[r2], j, u, pu);
                double L1 = cl[r1], L2 = cl[r2], du = dem[u], dv = dem[v];
                dd += pen * (std::max(0.0, L1 - du + dv - Cc) + std::max(0.0, L2 - dv + du - Cc) -
                             std::max(0.0, L1 - Cc) - std::max(0.0, L2 - Cc));
                EK[w] = keyA(0, r1, i, r2, j);
                EK2[w] = keyB(pu, pv);
                EE[w] = dd;
                ++w;
            }
        }
        for (size_t z = 0; z < t1s.size(); ++z) {
            int h = t1s[z];
            int c = t1r[h];
            if (c == 0) continue;
            // header slot held r1 originally; recover r1 from next-free logic: stored separately
            int* L = t1r.data() + h + 1;
            std::sort(L, L + c);
            int r1 = t1rr[z];
            int u = ND[off[r1] + 1];
            int last = -1;
            for (int a = 0; a < c; ++a) {
                if (L[a] == last) continue;
                last = L[a];
                int ps = fastIns(s, last, -1, u);
                out.push_back({1, r1, last, ps, 0, 0, 0});
                const int* n2 = ND + off[last];
                int p = n2[ps], q = n2[ps + 1];
                double dd = d(p, u) + d(u, q) - d(p, q) - d(0, u) - d(u, 0);
                double L2 = cl[last], du = dem[u];
                dd += pen * (std::max(0.0, L2 + du - Cc) - std::max(0.0, L2 - Cc) - std::max(0.0, du - Cc));
                EK[w] = keyA(1, r1, last, ps, 0);
                EK2[w] = 0u;
                EE[w] = dd;
                ++w;
            }
        }
        mbase = out.data() + base;
        mcount = w;
    }

    void slowMoves(const Sol& s, std::vector<Move>& out, size_t base) {
        for (int r1 = 0; r1 < cR; ++r1) {
            if (!okr[r1]) continue;
            const auto& A = s[r1];
            for (int i = 0; i < clen[r1]; ++i) {
                int u = A[i];
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t], r2 = locR[v];
                    if (r2 < 0 || r2 == r1) continue;
                    if (clen[r1] == 1 && clen[r2] == 1) continue;
                    int j = locP[v];
                    int ra = r1, ia = i, rb = r2, ib = j;
                    if (ra > rb) { std::swap(ra, rb); std::swap(ia, ib); }
                    double c;
                    int pu = bestIns(s[rb], ib, s[ra][ia], c);
                    int pv = bestIns(s[ra], ia, s[rb][ib], c);
                    out.push_back({0, ra, ia, rb, ib, pu, pv});
                }
                if (clen[r1] == 1) {
                    for (int t = 0; t < K; ++t) {
                        int v = nb[t], r2 = locR[v];
                        if (r2 < 0 || r2 == r1) continue;
                        double c;
                        out.push_back({1, r1, r2, bestIns(s[r2], -1, u, c), 0, 0, 0});
                    }
                }
            }
        }
        if (out.size() == base) {
            for (int r1 = 0; r1 < cR; ++r1) {
                if (!okr[r1] || clen[r1] != 1) continue;
                for (int r2 = 0; r2 < cR; ++r2)
                    if (r2 != r1 && okr[r2] && clen[r2] > 0) {
                        double c;
                        out.push_back({1, r1, r2, bestIns(s[r2], -1, s[r1][0], c), 0, 0, 0});
                    }
            }
            for (int r1 = 0; r1 < cR && out.size() == base; ++r1)
                for (int r2 = r1 + 1; r2 < cR; ++r2)
                    if (okr[r1] && okr[r2] && clen[r1] > 0 && clen[r2] > 0) {
                        double c;
                        int pu = bestIns(s[r2], 0, s[r1][0], c);
                        int pv = bestIns(s[r1], 0, s[r2][0], c);
                        out.push_back({0, r1, 0, r2, 0, pu, pv});
                    }
        }
        std::sort(out.begin() + base, out.end());
        out.erase(std::unique(out.begin() + base, out.end()), out.end());
    }

    Sol apply(const Sol& s, const Move& m) override {
        if (m[0] == 0) {
            int r1 = m[1], i = m[2], r2 = m[3], j = m[4], pu = m[5], pv = m[6];
            Sol t = s;
            int u = s[r1][i], v = s[r2][j];
            auto& A = t[r1];
            A.erase(A.begin() + i);
            A.insert(A.begin() + pv, v);
            auto& B = t[r2];
            B.erase(B.begin() + j);
            B.insert(B.begin() + pu, u);
            return t;
        }
        int r1 = m[1], r2 = m[2], pos = m[3];
        int u = s[r1][0];
        Sol t;
        t.reserve(s.size());
        for (int r = 0; r < (int)s.size(); ++r) {
            if (r == r1) continue;
            t.push_back(s[r]);
            if (r == r2) t.back().insert(t.back().begin() + pos, u);
        }
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        if (&s == cptr && mcount) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move)) {
                size_t idx = dpos / sizeof(Move);
                unsigned orv = (unsigned)(m[1] | m[2] | m[3] | m[4] | m[5] | m[6]);
                if ((unsigned)m[0] < 2u && orv < 32768u && ek[idx] == keyA(m[0], m[1], m[2], m[3], m[4]) &&
                    ek2[idx] == keyB(m[5], m[6]) && (int)s.size() == cR) {
                    if (m[0] == 0) {
                        int r1 = m[1], r2 = m[3];
                        if (r1 < cR && r2 < cR && cached(s, r1) && cached(s, r2) &&
                            m[2] < clen[r1] && m[4] < clen[r2] &&
                            s[r1][m[2]] == nodes[off[r1] + 1 + m[2]] && s[r2][m[4]] == nodes[off[r2] + 1 + m[4]])
                            return eest[idx];
                    } else {
                        int r1 = m[1], r2 = m[2];
                        if (r1 < cR && r2 < cR && cached(s, r1) && cached(s, r2) && clen[r1] == 1 &&
                            s[r1][0] == nodes[off[r1] + 1])
                            return eest[idx];
                    }
                }
            }
        }
        const double C = M.capacity, pen = M.penalty;
        if (m[0] == 0) {
            int r1 = m[1], i = m[2], r2 = m[3], j = m[4], pu = m[5], pv = m[6];
            if (!okOf(s, r1) || !okOf(s, r2)) return full(s, m);
            const auto& A = s[r1];
            const auto& B = s[r2];
            int u = A[i], v = B[j];
            double dd = part(A, i, v, pv) + part(B, j, u, pu);
            double L1 = loadOf(s, r1), L2 = loadOf(s, r2), du = M.demand[u], dv = M.demand[v];
            dd += pen * (std::max(0.0, L1 - du + dv - C) + std::max(0.0, L2 - dv + du - C) -
                         std::max(0.0, L1 - C) - std::max(0.0, L2 - C));
            return dd;
        }
        int r1 = m[1], r2 = m[2], pos = m[3];
        const auto& A = s[r1];
        if (A.size() != 1 || !okOf(s, r1) || !okOf(s, r2)) return full(s, m);
        const auto& B = s[r2];
        int u = A[0];
        int p = pos > 0 ? B[pos - 1] : 0, q = pos < (int)B.size() ? B[pos] : 0;
        double dd = d(p, u) + d(u, q) - d(p, q) - d(0, u) - d(u, 0);
        double L2 = loadOf(s, r2), du = M.demand[u];
        dd += pen * (std::max(0.0, L2 + du - C) - std::max(0.0, L2 - C) - std::max(0.0, du - C));
        return dd;
    }

private:
    const CVRP& M;
    int K;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf, locR, locP, clen;
    std::vector<double> cl;
    std::vector<char> okr;
    std::vector<const int*> rptr;
    int cR = 0;
    const Sol* cptr = nullptr;
    int maxLen = 0;
    std::vector<int> off, nodes;
    std::vector<double> ec;
    struct Top3 { double c[3]; int e[3]; unsigned st = 0; };
    struct TE { short e[3]; unsigned short st = 0; };
    std::vector<int> adjS, adjV, tmpv;
    int maxDeg = 0;
    char dupF = 0;
    std::vector<unsigned long long> ek;
    std::vector<unsigned> ek2;
    std::vector<double> eest;
    const Move* mbase = nullptr;
    size_t mcount = 0;
    static inline unsigned long long keyA(int t, int a, int b, int c, int e) {
        return (unsigned long long)(unsigned)t | ((unsigned long long)(unsigned)a << 1) |
               ((unsigned long long)(unsigned)b << 16) | ((unsigned long long)(unsigned)c << 31) |
               ((unsigned long long)(unsigned)e << 46);
    }
    static inline unsigned keyB(int f, int g) { return (unsigned)f | ((unsigned)g << 16); }
    // same as part(A, i, w, pw) on the depot-padded node array of the route
    inline double partN(const int* nd, int i, int w, int pw) const {
        int a = nd[i], u = nd[i + 1], b = nd[i + 2];
        double dd = d(a, b) - d(a, u) - d(u, b);
        int p = pw <= i ? nd[pw] : nd[pw + 1];
        int q = pw < i ? nd[pw + 1] : nd[pw + 2];
        return dd + d(p, w) + d(w, q) - d(p, q);
    }
    // move generation scratch
    std::vector<int> plo, phi, cnt, pos, buf, gr, t1r, t1s, t1rr;
    // persistent per-route-content cache of top3
    std::vector<int> oNodes, oOff, oClen, rid, oRid, fo, freeIds;
    std::vector<unsigned> fos, ver, idMark;
    std::vector<TE> tab;
    unsigned foGen = 0, mkGen = 0;
    size_t tabIds = 0;
    static constexpr size_t LIMIT = (size_t)1 << 20;

    void top3(int w, int r, Top3& T) const {
        const double inf = std::numeric_limits<double>::infinity();
        T.c[0] = T.c[1] = T.c[2] = inf;
        T.e[0] = T.e[1] = T.e[2] = -1;
        const int* nd = nodes.data() + off[r];
        const double* e = ec.data() + off[r];
        const int L = clen[r];
        const double* Dw = Dp + (size_t)w * S;
        for (int k = 0; k <= L; ++k) {
            double c = Dw[nd[k]] + Dw[nd[k + 1]] - e[k];
            if (c < T.c[2]) {
                if (c < T.c[1]) {
                    T.c[2] = T.c[1]; T.e[2] = T.e[1];
                    if (c < T.c[0]) { T.c[1] = T.c[0]; T.e[1] = T.e[0]; T.c[0] = c; T.e[0] = k; }
                    else { T.c[1] = c; T.e[1] = k; }
                } else { T.c[2] = c; T.e[2] = k; }
            }
        }
    }

    // same result as bestIns(s[r], skip, w)
    int fastIns(const Sol& s, int r, int skip, int w) {
        if (!okr[r]) { double c; return bestIns(s[r], skip, w, c); }
        int E[3];
        int id = rid[r];
        if (id >= 0 && (size_t)id < tabIds) {
            TE& TT = tab[(size_t)id * S + (size_t)w];
            unsigned short vs = (unsigned short)ver[id];
            if (TT.st != vs) {
                Top3 t3;
                top3(w, r, t3);
                TT.e[0] = (short)t3.e[0]; TT.e[1] = (short)t3.e[1]; TT.e[2] = (short)t3.e[2];
                TT.st = vs;
            }
            E[0] = TT.e[0]; E[1] = TT.e[1]; E[2] = TT.e[2];
        } else {
            Top3 t3;
            top3(w, r, t3);
            E[0] = t3.e[0]; E[1] = t3.e[1]; E[2] = t3.e[2];
        }
        if (skip < 0) return E[0] < 0 ? 0 : E[0];
        int be = -1;
        for (int k = 0; k < 3; ++k) {
            int e = E[k];
            if (e < 0) break;
            if (e != skip && e != skip + 1) { be = e; break; }
        }
        if (be < 0) return skip;
        const int* nd = nodes.data() + off[r];
        const double* Dw = Dp + (size_t)w * S;
        double bc = Dw[nd[be]] + Dw[nd[be + 1]] - ec[(size_t)off[r] + be];
        int prev = nd[skip], q = nd[skip + 2];
        double c0 = Dw[prev] + Dw[q] - d(prev, q);
        if (c0 < bc) return skip;
        if (c0 == bc) return be < skip ? be : skip;
        return be < skip ? be : be - 1;
    }

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    double part(const std::vector<int>& A, int i, int w, int pw) const {
        int L = (int)A.size(), u = A[i];
        int a = i > 0 ? A[i - 1] : 0, b = i + 1 < L ? A[i + 1] : 0;
        double dd = d(a, b) - d(a, u) - d(u, b);
        int mlen = L - 1;
        auto at = [&](int k) { return k < i ? A[k] : A[k + 1]; };
        int p = pw > 0 ? at(pw - 1) : 0, q = pw < mlen ? at(pw) : 0;
        return dd + d(p, w) + d(w, q) - d(p, q);
    }

    int bestIns(const std::vector<int>& A, int skip, int w, double& bc) const {
        int L = (int)A.size();
        int mlen = skip >= 0 ? L - 1 : L;
        int best = 0, prev = 0;
        bc = std::numeric_limits<double>::infinity();
        const double* Dw = Dp + (size_t)w * S;
        for (int pos = 0; pos <= mlen; ++pos) {
            int q = pos < mlen ? ((skip < 0 || pos < skip) ? A[pos] : A[pos + 1]) : 0;
            double c = Dw[prev] + Dw[q] - d(prev, q);
            if (c < bc) { bc = c; best = pos; }
            prev = q;
        }
        return best;
    }

    void freeId(int id) {
        if (++ver[id] > 0xFFFFu) {
            ver[id] = 1;
            if ((size_t)id < tabIds)
                for (size_t k = (size_t)id * S, e = (size_t)(id + 1) * S; k < e; ++k) tab[k].st = 0u;
        }
        freeIds.push_back(id);
    }
    int allocId() {
        if (!freeIds.empty()) { int id = freeIds.back(); freeIds.pop_back(); return id; }
        int id = (int)ver.size();
        ver.push_back(1);
        idMark.push_back(0);
        if ((size_t)id >= tabIds && (size_t)(id + 1) * S <= LIMIT) {
            size_t ni = std::max((size_t)id + 1, tabIds * 2);
            ni = std::min(ni, LIMIT / S);
            tab.resize(ni * S);
            tabIds = ni;
        }
        return id;
    }

    void build(const Sol& s) {
        std::fill(locR.begin(), locR.end(), -1);
        dupF = 0;
        std::swap(nodes, oNodes); std::swap(off, oOff); std::swap(clen, oClen); std::swap(rid, oRid);
        const int oR = (int)oRid.size();
        if (++foGen == 0) { std::fill(fos.begin(), fos.end(), 0u); foGen = 1; }
        for (int r = 0; r < oR; ++r)
            if (oRid[r] >= 0) { int c = oNodes[oOff[r] + 1]; fos[c] = foGen; fo[c] = r; }

        cR = (int)s.size();
        cptr = &s;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR); rid.resize(cR);
        off.resize(cR + 1);
        size_t run = 0;
        maxLen = 0;
        for (int r = 0; r < cR; ++r) {
            off[r] = (int)run;
            int len = (int)s[r].size();
            run += (size_t)len + 2;
            if (len > maxLen) maxLen = len;
        }
        off[cR] = (int)run;
        nodes.resize(run);
        ec.resize(run);
        gr.resize(run);
        const double* dem = M.demand.data();
        const int n = M.n;
        for (int r = 0; r < cR; ++r) {
            const auto& A = s[r];
            int len = (int)A.size();
            clen[r] = len;
            rptr[r] = A.data();
            int* nd = nodes.data() + off[r];
            nd[0] = 0;
            double l = 0.0;
            char ok = 1;
            for (int p = 0; p < len; ++p) {
                int c = A[p];
                nd[p + 1] = c;
                if (c >= 1 && c <= n) l += dem[c];
                else ok = 0;
            }
            nd[len + 1] = 0;
            cl[r] = l;
            okr[r] = ok;
            if (ok) {
                double* e = ec.data() + off[r];
                for (int k = 0; k <= len; ++k) e[k] = d(nd[k], nd[k + 1]);
                int* g = gr.data() + off[r] + 1;
                for (int p = 0; p < len; ++p) {
                    if (locR[A[p]] >= 0) dupF = 1;
                    locR[A[p]] = r; locP[A[p]] = p; g[p] = r;
                }
            }
        }
        if (++mkGen == 0) { std::fill(idMark.begin(), idMark.end(), 0u); mkGen = 1; }
        for (int r = 0; r < cR; ++r) {
            rid[r] = -1;
            int len = clen[r];
            if (!okr[r] || len == 0) continue;
            int c = nodes[off[r] + 1];
            if (fos[c] != foGen) continue;
            int o = fo[c];
            if (oClen[o] == len &&
                std::memcmp(nodes.data() + off[r] + 1, oNodes.data() + oOff[o] + 1, (size_t)len * sizeof(int)) == 0) {
                rid[r] = oRid[o];
                idMark[rid[r]] = mkGen;
            }
        }
        for (int o = 0; o < oR; ++o) {
            int id = oRid[o];
            if (id >= 0 && idMark[id] != mkGen) { idMark[id] = mkGen; freeId(id); }
        }
        for (int r = 0; r < cR; ++r)
            if (okr[r] && clen[r] > 0 && rid[r] < 0) { int id = allocId(); rid[r] = id; idMark[id] = mkGen; }
        // type-1 owner routes are recorded in moves via t1rr
        t1rr.clear();
        for (int r = 0; r < cR; ++r) if (okr[r] && clen[r] == 1) t1rr.push_back(r);
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
    int k = (int)params.get("k_neighbors", 8);
    return std::make_unique<SwapStar>(model, k);
}
