// COMPONENT: {"name": "customer_pair_swap_nearby", "slot": "neighborhood", "params": {"k_nearest": {"type": "int", "range": [2, 20]}}}
class CustomerPairSwap : public hsf::Neighborhood<Model> {
public:
    CustomerPairSwap(const Model& md, int k) : M(md) {
        K = std::max(1, std::min(k, std::max(1, M.n)));
        near.resize(M.m);
        inNear.assign((size_t)M.m * std::max(1, M.n), 0);
        std::vector<int> idx(M.n);
        double maxc = 0.0, maxf = 0.0;
        for (int j = 0; j < M.m; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            int kk = std::min(K, M.n);
            std::partial_sort(idx.begin(), idx.begin() + kk, idx.end(),
                              [&](int a, int b) { return cst(a, j) < cst(b, j); });
            near[j].assign(idx.begin(), idx.begin() + kk);
            for (int t : near[j]) inNear[(size_t)j * M.n + t] = 1;
            for (int i = 0; i < M.n; ++i) maxc = std::max(maxc, std::fabs(cst(i, j)));
        }
        for (int i = 0; i < M.n; ++i) maxf = std::max(maxf, std::fabs(M.fixed[i]));
        pen = std::max(1.0, M.penalty) * (maxc + maxf + 1.0);
        owner.assign(M.m, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        std::fill(owner.begin(), owner.end(), -1);
        int N = std::min((int)s.size(), M.n);
        for (int i = 0; i < N; ++i)
            for (int j : s[i]) if (j >= 0 && j < M.m) owner[j] = i;
        for (int j1 = 0; j1 < M.m; ++j1) {
            int i1 = owner[j1];
            if (i1 < 0) continue;
            for (int i2 : near[j1]) {
                if (i2 == i1 || i2 >= N) continue;
                for (int j2 : s[i2]) {
                    if (j2 < 0 || j2 >= M.m || j2 == j1) continue;
                    // evita duplicados: el par también lo genera j2 si i1 está entre sus cercanos
                    if (j2 < j1 && inNear[(size_t)j2 * M.n + i1]) continue;
                    if (j1 < j2) out.push_back(mk(j1, i1, j2, i2));
                    else out.push_back(mk(j2, i2, j1, i1));
                }
            }
        }
        // traslados simples (b = -1) a los centros cercanos: siempre presentes, permiten cambiar
        // cargas y abrir/cerrar centros, cosa que el intercambio puro no puede
        size_t before = out.size();
        for (int j = 0; j < M.m; ++j)
            for (int t : near[j])
                if (t != owner[j] && t < N) out.push_back(mk(j, owner[j], -1, t));
        if (out.size() == before)
            for (int j = 0; j < M.m; ++j)
                for (int t = 0; t < N; ++t)
                    if (t != owner[j]) out.push_back(mk(j, owner[j], -1, t));
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        int a = mv[0], ia = mv[1], b = mv[2], ib = mv[3];
        if (b < 0) {
            if (ia >= 0 && ia < (int)r.size()) {
                auto& v = r[ia];
                auto it = std::find(v.begin(), v.end(), a);
                if (it != v.end()) { *it = v.back(); v.pop_back(); }
            }
            if (ib >= 0 && ib < (int)r.size()) r[ib].push_back(a);
            return r;
        }
        if (ia >= 0 && ia < (int)r.size()) {
            auto it = std::find(r[ia].begin(), r[ia].end(), a);
            if (it != r[ia].end()) *it = b;
        }
        if (ib >= 0 && ib < (int)r.size()) {
            auto it = std::find(r[ib].begin(), r[ib].end(), b);
            if (it != r[ib].end()) *it = a;
        }
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        return M.objective(apply(s, mv)) - M.objective(s);
    }

    Move tabu_key(const Move& mv) override {
        return mk(mv[0], mv[3], mv[2], mv[1]);
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        int a = mv[0], ia = mv[1], b = mv[2], ib = mv[3];
        if (b < 0) {
            double d = M.demand[a];
            double e = cst(ib, a);
            if (ia >= 0) {
                e -= cst(ia, a);
                if (s[ia].size() == 1) e -= M.fixed[ia];
                double l = sumLoad(s[ia]);
                e += pen * (over(l - d, ia) - over(l, ia));
            } else e -= pen * (d + 1.0);
            if (s[ib].empty()) e += M.fixed[ib];
            double l2 = sumLoad(s[ib]);
            e += pen * (over(l2 + d, ib) - over(l2, ib));
            return e;
        }
        double e = cst(ib, a) + cst(ia, b) - cst(ia, a) - cst(ib, b);
        double la = sumLoad(s[ia]), lb = sumLoad(s[ib]);
        double dd = M.demand[b] - M.demand[a];
        e += pen * (over(la + dd, ia) - over(la, ia) + over(lb - dd, ib) - over(lb, ib));
        return e;
    }

private:
    const Model& M;
    int K;
    double pen;
    std::vector<std::vector<int>> near;
    std::vector<char> inNear;
    std::vector<int> owner;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    double over(double l, int i) const { return std::max(0.0, l - M.capacity[i]); }
    double sumLoad(const std::vector<int>& v) const {
        double l = 0.0;
        for (int j : v) l += M.demand[j];
        return l;
    }
    static Move mk(int a, int b, int c, int d) {
        Move mv; mv.fill(0);
        mv[0] = a; mv[1] = b; mv[2] = c; mv[3] = d;
        return mv;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_nearest", 5.0);
    return std::make_unique<CustomerPairSwap>(model, k);
}
