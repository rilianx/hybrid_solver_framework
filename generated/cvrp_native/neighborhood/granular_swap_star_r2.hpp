// COMPONENT: {"name": "granular_swap_star", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}}}
class GranularSwapStar : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    struct RInfo { int base; int off; int L; double ld; double dd; double cost; bool fast; };
    const Model& M;
    int K;
    std::vector<int> nb, nbs, rof, pof;
    // caché por solución
    std::vector<int> flat, lvp, nvp;
    std::vector<double> ec;
    std::vector<RInfo> ri;
    int nCached = 0;
    const double* Dm = nullptr;
    size_t n1 = 1;
    size_t lastCount = 0;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    inline double pen(double ld) const { return ld > M.capacity + 1e-9 ? M.penalty * (ld - M.capacity) : 0.0; }
    void locate(const S& s) {
        std::fill(rof.begin(), rof.end(), -1);
        const int n = M.n;
        const double* dem = M.demand.data();
        int SZ = (int)s.size();
        ri.resize(SZ);
        int tot = 0;
        for (int r = 0; r < SZ; ++r) { ri[r].off = tot; tot += (int)s[r].size(); }
        flat.resize(tot);
        size_t A = (size_t)tot + SZ;
        lvp.resize(A); nvp.resize(A); ec.resize(A);
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            const int* a = R.data();
            int L = (int)R.size();
            int o = ri[r].off;
            int ao = o + r;
            if (L) std::copy(R.begin(), R.end(), flat.begin() + o);
            double ld = 0.0, dd = 0.0; int last = 0, lastp = -1; bool allv = true, any = false;
            int* LV = lvp.data() + ao;
            int* NV = nvp.data() + ao;
            for (int p = 0; p < L; ++p) {
                LV[p] = lastp;
                int c = a[p];
                if (c >= 1 && c <= n) {
                    dd += dst(last, c); ld += dem[c]; last = c; lastp = p; any = true;
                    if (rof[c] < 0) { rof[c] = r; pof[c] = p; }
                } else allv = false;
            }
            LV[L] = lastp;
            if (any) dd += dst(last, 0);
            int np = L; NV[L] = L;
            for (int p = L - 1; p >= 0; --p) {
                int c = a[p];
                if (c >= 1 && c <= n) np = p;
                NV[p] = np;
            }
            bool fast = allv && Dm;
            if (fast) {
                double* E = ec.data() + ao;
                for (int i = 0; i <= L; ++i) {
                    int x = i ? a[i - 1] : 0;
                    int y = i < L ? a[i] : 0;
                    E[i] = Dm[(size_t)x * n1 + y];
                }
            }
            RInfo& q = ri[r];
            q.base = ao; q.L = L; q.ld = ld; q.dd = dd; q.cost = dd + pen(ld); q.fast = fast;
        }
        nCached = SZ;
    }
    bool cached(const std::vector<int>& R, int r) const {
        if (r < 0 || r >= nCached) return false;
        const RInfo& q = ri[r];
        if (q.L != (int)R.size()) return false;
        return q.L == 0 || std::equal(R.begin(), R.end(), flat.begin() + q.off);
    }
    // mejor posición (índice en R sin `skip`) para insertar c
    int bestIns(const std::vector<int>& R, int skip, int c) const {
        int L = (int)R.size();
        int Lr = L - 1;
        int best = 0; double bc = std::numeric_limits<double>::infinity();
        int a = 0;
        int k = 0;
        for (int i = 0; i <= L; ++i) {
            if (i == skip) continue;
            int b = 0;
            if (i < L) { b = R[i]; if (!valid(b)) b = 0; }
            double cst = dst(a, c) + dst(c, b) - dst(a, b);
            if (cst < bc) { bc = cst; best = k; }
            if (i < L) { a = valid(R[i]) ? R[i] : a; }
            ++k;
            if (k > Lr) break;
        }
        return best;
    }
    // versión rápida: ruta toda válida, con matriz, skip en [0, L)
    int bestInsFast(const int* R, int L, int base, int skip, int c) const {
        const double* row = Dm + (size_t)c * n1;
        const double* E = ec.data() + base;
        int best = 0; double bc = std::numeric_limits<double>::infinity();
        for (int i = 0; i < skip; ++i) {
            int a = i ? R[i - 1] : 0;
            double cst = row[a] + row[R[i]] - E[i];
            if (cst < bc) { bc = cst; best = i; }
        }
        {
            int i = skip + 1;
            int a = skip ? R[skip - 1] : 0;
            int b = i < L ? R[i] : 0;
            double cst = row[a] + row[b] - Dm[(size_t)a * n1 + b];
            if (cst < bc) { bc = cst; best = skip; }
        }
        for (int i = skip + 2; i <= L; ++i) {
            int a = R[i - 1];
            int b = i < L ? R[i] : 0;
            double cst = row[a] + row[b] - E[i];
            if (cst < bc) { bc = cst; best = i - 1; }
        }
        return best;
    }
    // costo (distancia + penalización) de R sin `skip`, con `ins` en el índice q del resto
    double costMod(const std::vector<int>& R, int skip, int ins, int q) const {
        double d = 0.0, ld = 0.0; int prev = 0; bool any = false;
        const double* dem = M.demand.data();
        auto vis = [&](int c) {
            if (!valid(c)) return;
            d += dst(prev, c); ld += dem[c]; prev = c; any = true;
        };
        int L = (int)R.size(), k = 0;
        for (int i = 0; i < L; ++i) {
            if (i == skip) continue;
            if (k == q) vis(ins);
            vis(R[i]);
            ++k;
        }
        if (k == q) vis(ins);
        if (any) d += dst(prev, 0);
        if (ld > M.capacity + 1e-9) d += M.penalty * (ld - M.capacity);
        return d;
    }
    // distancia de la ruta cacheada sin `skip` (cliente válido c), con ins válido en el índice q del resto
    double modDist(const RInfo& I, const int* a, int skip, int c, int ins, int q) const {
        const int* LV = lvp.data() + I.base;
        const int* NV = nvp.data() + I.base;
        int L = I.L;
        int pp = LV[skip]; int pa = pp < 0 ? 0 : a[pp];
        int np = NV[skip + 1]; int nx = np >= L ? 0 : a[np];
        double d = I.dd - dst(pa, c) - dst(c, nx) + dst(pa, nx);
        int i = q < skip ? q : q + 1;
        int p = LV[i]; if (p == skip) p = LV[skip];
        int x = p < 0 ? 0 : a[p];
        p = NV[i]; if (p == skip) p = NV[skip + 1];
        int y = p >= L ? 0 : a[p];
        d += dst(x, ins) + dst(ins, y) - dst(x, y);
        return d;
    }
    void buildMod(const std::vector<int>& R, int skip, int ins, int q, std::vector<int>& out) const {
        out.clear();
        out.reserve(R.size());
        int L = (int)R.size(), k = 0;
        for (int i = 0; i < L; ++i) {
            if (i == skip) continue;
            if (k == q) out.push_back(ins);
            out.push_back(R[i]);
            ++k;
        }
        if (k == q) out.push_back(ins);
    }
    bool sane(const S& s, const hsf::Move& m) const {
        int SZ = (int)s.size();
        if (m[0] < 0 || m[2] < 0 || m[0] >= SZ || m[2] >= SZ || m[0] == m[2]) return false;
        int L1 = (int)s[m[0]].size(), L2 = (int)s[m[2]].size();
        return m[1] >= 0 && m[1] < L1 && m[3] >= 0 && m[3] < L2 &&
               m[4] >= 0 && m[4] <= L2 - 1 && m[5] >= 0 && m[5] <= L1 - 1;
    }
public:
    GranularSwapStar(const Model& m, int k) : M(m) {
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
        nbs = nb;
        for (int c = 1; c <= n && K > 0; ++c)
            std::sort(nbs.begin() + (size_t)c * K, nbs.begin() + (size_t)(c + 1) * K);
        rof.assign(n + 1, -1); pof.assign(n + 1, -1);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        locate(s);
        if (out.capacity() < lastCount) out.reserve(lastCount);
        int SZ = (int)s.size();
        int N1 = M.n + 1;
        const int n = M.n;
        const int* NB = nb.data();
        const int* RO = rof.data();
        const int* PO = pof.data();
        for (int r1 = 0; r1 < SZ; ++r1) {
            const auto& A = s[r1];
            const int* ap = A.data();
            int L1 = (int)A.size();
            const RInfo& IA = ri[r1];
            for (int p1 = 0; p1 < L1; ++p1) {
                int u = ap[p1];
                if (u < 1 || u > n || RO[u] != r1 || PO[u] != p1) continue;
                const int* nu = NB + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nu[t];
                    int r2 = RO[v];
                    if (r2 < 0 || r2 == r1) continue;
                    if (r1 > r2 && std::binary_search(nbs.begin() + (size_t)v * K,
                                                      nbs.begin() + (size_t)(v + 1) * K, u)) continue;
                    int p2 = PO[v];
                    const RInfo& IB = ri[r2];
                    int q1 = IB.fast ? bestInsFast(s[r2].data(), IB.L, IB.base, p2, u) : bestIns(s[r2], p2, u);
                    int q2 = IA.fast ? bestInsFast(ap, L1, IA.base, p1, v) : bestIns(A, p1, v);
                    out.push_back({r1, p1, r2, p2, q1, q2, std::min(u, v) * N1 + std::max(u, v)});
                }
            }
        }
        if (out.empty()) {
            int a = -1, b = -1;
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) { if (a < 0) a = r; else { b = r; break; } }
            if (b >= 0) out.push_back({a, 0, b, 0, 0, 0, 0});
            else out.push_back({-1, 0, -1, 0, 0, 0, 0});
        }
        lastCount = out.size();
    }
    S apply(const S& s, const hsf::Move& m) override {
        if (!sane(s, m)) return s;
        int SZ = (int)s.size();
        S t(SZ);
        for (int r = 0; r < SZ; ++r)
            if (r != m[0] && r != m[2]) t[r] = s[r];
        const auto& A = s[m[0]];
        const auto& B = s[m[2]];
        int u = A[m[1]], v = B[m[3]];
        buildMod(A, m[1], v, m[5], t[m[0]]);
        buildMod(B, m[3], u, m[4], t[m[2]]);
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        if (!sane(s, m)) return 0.0;
        const auto& A = s[m[0]];
        const auto& B = s[m[2]];
        int u = A[m[1]], v = B[m[3]];
        if (valid(u) && valid(v) && cached(A, m[0]) && cached(B, m[2])) {
            const RInfo& IA = ri[m[0]];
            const RInfo& IB = ri[m[2]];
            const double* dem = M.demand.data();
            double dA = modDist(IA, A.data(), m[1], u, v, m[5]);
            double dB = modDist(IB, B.data(), m[3], v, u, m[4]);
            double lA = IA.ld - dem[u] + dem[v];
            double lB = IB.ld - dem[v] + dem[u];
            return (dA + pen(lA)) + (dB + pen(lB)) - IA.cost - IB.cost;
        }
        return costMod(A, m[1], v, m[5]) + costMod(B, m[3], u, m[4])
             - costMod(A, -1, 0, -1) - costMod(B, -1, 0, -1);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-5, m[6], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    return std::make_unique<GranularSwapStar>(model, k);
}
