// COMPONENT: {"name": "granular_swap_star", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}}}
class GranularSwapStar : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K;
    std::vector<int> nb, nbs, rof, pof;
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
    void buildMod(const std::vector<int>& R, int skip, int ins, int q, std::vector<int>& out) const {
        out.clear();
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
        for (int r1 = 0; r1 < SZ; ++r1) {
            const auto& A = s[r1];
            int L1 = (int)A.size();
            for (int p1 = 0; p1 < L1; ++p1) {
                int u = A[p1];
                if (!valid(u) || rof[u] != r1 || pof[u] != p1) continue;
                for (int t = 0; t < K; ++t) {
                    int v = nb[(size_t)u * K + t];
                    int r2 = rof[v];
                    if (r2 < 0 || r2 == r1) continue;
                    if (r1 > r2 && std::binary_search(nbs.begin() + (size_t)v * K,
                                                      nbs.begin() + (size_t)(v + 1) * K, u)) continue;
                    int p2 = pof[v];
                    int q1 = bestIns(s[r2], p2, u);
                    int q2 = bestIns(A, p1, v);
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
        S t = s;
        if (!sane(s, m)) return t;
        const auto& A = s[m[0]];
        const auto& B = s[m[2]];
        int u = A[m[1]], v = B[m[3]];
        std::vector<int> na, nb2;
        buildMod(A, m[1], v, m[5], na);
        buildMod(B, m[3], u, m[4], nb2);
        t[m[0]] = std::move(na);
        t[m[2]] = std::move(nb2);
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        if (!sane(s, m)) return 0.0;
        const auto& A = s[m[0]];
        const auto& B = s[m[2]];
        int u = A[m[1]], v = B[m[3]];
        return costMod(A, m[1], v, m[5]) + costMod(B, m[3], u, m[4])
             - costMod(A, -1, 0, -1) - costMod(B, -1, 0, -1);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-5, m[6], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    return std::make_unique<GranularSwapStar>(model, k);
}
