// COMPONENT: {"name": "granular_relocate", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 40]}, "new_route": {"type": "int", "range": [0, 1]}}}
class GranularRelocate : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K;
    bool newRoute;
    std::vector<int> nb, rof, pof;
    std::vector<char> mark;
    std::vector<int> b1, b2;
    // caché por solución: contenido plano de cada ruta y su carga
    std::vector<int> flat, cOff;
    std::vector<double> cLoad;
    int nCached = 0;
    size_t lastCount = 0;
    const double* Dm = nullptr;
    size_t n1 = 1;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    bool valid(int c) const { return c >= 1 && c <= M.n; }
    template <bool TRUST>
    double routeLoad(const std::vector<int>& R, int r) const {
        if (r < nCached) {
            int o = cOff[r];
            int l = cOff[r + 1] - o;
            if (l == (int)R.size() && (TRUST || std::equal(R.begin(), R.end(), flat.begin() + o))) return cLoad[r];
        }
        const int n = M.n;
        const double* dem = M.demand.data();
        double ld = 0.0;
        for (int c : R) if (c >= 1 && c <= n) ld += dem[c];
        return ld;
    }
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
        const int n = M.n;
        const double* dem = M.demand.data();
        int SZ = (int)s.size();
        cOff.resize(SZ + 1);
        cLoad.resize(SZ);
        flat.clear();
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            cOff[r] = (int)flat.size();
            flat.insert(flat.end(), R.begin(), R.end());
            double ld = 0.0;
            int len = (int)R.size();
            for (int p = 0; p < len; ++p) {
                int c = R[p];
                if (c >= 1 && c <= n) {
                    ld += dem[c];
                    if (rof[c] < 0) { rof[c] = r; pof[c] = p; }
                }
            }
            cLoad[r] = ld;
        }
        cOff[SZ] = (int)flat.size();
        nCached = SZ;
    }
    bool canon(int c, int r, int p) const { return valid(c) && rof[c] == r && pof[c] == p; }
public:
    GranularRelocate(const Model& m, int k, bool nr) : M(m), newRoute(nr) {
        int n = M.n;
        n1 = (size_t)n + 1;
        Dm = M.useMatrix ? M.D.data() : nullptr;
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
        if (out.capacity() < lastCount) out.reserve(lastCount);
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
        lastCount = out.size();
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
    inline double pen(double load) const {
        return load > M.capacity + 1e-9 ? M.penalty * (load - M.capacity) : 0.0;
    }
    double delta(const S& s, const hsf::Move& m) override { return eval<false>(s, m); }
    bool has_estimate() const override { return true; }
    double estimate(const S& s, const hsf::Move& m) override { return eval<true>(s, m); }
    template <bool TRUST>
    double eval(const S& s, const hsf::Move& m) const {
        int r1 = m[0], p1 = m[1], r2 = m[2], p2 = m[3];
        const auto& A = s[r1];
        const int* a = A.data();
        int lenA = (int)A.size();
        int c = a[p1];
        bool cv = valid(c);
        double d = 0.0;
        // quitar c de A
        if (cv) {
            int pa = 0, nbx = 0;
            for (int i = p1 - 1; i >= 0; --i) if (valid(a[i])) { pa = a[i]; break; }
            for (int i = p1 + 1; i < lenA; ++i) if (valid(a[i])) { nbx = a[i]; break; }
            d += dst(pa, nbx) - dst(pa, c) - dst(c, nbx);
        }
        if (r1 == r2) {
            if (cv) {
                // insertar en b1 = A sin p1, en la posición p2
                int L = lenA - 1;
                int pa = 0, nbx = 0;
                for (int i = p2 - 1; i >= 0; --i) {
                    int v = a[i < p1 ? i : i + 1];
                    if (valid(v)) { pa = v; break; }
                }
                for (int i = p2; i < L; ++i) {
                    int v = a[i < p1 ? i : i + 1];
                    if (valid(v)) { nbx = v; break; }
                }
                d += dst(pa, c) + dst(c, nbx) - dst(pa, nbx);
            }
            return d;
        }
        double dc = cv ? M.demand[c] : 0.0;
        double loadA = routeLoad<TRUST>(A, r1);
        double loadB1 = cv ? loadA - dc : loadA;
        d += pen(loadB1) - pen(loadA);
        if (r2 >= (int)s.size()) {
            if (cv) {
                d += dst(0, c) + dst(c, 0);
                d += pen(M.demand[c]);
            }
            return d;
        }
        const auto& B = s[r2];
        const int* b = B.data();
        int lenB = (int)B.size();
        double loadB = routeLoad<TRUST>(B, r2);
        double loadB2 = cv ? loadB + dc : loadB;
        if (cv) {
            int pa = 0, nbx = 0;
            for (int i = p2 - 1; i >= 0; --i) if (valid(b[i])) { pa = b[i]; break; }
            for (int i = p2; i < lenB; ++i) if (valid(b[i])) { nbx = b[i]; break; }
            d += dst(pa, c) + dst(c, nbx) - dst(pa, nbx);
        }
        d += pen(loadB2) - pen(loadB);
        return d;
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-1, m[4], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 12);
    int nr = (int)params.get("new_route", 1);
    return std::make_unique<GranularRelocate>(model, k, nr != 0);
}
