// COMPONENT: {"name": "granular_intra_or_opt", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [2, 5]}, "use_reversed": {"type": "int", "range": [0, 1]}}}
class GranularIntraOrOpt : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    struct RI { int eb; int po; int L; const int* ptr; bool ok; };
    const Model& M;
    int K, Lmax, nn;
    bool useRev;
    std::vector<int> nb, rof, pof;
    std::vector<int> scratch;
    // caché por solución
    std::vector<double> ec;
    std::vector<double> rv;
    int LM1 = 3;
    std::vector<RI> ri;
    std::vector<int> nl, nc;
    std::vector<int> flat;
    std::vector<std::vector<hsf::Move>> rm;
    bool haveCache = false, clean = false;
    int pendR = -1;
    std::vector<int> pendRoute;
    int nCached = 0;
    const double* Dm = nullptr;
    size_t n1 = 1;
    size_t lastCount = 0;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool valid(int c) const { return c >= 1 && c <= nn; }
    void routeEdges(int r, const int* a) {
        int L = ri[r].L;
        double* E = ec.data() + ri[r].eb;
        if (L == 0) { E[0] = 0.0; return; }
        int prev = 0;
        for (int p = 0; p < L; ++p) { E[p] = dst(prev, a[p]); prev = a[p]; }
        E[L] = dst(prev, 0);
        double* RV = rv.data() + (size_t)ri[r].po * LM1;
        for (int p = 0; p < L; ++p) {
            int pv = p > 0 ? a[p - 1] : 0;
            double* row = RV + (size_t)p * LM1;
            for (int l = 1; l <= Lmax && p + l <= L; ++l) {
                int e = p + l - 1;
                int nx = e + 1 < L ? a[e + 1] : 0;
                row[l] = dst(pv, nx) - E[p] - E[e + 1];
            }
        }
    }
    void routeNl(int r, const int* a) {
        int L = ri[r].L;
        if (L < 3) return;
        size_t KK = (size_t)std::max(K, 1);
        const int* NB = nb.data();
        const int* RO = rof.data();
        const int* PO = pof.data();
        int base = ri[r].po;
        for (int i = 0; i < L; ++i) {
            int c = a[i];
            int cnt = 0;
            if (c >= 1 && c <= nn) {
                int* dstl = nl.data() + (size_t)(base + i) * KK;
                const int* nu = NB + (size_t)c * K;
                for (int t = 0; t < K; ++t) {
                    int v = nu[t];
                    if (RO[v] == r) dstl[cnt++] = PO[v];
                }
            }
            nc[base + i] = cnt;
        }
    }
    void genRoute(int r, const int* a, std::vector<hsf::Move>& out) {
        out.clear();
        int L = ri[r].L;
        if (L < 3) return;
        const int* RO = rof.data();
        const int* PO = pof.data();
        size_t KK = (size_t)std::max(K, 1);
        const bool ur = useRev;
        int base = ri[r].po;
        for (int p = 0; p < L; ++p) {
            int f = a[p];
            if (f < 1 || f > nn || RO[f] != r || PO[f] != p) continue;
            int lmax = std::min(Lmax, L - p);
            const int* lf = nl.data() + (size_t)(base + p) * KK;
            int cf = nc[base + p];
            for (int l = 2; l <= lmax; ++l) {
                int e = p + l - 1;
                int g = a[e];
                for (int t = 0; t < cf; ++t) {
                    int pv = lf[t];
                    if (pv >= p && pv <= e) continue;
                    int pr = pv < p ? pv : pv - l;
                    if (pr + 1 != p) out.push_back({r, p, l, pr + 1, 0, f, 0});
                    if (ur) out.push_back({r, p, l, pr, 1, f, 0});
                }
                if (g >= 1 && g <= nn) {
                    const int* lg = nl.data() + (size_t)(base + e) * KK;
                    int cg = nc[base + e];
                    for (int t = 0; t < cg; ++t) {
                        int pv = lg[t];
                        if (pv >= p && pv <= e) continue;
                        int pr = pv < p ? pv : pv - l;
                        if (pr != p) out.push_back({r, p, l, pr, 0, f, 0});
                        if (ur) out.push_back({r, p, l, pr + 1, 1, f, 0});
                    }
                }
            }
        }
    }
    void locate(const S& s) {
        std::fill(rof.begin(), rof.end(), -1);
        int SZ = (int)s.size();
        ri.resize(SZ);
        int tot = 0, assigned = 0;
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            const int* a = R.data();
            int L = (int)R.size();
            ri[r].po = tot; ri[r].eb = tot + r; ri[r].L = L; ri[r].ptr = a;
            tot += L;
            bool ok = true;
            for (int p = 0; p < L; ++p) {
                int c = a[p];
                if (c >= 1 && c <= nn) { if (rof[c] < 0) { rof[c] = r; pof[c] = p; ++assigned; } }
                else ok = false;
            }
            ri[r].ok = ok;
        }
        clean = (assigned == tot);
        flat.resize(tot);
        for (int r = 0; r < SZ; ++r)
            if (ri[r].L) std::copy(s[r].begin(), s[r].end(), flat.begin() + ri[r].po);
        ec.resize((size_t)tot + SZ);
        if (rv.size() < (size_t)tot * LM1) rv.resize((size_t)tot * LM1);
        for (int r = 0; r < SZ; ++r) {
            if (!ri[r].ok) continue;
            routeEdges(r, s[r].data());
        }
        size_t KK = (size_t)std::max(K, 1);
        if (nl.size() < (size_t)tot * KK) nl.resize((size_t)tot * KK);
        if (nc.size() < (size_t)tot) nc.resize(tot);
        for (int r = 0; r < SZ; ++r) routeNl(r, s[r].data());
        if ((int)rm.size() < SZ) rm.resize(SZ);
        for (int r = 0; r < SZ; ++r) genRoute(r, s[r].data(), rm[r]);
        nCached = SZ;
        haveCache = true;
    }
    void updateRoute(int r, const int* a) {
        int L = ri[r].L;
        int base = ri[r].po;
        std::copy(a, a + L, flat.begin() + base);
        for (int p = 0; p < L; ++p) pof[a[p]] = p;
        routeEdges(r, a);
        routeNl(r, a);
        genRoute(r, a, rm[r]);
    }
    double routeCost(const std::vector<int>& R) const {
        double d = 0.0, ld = 0.0; int prev = 0; bool any = false;
        for (int c : R) {
            if (!valid(c)) continue;
            d += dst(prev, c); ld += M.demand[c]; prev = c; any = true;
        }
        if (any) d += dst(prev, 0);
        if (ld > M.capacity + 1e-9) d += M.penalty * (ld - M.capacity);
        return d;
    }
    void build(const std::vector<int>& R, int p, int l, int q, bool rev, std::vector<int>& out) const {
        out.clear();
        int L = (int)R.size();
        out.reserve(L);
        int Lr = L - l;
        for (int k = 0; k <= Lr; ++k) {
            if (k == q) {
                if (!rev) for (int i = p; i < p + l; ++i) out.push_back(R[i]);
                else for (int i = p + l - 1; i >= p; --i) out.push_back(R[i]);
            }
            if (k < Lr) out.push_back(R[k < p ? k : k + l]);
        }
    }
    bool sane(const S& s, const hsf::Move& m) const {
        if (m[0] < 0 || m[0] >= (int)s.size()) return false;
        int L = (int)s[m[0]].size();
        int p = m[1], l = m[2], q = m[3];
        return l >= 1 && p >= 0 && p + l <= L && q >= 0 && q <= L - l;
    }
public:
    GranularIntraOrOpt(const Model& m, int k, int lm, bool ur) : M(m), Lmax(std::max(2, lm)), useRev(ur) {
        int n = M.n;
        nn = n;
        n1 = (size_t)n + 1;
        LM1 = Lmax + 1;
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
        rof.assign(n + 1, -1); pof.assign(n + 1, -1);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        int SZ = (int)s.size();
        int upd = -2;
        if (haveCache && clean && SZ == nCached) {
            upd = -1;
            for (int r = 0; r < SZ; ++r) {
                const auto& R = s[r];
                int L = ri[r].L;
                if ((int)R.size() != L) { upd = -2; break; }
                const int* a = R.data();
                const int* f = flat.data() + ri[r].po;
                if (L && !std::equal(a, a + L, f)) {
                    if (upd == -1 && r == pendR && (int)pendRoute.size() == L &&
                        std::equal(a, a + L, pendRoute.data())) upd = r;
                    else { upd = -2; break; }
                }
            }
        }
        if (upd == -2) locate(s);
        else {
            if (upd >= 0) updateRoute(upd, s[upd].data());
            for (int r = 0; r < SZ; ++r) ri[r].ptr = s[r].data();
        }
        size_t total = 0;
        for (int r = 0; r < SZ; ++r) total += rm[r].size();
        if (out.capacity() < std::max(lastCount, total)) out.reserve(std::max(lastCount, total));
        for (int r = 0; r < SZ; ++r)
            if (!rm[r].empty()) out.insert(out.end(), rm[r].begin(), rm[r].end());
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) { out.push_back({r, 0, 1, 0, 0, s[r][0], 0}); break; }
            if (out.empty()) out.push_back({-1, 0, 0, 0, 0, 0, 0});
        }
        lastCount = out.size();
    }
    S apply(const S& s, const hsf::Move& m) override {
        for (auto& q : ri) q.ptr = nullptr;
        S t = s;
        if (!sane(s, m)) return t;
        auto& R = t[m[0]];
        int p = m[1], l = m[2], q = m[3];
        if (q < p) std::rotate(R.begin() + q, R.begin() + p, R.begin() + p + l);
        else if (q > p) std::rotate(R.begin() + p, R.begin() + p + l, R.begin() + q + l);
        if (m[4] != 0) std::reverse(R.begin() + q, R.begin() + q + l);
        pendR = m[0];
        pendRoute.assign(R.begin(), R.end());
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        {
            const int r = m[0];
            if ((unsigned)r < (unsigned)nCached && (size_t)r < s.size()) {
                const RI& c = ri[r];
                const auto& R = s[r];
                const int* a = R.data();
                const int L = c.L;
                int p = m[1], l = m[2], q = m[3];
                if (c.ok && c.ptr == a && (int)R.size() == L && l >= 1 && l <= Lmax && p >= 0 &&
                    p + l <= L && q >= 0 && q <= L - l && a[p] == m[5]) {
                    const double* E = ec.data() + c.eb;
                    int e = p + l - 1;
                    int f = a[p], g = a[e];
                    double d = rv[((size_t)c.po + p) * LM1 + l];
                    int A, B; double dab;
                    if (q < p) { A = q > 0 ? a[q - 1] : 0; B = a[q]; dab = E[q]; }
                    else if (q > p) { A = a[q - 1 + l]; B = q < L - l ? a[q + l] : 0; dab = E[q + l]; }
                    else {
                        A = p > 0 ? a[p - 1] : 0; B = e + 1 < L ? a[e + 1] : 0;
                        dab = dst(A, B);
                    }
                    if (Dm) {
                        if (m[4] == 0) d += Dm[(size_t)A * n1 + f] + Dm[(size_t)g * n1 + B] - dab;
                        else d += Dm[(size_t)A * n1 + g] + Dm[(size_t)f * n1 + B] - dab;
                    } else {
                        if (m[4] == 0) d += M.rawDist(A, f) + M.rawDist(g, B) - dab;
                        else d += M.rawDist(A, g) + M.rawDist(f, B) - dab;
                    }
                    return d;
                }
            }
        }
        if (!sane(s, m)) return 0.0;
        const int r = m[0];
        const auto& R = s[r];
        int L = (int)R.size();
        int p = m[1], l = m[2], q = m[3];
        bool rev = m[4] != 0;
        int e = p + l - 1;
        int Lr = L - l;
        const int* a = R.data();
        if (r < nCached) {
            const RI& c = ri[r];
            if (c.ok && c.ptr == a && c.L == L && a[p] == m[5]) {
                const double* E = ec.data() + c.eb;
                int f = a[p], g = a[e];
                int prev = p > 0 ? a[p - 1] : 0;
                int next = e + 1 < L ? a[e + 1] : 0;
                double dpn = dst(prev, next);
                double d = dpn - E[p] - E[e + 1];
                int A, B; double dab;
                if (q < p) { A = q > 0 ? a[q - 1] : 0; B = a[q]; dab = E[q]; }
                else if (q > p) { A = a[q - 1 + l]; B = q < Lr ? a[q + l] : 0; dab = E[q + l]; }
                else { A = prev; B = next; dab = dpn; }
                if (!rev) d += dst(A, f) + dst(g, B) - dab;
                else d += dst(A, g) + dst(f, B) - dab;
                return d;
            }
        }
        int f = R[p], g = R[e];
        bool ok = valid(f) && valid(g);
        int prev = 0, next = 0, A = 0, B = 0;
        if (p > 0) { prev = R[p - 1]; ok = ok && valid(prev); }
        if (e + 1 < L) { next = R[e + 1]; ok = ok && valid(next); }
        if (q > 0) { int i = q - 1; A = R[i < p ? i : i + l]; ok = ok && valid(A); }
        if (q < Lr) { B = R[q < p ? q : q + l]; ok = ok && valid(B); }
        if (ok) {
            double d = dst(prev, next) - dst(prev, f) - dst(g, next);
            if (!rev) d += dst(A, f) + dst(g, B) - dst(A, B);
            else d += dst(A, g) + dst(f, B) - dst(A, B);
            return d;
        }
        build(R, p, l, q, rev, scratch);
        return routeCost(scratch) - routeCost(R);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-4, m[5], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    int l = (int)params.get("max_seg", 3);
    int ur = (int)params.get("use_reversed", 1);
    return std::make_unique<GranularIntraOrOpt>(model, k, l, ur != 0);
}
