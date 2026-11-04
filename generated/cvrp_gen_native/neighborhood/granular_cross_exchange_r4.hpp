// COMPONENT: {"name": "granular_cross_exchange", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [1, 4]}}}
class GranularCrossExchange : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    struct Node { double pre; int lv; int nv; int nvp; int pad; };
    struct RInfo { int base; int L; int off; const int* ptr; double tot; double pn; };
    const Model& M;
    int K, L;
    std::vector<int> nb, rof, pof;
    // caché por solución
    std::vector<int> flat;
    std::vector<Node> nd;
    std::vector<RInfo> ri;
    int nCached = 0;
    size_t lastCount = 0;
    const double* Dm = nullptr;
    size_t n1 = 1;
    double capE = 0.0, cap = 0.0, pnl = 0.0;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool cachedRoute(const std::vector<int>& R, int r) {
        if (r < 0 || r >= nCached) return false;
        RInfo& q = ri[r];
        if (q.L != (int)R.size()) return false;
        const int* d = R.data();
        if (d && q.ptr == d) return true;
        if (!std::equal(R.begin(), R.end(), flat.begin() + q.off)) return false;
        q.ptr = d;
        return true;
    }
    static inline void segFL(const Node* N, int p, int e, int& f, int& l) {
        if (N[p].nvp < e) { f = N[p].nv; l = N[e].lv; }
        else { f = 0; l = 0; }
    }
    bool valid(int c) const { return c >= 1 && c <= M.n; }
    void locate(const S& s) {
        std::fill(rof.begin(), rof.end(), -1);
        const int n = M.n;
        const double* dem = M.demand.data();
        int SZ = (int)s.size();
        ri.resize(SZ);
        int tot = 0;
        for (int r = 0; r < SZ; ++r) { ri[r].off = tot; tot += (int)s[r].size(); }
        flat.resize(tot);
        nd.resize((size_t)tot + SZ);
        int* RO = rof.data();
        int* PO = pof.data();
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            const int* a = R.data();
            int Ln = (int)R.size();
            int o = ri[r].off;
            int ao = o + r;
            if (Ln) std::copy(R.begin(), R.end(), flat.begin() + o);
            Node* N = nd.data() + ao;
            double ld = 0.0; int last = 0;
            for (int p = 0; p < Ln; ++p) {
                N[p].pre = ld; N[p].lv = last;
                int c = a[p];
                if (c >= 1 && c <= n) {
                    ld += dem[c]; last = c;
                    if (RO[c] < 0) { RO[c] = r; PO[c] = p; }
                }
            }
            N[Ln].pre = ld; N[Ln].lv = last;
            int nx = 0, np = Ln;
            N[Ln].nv = 0; N[Ln].nvp = Ln;
            for (int p = Ln - 1; p >= 0; --p) {
                int c = a[p];
                if (c >= 1 && c <= n) { nx = c; np = p; }
                N[p].nv = nx; N[p].nvp = np;
            }
            RInfo& q = ri[r];
            q.base = ao; q.L = Ln; q.ptr = a; q.tot = ld; q.pn = pen(ld);
        }
        nCached = SZ;
    }
    // m = {r1, p1, l1, r2, p2, l2, u}; r2 >= |s| significa ruta nueva (vacía)
    void build(const S& s, const hsf::Move& m, std::vector<int>& a, std::vector<int>& b) const {
        static const std::vector<int> empty;
        const auto& A = s[m[0]];
        const auto& B = m[3] < (int)s.size() ? s[m[3]] : empty;
        int p1 = m[1], l1 = m[2], p2 = m[4], l2 = m[5];
        a.assign(A.begin(), A.begin() + p1);
        a.insert(a.end(), B.begin() + p2, B.begin() + p2 + l2);
        a.insert(a.end(), A.begin() + p1 + l1, A.end());
        b.assign(B.begin(), B.begin() + p2);
        b.insert(b.end(), A.begin() + p1, A.begin() + p1 + l1);
        b.insert(b.end(), B.begin() + p2 + l2, B.end());
    }
public:
    GranularCrossExchange(const Model& m, int k, int l) : M(m), L(std::max(1, l)) {
        int n = M.n;
        n1 = (size_t)n + 1;
        Dm = M.useMatrix ? M.D.data() : nullptr;
        cap = M.capacity; capE = M.capacity + 1e-9; pnl = M.penalty;
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
        locate(s);
        if (out.capacity() < lastCount) out.reserve(lastCount);
        int SZ = (int)s.size();
        const int n = M.n;
        const int* NB = nb.data();
        const int* RO = rof.data();
        const int* PO = pof.data();
        const int Lm = L;
        for (int r = 0; r < SZ; ++r) {
            const int* a = s[r].data();
            int len1 = (int)s[r].size();
            for (int p1 = 0; p1 < len1; ++p1) {
                int u = a[p1];
                if (u < 1 || u > n || RO[u] != r || PO[u] != p1) continue;
                const int* nu = NB + (size_t)u * K;
                int maxl1 = std::min(Lm, len1 - p1);
                for (int t = 0; t < K; ++t) {
                    int v = nu[t];
                    int r2 = RO[v];
                    if (r2 < 0 || r2 == r) continue;
                    int p2 = PO[v] + 1;
                    int len2 = (int)s[r2].size();
                    int maxl2 = std::min(Lm, len2 - p2);
                    for (int l1 = 1; l1 <= maxl1; ++l1)
                        for (int l2 = 0; l2 <= maxl2; ++l2)
                            out.push_back({r, p1, l1, r2, p2, l2, u});
                }
            }
        }
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) { out.push_back({r, 0, 1, SZ, 0, 0, s[r][0]}); break; }
        }
        lastCount = out.size();
    }
    S apply(const S& s, const hsf::Move& m) override {
        for (auto& q : ri) q.ptr = nullptr;
        S t = s;
        std::vector<int> a, b;
        build(s, m, a, b);
        int r1 = m[0], r2 = m[3];
        t[r1] = std::move(a);
        if (r2 >= (int)t.size()) { t.push_back(std::move(b)); r2 = (int)t.size() - 1; }
        else t[r2] = std::move(b);
        int hi = std::max(r1, r2), lo = std::min(r1, r2);
        if (t[hi].empty()) t.erase(t.begin() + hi);
        if (t[lo].empty()) t.erase(t.begin() + lo);
        return t;
    }
    inline double pen(double load) const {
        return load > capE ? pnl * (load - cap) : 0.0;
    }
    // costo de enlace: depósito -> partes no vacías (first,last) -> depósito; 0 = parte vacía
    inline double link(int f0, int l0, int f1, int l1, int f2, int l2) const {
        double d = 0.0; int prev = 0; bool any = false;
        if (f0) { d += dst(prev, f0); prev = l0; any = true; }
        if (f1) { d += dst(prev, f1); prev = l1; any = true; }
        if (f2) { d += dst(prev, f2); prev = l2; any = true; }
        if (any) d += dst(prev, 0);
        return d;
    }
    double delta(const S& s, const hsf::Move& m) override {
        int r1 = m[0], p1 = m[1], l1 = m[2], r2 = m[3], p2 = m[4], l2 = m[5];
        const auto& A = s[r1];
        int SZ = (int)s.size();
        bool newB = r2 >= SZ;
        if (cachedRoute(A, r1) && (newB || cachedRoute(s[r2], r2))) {
            int af[3], al[3], bf[3] = {0, 0, 0}, bl[3] = {0, 0, 0};
            const RInfo& QA = ri[r1];
            const Node* NA = nd.data() + QA.base;
            int lenA = QA.L;
            int e1 = p1 + l1;
            segFL(NA, 0, p1, af[0], al[0]);
            segFL(NA, p1, e1, af[1], al[1]);
            segFL(NA, e1, lenA, af[2], al[2]);
            double loadA = QA.tot;
            double segA = NA[e1].pre - NA[p1].pre;
            double loadB = 0.0, segB = 0.0, pnB;
            if (!newB) {
                const RInfo& QB = ri[r2];
                const Node* NBn = nd.data() + QB.base;
                int lenB = QB.L;
                int e2 = p2 + l2;
                segFL(NBn, 0, p2, bf[0], bl[0]);
                segFL(NBn, p2, e2, bf[1], bl[1]);
                segFL(NBn, e2, lenB, bf[2], bl[2]);
                loadB = QB.tot;
                segB = NBn[e2].pre - NBn[p2].pre;
                pnB = QB.pn;
            } else {
                pnB = pen(0.0);
            }
            double oldL = link(af[0], al[0], af[1], al[1], af[2], al[2])
                        + link(bf[0], bl[0], bf[1], bl[1], bf[2], bl[2]);
            double newL = link(af[0], al[0], bf[1], bl[1], af[2], al[2])
                        + link(bf[0], bl[0], af[1], al[1], bf[2], bl[2]);
            double la = loadA - segA + segB;
            double lb = loadB - segB + segA;
            return (newL - oldL) + pen(la) + pen(lb) - QA.pn - pnB;
        }
        const int n = M.n;
        const double* dem = M.demand.data();
        const int* a = A.data();
        int lenA = (int)A.size();
        int af[3] = {0, 0, 0}, al[3] = {0, 0, 0};
        double loadA = 0.0, segA = 0.0;
        {
            int e1 = p1 + l1;
            for (int i = 0; i < p1; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; if (!af[0]) af[0] = c; al[0] = c;
            }
            for (int i = p1; i < e1; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; segA += dem[c]; if (!af[1]) af[1] = c; al[1] = c;
            }
            for (int i = e1; i < lenA; ++i) {
                int c = a[i];
                if (c < 1 || c > n) continue;
                loadA += dem[c]; if (!af[2]) af[2] = c; al[2] = c;
            }
        }
        int bf[3] = {0, 0, 0}, bl[3] = {0, 0, 0};
        double loadB = 0.0, segB = 0.0;
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            const int* b = B.data();
            int lenB = (int)B.size();
            int e2 = p2 + l2;
            for (int i = 0; i < p2; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; if (!bf[0]) bf[0] = c; bl[0] = c;
            }
            for (int i = p2; i < e2; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; segB += dem[c]; if (!bf[1]) bf[1] = c; bl[1] = c;
            }
            for (int i = e2; i < lenB; ++i) {
                int c = b[i];
                if (c < 1 || c > n) continue;
                loadB += dem[c]; if (!bf[2]) bf[2] = c; bl[2] = c;
            }
        }
        double oldL = link(af[0], al[0], af[1], al[1], af[2], al[2])
                    + link(bf[0], bl[0], bf[1], bl[1], bf[2], bl[2]);
        double newL = link(af[0], al[0], bf[1], bl[1], af[2], al[2])
                    + link(bf[0], bl[0], af[1], al[1], bf[2], bl[2]);
        double la = loadA - segA + segB;
        double lb = loadB - segB + segA;
        return (newL - oldL) + pen(la) + pen(lb) - pen(loadA) - pen(loadB);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-3, m[6], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 8);
    int l = (int)params.get("max_seg", 3);
    return std::make_unique<GranularCrossExchange>(model, k, l);
}
