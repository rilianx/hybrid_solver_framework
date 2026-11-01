// COMPONENT: {"name": "granular_relocate_customer", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class GranularRelocate : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    GranularRelocate(const CVRP& m, int k) : M(m) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        nbf.assign((size_t)(n + 1) * (K > 0 ? K : 1), 0);
        std::vector<int> idx;
        for (int c = 1; c <= n; ++c) {
            idx.clear();
            for (int o = 1; o <= n; ++o) if (o != c) idx.push_back(o);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) nbf[(size_t)c * K + t] = idx[t];
        }
        loc.assign((size_t)(n + 1) * 2, -1);
        d0c.assign(n + 1, 0.0);
        for (int c = 0; c <= n; ++c) d0c[c] = M.dist(0, c) + M.dist(c, 0);
        d00 = M.dist(0, 0);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const int n = M.n;
        int* lc = loc.data();
        for (size_t z = 0, e = loc.size(); z < e; z += 2) lc[z] = -1;
        int R = (int)s.size(), empty = -1;
        cl.resize(R);
        mxl.resize(R);
        clen.resize(R);
        rptr.resize(R);
        off.resize(R + 1);
        const double* dem = M.demand.data();
        const double C = M.capacity, pen = M.penalty;
        size_t total = 0, run = 0;
        for (int r = 0; r < R; ++r) {
            int len = (int)s[r].size();
            off[r] = (int)run;
            run += len + 2;
            total += len;
        }
        off[R] = (int)run;
        nodes.resize(run);
        ec.resize(run);
        for (int r = 0; r < R; ++r) {
            const auto& rt = s[r];
            int len = (int)rt.size();
            clen[r] = len;
            rptr[r] = rt.data();
            if (len == 0 && empty < 0) empty = r;
            int o = off[r];
            int* nd = nodes.data() + o;
            nd[0] = 0;
            double l = 0.0;
            for (int p = 0; p < len; ++p) {
                int c = rt[p];
                nd[p + 1] = c;
                if (c >= 1 && c <= n) { lc[2 * c] = r; lc[2 * c + 1] = p; l += dem[c]; }
            }
            nd[len + 1] = 0;
            cl[r] = l;
            mxl[r] = std::max(0.0, l - C);
            double* e = ec.data() + o;
            for (int q = 0; q <= len; ++q) e[q] = Dp[(size_t)nd[q] * S + nd[q + 1]];
        }
        cR = R;
        cptr = &s;
        size_t cap = total * (2 * (size_t)K + 1);
        size_t base = out.size();
        out.reserve(base + cap);
        if (ekey.size() < cap) { ekey.resize(cap); eest.resize(cap); }
        unsigned long long* kp = ekey.data();
        double* ep = eest.data();
        size_t w = 0;
        const int* ND = nodes.data();
        const double* EC = ec.data();
        int target = empty < 0 ? R : empty;
        for (int r1 = 0; r1 < R; ++r1) {
            int len = clen[r1];
            const int o1 = off[r1];
            const int* nd = ND + o1 + 1;
            const double L1 = cl[r1], b1 = mxl[r1];
            for (int i = 0; i < len; ++i) {
                int c = nd[i];
                if (c < 1 || c > n) continue;
                const int g1 = o1 + i + 1;
                const double dc = dem[c];
                const double* Dc = Dp + (size_t)c * S;
                const int pp = ND[g1 - 1], nx = ND[g1 + 1];
                const double drem = Dp[(size_t)pp * S + nx] - Dc[pp] - Dc[nx];
                const double pr1 = std::max(0.0, L1 - dc - C) - b1;
                const int* nb = nbf.data() + (size_t)c * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = lc[2 * v];
                    if (r2 < 0) continue;
                    int q = lc[2 * v + 1];
                    if (r2 != r1) {
                        double L2 = cl[r2];
                        double pterm = pen * ((pr1 + std::max(0.0, L2 + dc - C)) - mxl[r2]);
                        int g = off[r2] + q;
                        out.push_back({r1, i, r2, q, 0, 0});
                        {
                            double dd = drem;
                            dd += Dc[ND[g]] + Dc[ND[g + 1]] - EC[g];
                            dd += pterm;
                            kp[w] = key4(r1, i, r2, q); ep[w] = dd; ++w;
                        }
                        out.push_back({r1, i, r2, q + 1, 0, 0});
                        {
                            int g2 = g + 1;
                            double dd = drem;
                            dd += Dc[ND[g2]] + Dc[ND[g2 + 1]] - EC[g2];
                            dd += pterm;
                            kp[w] = key4(r1, i, r2, q + 1); ep[w] = dd; ++w;
                        }
                    } else {
                        int qq = q < i ? q : q - 1;
                        if (qq != i) {
                            out.push_back({r1, i, r1, qq, 0, 0});
                            int e = qq < i ? qq : qq + 1;
                            int g = o1 + e;
                            kp[w] = key4(r1, i, r1, qq);
                            ep[w] = drem + Dc[ND[g]] + Dc[ND[g + 1]] - EC[g];
                            ++w;
                        }
                        if (qq + 1 != i) {
                            int j = qq + 1;
                            out.push_back({r1, i, r1, j, 0, 0});
                            int e = j < i ? j : j + 1;
                            int g = o1 + e;
                            kp[w] = key4(r1, i, r1, j);
                            ep[w] = drem + Dc[ND[g]] + Dc[ND[g + 1]] - EC[g];
                            ++w;
                        }
                    }
                }
                if (len > 1) {
                    out.push_back({r1, i, target, 0, 0, 0});
                    double dd = drem;
                    double L2 = 0.0, m2 = 0.0;
                    if (target < R) {
                        int g = off[target];
                        dd += Dc[ND[g]] + Dc[ND[g + 1]] - EC[g];
                        L2 = cl[target];
                        m2 = mxl[target];
                    } else {
                        dd += Dc[0] + Dc[0] - d00;
                    }
                    dd += pen * ((pr1 + std::max(0.0, L2 + dc - C)) - m2);
                    kp[w] = key4(r1, i, target, 0); ep[w] = dd; ++w;
                }
            }
        }
        mbase = out.data() + base;
        mcount = (total + (size_t)R + 2 < 65536) ? w : 0;
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
        if (&s == cptr) {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move) && ((unsigned)(r1 | i | r2 | j) < 65536u) &&
                (int)s.size() == cR) {
                size_t idx = dpos / sizeof(Move);
                if (ekey[idx] == key4(r1, i, r2, j) && sameRoute(s, r1) && (r2 >= cR || sameRoute(s, r2)))
                    return eest[idx];
            }
        }
        const auto& A = s[r1];
        int len = (int)A.size();
        int c = A[i];
        int p = i > 0 ? A[i - 1] : 0, nx = i + 1 < len ? A[i + 1] : 0;
        const double* Dc = Dp + (size_t)c * S;
        double dd = Dp[(size_t)p * S + nx] - Dc[p] - Dc[nx];
        if (r1 == r2) {
            int mlen = len - 1;
            auto at = [&](int k) { return k < i ? A[k] : A[k + 1]; };
            int a = j > 0 ? at(j - 1) : 0, b = j < mlen ? at(j) : 0;
            return dd + Dc[a] + Dc[b] - Dp[(size_t)a * S + b];
        }
        int a = 0, b = 0;
        double L2 = 0.0;
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            a = j > 0 ? B[j - 1] : 0;
            b = j < (int)B.size() ? B[j] : 0;
            L2 = fastLoad(s, r2, B);
        }
        dd += Dc[a] + Dc[b] - Dp[(size_t)a * S + b];
        double L1 = fastLoad(s, r1, A), dc = M.demand[c], C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - dc - C) - std::max(0.0, L1 - C) +
                           std::max(0.0, L2 + dc - C) - std::max(0.0, L2 - C));
        return dd;
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        if (&s != cptr || (int)s.size() != cR) return delta(s, m);
        const int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        {
            std::uintptr_t dpos = reinterpret_cast<std::uintptr_t>(&m) - reinterpret_cast<std::uintptr_t>(mbase);
            if (dpos < mcount * sizeof(Move) && ((unsigned)(r1 | i | r2 | j) < 65536u)) {
                size_t idx = dpos / sizeof(Move);
                if (ekey[idx] == key4(r1, i, r2, j)) return eest[idx];
            }
        }
        const int len1 = clen[r1];
        if (i < 0 || i >= len1) return delta(s, m);
        const int g1 = off[r1] + i + 1;
        const int* nd = nodes.data();
        const int c = nd[g1];
        if ((unsigned)c > (unsigned)M.n) return delta(s, m);
        const double* Dc = Dp + (size_t)c * S;
        const int pp = nd[g1 - 1], nx = nd[g1 + 1];
        double dd = Dp[(size_t)pp * S + nx] - Dc[pp] - Dc[nx];
        if (r1 == r2) {
            int e = j < i ? j : j + 1;
            if (j < 0 || e > len1) return delta(s, m);
            int g = off[r1] + e;
            return dd + Dc[nd[g]] + Dc[nd[g + 1]] - ec[g];
        }
        double L2 = 0.0;
        if (r2 < cR) {
            if (j < 0 || j > clen[r2]) return delta(s, m);
            int g = off[r2] + j;
            dd += Dc[nd[g]] + Dc[nd[g + 1]] - ec[g];
            L2 = cl[r2];
        } else {
            dd += d0c[c] - d00;
        }
        const double C = M.capacity, dc = M.demand[c], L1 = cl[r1];
        dd += M.penalty * (std::max(0.0, L1 - dc - C) - std::max(0.0, L1 - C) +
                           std::max(0.0, L2 + dc - C) - std::max(0.0, L2 - C));
        return dd;
    }

    Move tabu_key(const Move& m) override { return {m[2], m[3], m[0], m[1], 0, 0}; }

private:
    const CVRP& M;
    int K;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf;
    std::vector<int> loc;       // loc[2c] = ruta, loc[2c+1] = posición
    std::vector<int> nodes;     // rutas con depósito en ambos extremos, contiguas
    std::vector<double> ec;     // costo de la arista (q, q+1) de cada ruta
    std::vector<int> off, clen;
    std::vector<double> cl, mxl;
    std::vector<double> d0c;
    double d00 = 0.0;
    int cR = 0;
    const Sol* cptr = nullptr;
    std::vector<unsigned long long> ekey;
    std::vector<double> eest;
    const Move* mbase = nullptr;
    size_t mcount = 0;
    std::vector<const int*> rptr;

    inline bool sameRoute(const Sol& s, int r) const {
        const auto& R = s[r];
        return R.data() == rptr[r] && (int)R.size() == clen[r];
    }

    // cached load if the route keeps its buffer, length and endpoints since moves(); otherwise exact
    inline double fastLoad(const Sol& s, int r, const std::vector<int>& R) const {
        if (&s == cptr && r < cR) {
            int len = (int)R.size();
            if (len == clen[r] && R.data() == rptr[r]) {
                if (len == 0) return cl[r];
                const int* nd = nodes.data() + off[r] + 1;
                if (R[0] == nd[0] && R[len - 1] == nd[len - 1]) return cl[r];
            }
        }
        return loadOf(r, R);
    }

    static inline unsigned long long key4(int a, int b, int c, int d) {
        return (unsigned long long)(unsigned)a | ((unsigned long long)(unsigned)b << 16) |
               ((unsigned long long)(unsigned)c << 32) | ((unsigned long long)(unsigned)d << 48);
    }

    double load(const std::vector<int>& r) const {
        double l = 0.0;
        for (int c : r) if (c >= 1 && c <= M.n) l += M.demand[c];
        return l;
    }
    // carga exacta: la cacheada solo si el contenido de la ruta coincide
    double loadOf(int r, const std::vector<int>& R) const {
        if (r < cR) {
            int len = (int)R.size();
            if (clen[r] == len) {
                if (len == 0) return cl[r];
                if (std::memcmp(R.data(), nodes.data() + off[r] + 1, (size_t)len * sizeof(int)) == 0)
                    return cl[r];
            }
        }
        return load(R);
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<GranularRelocate>(model, k);
}
