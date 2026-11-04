// COMPONENT: {"name": "route_dissolve_reinsert", "slot": "neighborhood", "params": {"k": {"type": "int", "range": [3, 30]}, "max_len": {"type": "int", "range": [1, 50]}}}
class RouteDissolveReinsert : public hsf::Neighborhood<Model> {
    using S = Model::Solution;
    const Model& M;
    int K, maxLen;
    std::vector<int> nb, rof, pof;
    const double* Dm = nullptr;
    size_t n1 = 1;
    // memoria de trabajo
    std::vector<std::vector<int>> wk;
    std::vector<double> wload;
    std::vector<int> slotOf, touched, stamp, order, extra, cands;
    std::vector<int> emptyR;
    int curStamp = 0;
    inline double dst(int i, int j) const { return Dm ? Dm[(size_t)i * n1 + j] : M.rawDist(i, j); }
    inline bool valid(int c) const { return c >= 1 && c <= M.n; }
    inline double pen(double ld) const { return ld > M.capacity + 1e-9 ? M.penalty * (ld - M.capacity) : 0.0; }
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
    double loadOf(const std::vector<int>& R) const {
        double ld = 0.0;
        for (int c : R) if (valid(c)) ld += M.demand[c];
        return ld;
    }
    double routeCost(const std::vector<int>& R) const {
        double d = 0.0, ld = 0.0; int prev = 0; bool any = false;
        for (int c : R) {
            if (!valid(c)) continue;
            d += dst(prev, c); ld += M.demand[c]; prev = c; any = true;
        }
        if (any) d += dst(prev, 0);
        return d + pen(ld);
    }
    int openSlot(const S& s, int idx) {
        if (slotOf[idx] >= 0) return slotOf[idx];
        int sl = (int)touched.size();
        touched.push_back(idx);
        if ((int)wk.size() <= sl) { wk.emplace_back(); wload.push_back(0.0); }
        if (idx < (int)s.size()) { wk[sl] = s[idx]; wload[sl] = loadOf(s[idx]); }
        else { wk[sl].clear(); wload[sl] = 0.0; }
        slotOf[idx] = sl;
        return sl;
    }
    // simulación determinista; deja el resultado en wk/touched y devuelve el delta exacto
    double simulate(const S& s, int r) {
        locate(s);
        int SZ = (int)s.size();
        slotOf.assign(SZ + 1, -1);
        touched.clear();
        if ((int)stamp.size() < SZ + 1) stamp.assign(SZ + 1, 0);
        const auto& RR = s[r];
        order.clear(); extra.clear();
        for (int c : RR) { if (valid(c)) order.push_back(c); else extra.push_back(c); }
        const double* dem = M.demand.data();
        std::sort(order.begin(), order.end(), [&](int a, int b) {
            if (dem[a] != dem[b]) return dem[a] > dem[b];
            return a < b;
        });
        for (int c : order) {
            double dc = dem[c];
            ++curStamp;
            cands.clear();
            for (int t = 0; t < K; ++t) {
                int w = nb[(size_t)c * K + t];
                int ro = rof[w];
                if (ro < 0 || ro == r) continue;
                if (stamp[ro] != curStamp) { stamp[ro] = curStamp; cands.push_back(ro); }
            }
            cands.push_back(SZ);
            double best = std::numeric_limits<double>::infinity();
            int bi = SZ, bp = 0;
            for (int idx : cands) {
                int sl = slotOf[idx];
                const std::vector<int>& R = sl >= 0 ? wk[sl] : (idx < SZ ? s[idx] : emptyR);
                double ld = sl >= 0 ? wload[sl] : (idx < SZ ? loadOf(R) : 0.0);
                double pinc = pen(ld + dc) - pen(ld);
                int L = (int)R.size();
                for (int k = 0; k <= L; ++k) {
                    int a = 0, b = 0;
                    if (k > 0) { a = R[k - 1]; if (!valid(a)) continue; }
                    if (k < L) { b = R[k]; if (!valid(b)) continue; }
                    double cst = dst(a, c) + dst(c, b) - dst(a, b) + pinc;
                    if (cst < best) { best = cst; bi = idx; bp = k; }
                }
            }
            int sl = openSlot(s, bi);
            wk[sl].insert(wk[sl].begin() + bp, c);
            wload[sl] += dc;
        }
        if (!extra.empty()) {
            int sl = openSlot(s, SZ);
            wk[sl].insert(wk[sl].end(), extra.begin(), extra.end());
        }
        double d = -routeCost(RR);
        for (int i = 0; i < (int)touched.size(); ++i) {
            int idx = touched[i];
            d += routeCost(wk[i]);
            if (idx < SZ) d -= routeCost(s[idx]);
        }
        return d;
    }
public:
    RouteDissolveReinsert(const Model& m, int k, int ml) : M(m), maxLen(std::max(1, ml)) {
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
        int SZ = (int)s.size();
        if (SZ >= 2) {
            for (int r = 0; r < SZ; ++r) {
                int len = (int)s[r].size();
                if (len >= 1 && len <= maxLen) out.push_back({r, s[r][0], 0, 0, 0, 0, 0});
            }
        }
        if (out.empty() && SZ >= 1) {
            int best = 0;
            for (int r = 1; r < SZ; ++r)
                if (!s[r].empty() && (s[best].empty() || s[r].size() < s[best].size())) best = r;
            out.push_back({best, s[best].empty() ? 0 : s[best][0], 0, 0, 0, 0, 0});
        }
        if (out.empty()) out.push_back({-1, 0, 0, 0, 0, 0, 0});
    }
    S apply(const S& s, const hsf::Move& m) override {
        int r = m[0];
        if (r < 0 || r >= (int)s.size()) return s;
        simulate(s, r);
        int SZ = (int)s.size();
        S t = s;
        for (int i = 0; i < (int)touched.size(); ++i) {
            int idx = touched[i];
            if (idx < SZ) t[idx] = wk[i];
            else if (!wk[i].empty()) t.push_back(wk[i]);
        }
        t.erase(t.begin() + r);
        return t;
    }
    double delta(const S& s, const hsf::Move& m) override {
        int r = m[0];
        if (r < 0 || r >= (int)s.size()) return 0.0;
        return simulate(s, r);
    }
    hsf::Move tabu_key(const hsf::Move& m) override { return {-6, m[1], 0, 0, 0, 0, 0}; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k", 10);
    int ml = (int)params.get("max_len", 15);
    return std::make_unique<RouteDissolveReinsert>(model, k, ml);
}
