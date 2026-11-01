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
        locR.assign(n + 1, -1);
        locP.assign(n + 1, 0);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        size_t base = out.size();
        if (cR >= 32768 || maxLen >= 32768) { slowMoves(s, out, base); return; }
        keys.clear();
        for (int r1 = 0; r1 < cR; ++r1) {
            if (!okr[r1]) continue;
            const auto& A = s[r1];
            const int l1 = clen[r1];
            for (int i = 0; i < l1; ++i) {
                int u = A[i];
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t], r2 = locR[v];
                    if (r2 < 0 || r2 == r1) continue;
                    if (l1 == 1 && clen[r2] == 1) continue;
                    int j = locP[v];
                    if (r1 < r2) keys.push_back(kenc(0, r1, i, r2, j));
                    else keys.push_back(kenc(0, r2, j, r1, i));
                }
                if (l1 == 1) {
                    for (int t = 0; t < K; ++t) {
                        int v = nb[t], r2 = locR[v];
                        if (r2 < 0 || r2 == r1) continue;
                        keys.push_back(kenc(1, r1, r2, 0, 0));
                    }
                }
            }
        }
        if (keys.empty()) { slowMoves(s, out, base); return; }
        std::sort(keys.begin(), keys.end());
        keys.erase(std::unique(keys.begin(), keys.end()), keys.end());
        size_t tsz = (size_t)(M.n + 1) * (size_t)cR;
        useTab = tsz <= ((size_t)1 << 22);
        if (useTab) {
            if (tstamp.size() < tsz) { tstamp.resize(tsz, 0u); tidx.resize(tsz, 0); }
            if (++gen == 0) { std::fill(tstamp.begin(), tstamp.end(), 0u); gen = 1; }
            pool.clear();
        }
        out.reserve(base + keys.size());
        for (unsigned long long k : keys) {
            int ty = (int)(k >> 60);
            int a = (int)((k >> 45) & 32767), b = (int)((k >> 30) & 32767);
            if (ty == 0) {
                int c = (int)((k >> 15) & 32767), e = (int)(k & 32767);
                int pu = fastIns(s, c, e, s[a][b]);
                int pv = fastIns(s, a, b, s[c][e]);
                out.push_back({0, a, b, c, e, pu, pv});
            } else {
                out.push_back({1, a, b, fastIns(s, b, -1, s[a][0]), 0, 0, 0});
            }
        }
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
    std::vector<unsigned long long> keys;
    struct Top3 { double c[3]; int e[3]; };
    std::vector<Top3> pool;
    std::vector<unsigned> tstamp;
    std::vector<int> tidx;
    unsigned gen = 0;
    bool useTab = false;

    static inline unsigned long long kenc(int t, int a, int b, int c, int e) {
        return ((unsigned long long)(unsigned)t << 60) | ((unsigned long long)(unsigned)a << 45) |
               ((unsigned long long)(unsigned)b << 30) | ((unsigned long long)(unsigned)c << 15) |
               (unsigned long long)(unsigned)e;
    }

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
        Top3 loc3;
        const Top3* T;
        if (useTab) {
            size_t id = (size_t)w * cR + r;
            if (tstamp[id] != gen) {
                tstamp[id] = gen;
                tidx[id] = (int)pool.size();
                pool.emplace_back();
                top3(w, r, pool.back());
            }
            T = &pool[tidx[id]];
        } else {
            top3(w, r, loc3);
            T = &loc3;
        }
        if (skip < 0) return T->e[0] < 0 ? 0 : T->e[0];
        int be = -1;
        double bc = 0.0;
        for (int k = 0; k < 3; ++k) {
            int e = T->e[k];
            if (e < 0) break;
            if (e != skip && e != skip + 1) { be = e; bc = T->c[k]; break; }
        }
        const int* nd = nodes.data() + off[r];
        int prev = nd[skip], q = nd[skip + 2];
        const double* Dw = Dp + (size_t)w * S;
        double c0 = Dw[prev] + Dw[q] - d(prev, q);
        if (be < 0) return skip;
        if (c0 < bc) return skip;
        if (c0 == bc) return be < skip ? be : skip;
        return be < skip ? be : be - 1;
    }

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    double full(const Sol& s, const Move& m) { return M.objective(apply(s, m)) - M.objective(s); }

    // cost change on route A: remove A[i], insert w at position pw of the reduced route
    double part(const std::vector<int>& A, int i, int w, int pw) const {
        int L = (int)A.size(), u = A[i];
        int a = i > 0 ? A[i - 1] : 0, b = i + 1 < L ? A[i + 1] : 0;
        double dd = d(a, b) - d(a, u) - d(u, b);
        int mlen = L - 1;
        auto at = [&](int k) { return k < i ? A[k] : A[k + 1]; };
        int p = pw > 0 ? at(pw - 1) : 0, q = pw < mlen ? at(pw) : 0;
        return dd + d(p, w) + d(w, q) - d(p, q);
    }

    // best position to insert w into A with index `skip` removed (skip < 0: nothing removed)
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

    void build(const Sol& s) {
        std::fill(locR.begin(), locR.end(), -1);
        cR = (int)s.size();
        cptr = &s;
        clen.resize(cR); cl.resize(cR); okr.resize(cR); rptr.resize(cR);
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
                for (int p = 0; p < len; ++p) { locR[A[p]] = r; locP[A[p]] = p; }
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
    int k = (int)params.get("k_neighbors", 8);
    return std::make_unique<SwapStar>(model, k);
}
