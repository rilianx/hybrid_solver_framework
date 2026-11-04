// COMPONENT: {"name": "granular_intra_or_opt", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_seg": {"type": "int", "range": [2, 5]}, "use_reversed": {"type": "int", "range": [0, 1]}}}
class GranularIntraOrOpt : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K, Lmax;
    bool useRev;
    std::vector<int> nb, rof, pof;
    std::vector<int> scratch;
    const double* Dm = nullptr;
    size_t n1 = 1;
    size_t lastCount = 0;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    void locate(const S& s) {
        std::fill(rof.begin(), rof.end(), -1);
        for (int r = 0; r < (int)s.size(); ++r) {
            const auto& R = s[r];
            for (int p = 0; p < (int)R.size(); ++p) {
                int c = R[p];
                if (valid(c) && rof[c] < 0) { rof[c] = r; pof[c] = p; }
            }
        }
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
        rof.assign(n + 1, -1); pof.assign(n + 1, -1);
    }
    void moves(const S& s, std::vector<hsf::Move>& out) override {
        locate(s);
        if (out.capacity() < lastCount) out.reserve(lastCount);
        int SZ = (int)s.size();
        for (int r = 0; r < SZ; ++r) {
            const auto& R = s[r];
            int L = (int)R.size();
            if (L < 3) continue;
            for (int p = 0; p < L; ++p) {
                int f = R[p];
                if (!valid(f) || rof[f] != r || pof[f] != p) continue;
                int lmax = std::min(Lmax, L - p);
                for (int l = 2; l <= lmax; ++l) {
                    int e = p + l - 1;
                    int g = R[e];
                    auto push = [&](int q, int rev) {
                        if (q == p && !rev) return;
                        out.push_back({r, p, l, q, rev, f, 0});
                    };
                    for (int t = 0; t < K; ++t) {
                        int v = nb[(size_t)f * K + t];
                        if (rof[v] != r) continue;
                        int pv = pof[v];
                        if (pv >= p && pv <= e) continue;
                        int pr = pv < p ? pv : pv - l;
                        push(pr + 1, 0);
                        if (useRev) push(pr, 1);
                    }
                    if (valid(g)) {
                        for (int t = 0; t < K; ++t) {
                            int v = nb[(size_t)g * K + t];
                            if (rof[v] != r) continue;
                            int pv = pof[v];
                            if (pv >= p && pv <= e) continue;
                            int pr = pv < p ? pv : pv - l;
                            push(pr, 0);
                            if (useRev) push(pr + 1, 1);
                        }
                    }
                }
            }
        }
        if (out.empty()) {
            for (int r = 0; r < SZ; ++r)
                if (!s[r].empty()) { out.push_back({r, 0, 1, 0, 0, s[r][0], 0}); break; }
            if (out.empty()) out.push_back({-1, 0, 0, 0, 0, 0, 0});
        }
        lastCount = out.size();
    }
    S apply(const S& s, const hsf::Move& m) override {
        S t = s;
        if (!sane(s, m)) return t;
        std::vector<int> nr;
        build(s[m[0]], m[1], m[2], m[3], m[4] != 0, nr);
        t[m[0]] = std::move(nr);
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        if (!sane(s, m)) return 0.0;
        const auto& R = s[m[0]];
        int L = (int)R.size();
        int p = m[1], l = m[2], q = m[3];
        bool rev = m[4] != 0;
        int e = p + l - 1;
        int Lr = L - l;
        int f = R[p], g = R[e];
        bool ok = valid(f) && valid(g);
        int prev = 0, next = 0, a = 0, b = 0;
        if (p > 0) { prev = R[p - 1]; ok = ok && valid(prev); }
        if (e + 1 < L) { next = R[e + 1]; ok = ok && valid(next); }
        if (q > 0) { int i = q - 1; a = R[i < p ? i : i + l]; ok = ok && valid(a); }
        if (q < Lr) { b = R[q < p ? q : q + l]; ok = ok && valid(b); }
        if (ok) {
            double d = dst(prev, next) - dst(prev, f) - dst(g, next);
            if (!rev) d += dst(a, f) + dst(g, b) - dst(a, b);
            else d += dst(a, g) + dst(f, b) - dst(a, b);
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
