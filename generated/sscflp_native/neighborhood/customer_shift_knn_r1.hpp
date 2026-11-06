// COMPONENT: {"name": "customer_shift_knn", "slot": "neighborhood", "params": {"k_nearest": {"type": "int", "range": [2, 40]}}}
class CustomerShiftKnn : public hsf::Neighborhood<Model> {
public:
    CustomerShiftKnn(const Model& md, int k) : M(md) {
        K = std::max(1, std::min(k, std::max(1, M.n)));
        near.resize(M.m);
        std::vector<int> idx(M.n);
        double maxc = 0.0, maxf = 0.0;
        for (int j = 0; j < M.m; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            int kk = std::min(K, M.n);
            std::partial_sort(idx.begin(), idx.begin() + kk, idx.end(),
                              [&](int a, int b) { return cst(a, j) < cst(b, j); });
            near[j].assign(idx.begin(), idx.begin() + kk);
            for (int i = 0; i < M.n; ++i) maxc = std::max(maxc, std::fabs(cst(i, j)));
        }
        for (int i = 0; i < M.n; ++i) maxf = std::max(maxf, std::fabs(M.fixed[i]));
        pen = std::max(1.0, M.penalty) * (maxc + maxf + 1.0);
        owner.assign(M.m, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        buildOwner(s);
        int N = std::min((int)s.size(), M.n);
        for (int j = 0; j < M.m; ++j) {
            int o = owner[j];
            for (int t : near[j]) if (t != o && t < N) out.push_back(mk(j, o, t));
        }
        if (out.empty()) {
            for (int j = 0; j < M.m; ++j)
                for (int t = 0; t < N; ++t)
                    if (t != owner[j]) out.push_back(mk(j, owner[j], t));
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        int j = mv[0], f = mv[1], t = mv[2];
        if (f >= 0 && f < (int)r.size()) {
            auto& v = r[f];
            auto it = std::find(v.begin(), v.end(), j);
            if (it != v.end()) { *it = v.back(); v.pop_back(); }
        }
        if (t >= 0 && t < (int)r.size()) r[t].push_back(j);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        return M.objective(apply(s, mv)) - M.objective(s);
    }

    Move tabu_key(const Move& mv) override { return mk(mv[0], mv[2], mv[1]); }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        int j = mv[0], f = mv[1], t = mv[2];
        double d = M.demand[j];
        double e = cst(t, j);
        if (f >= 0 && f < (int)s.size()) {
            e -= cst(f, j);
            if (s[f].size() == 1) e -= M.fixed[f];
            double lf = sumLoad(s[f]);
            e += pen * (over(lf - d, f) - over(lf, f));
        } else {
            e -= pen * (d + 1.0);
        }
        if (s[t].empty()) e += M.fixed[t];
        double lt = sumLoad(s[t]);
        e += pen * (over(lt + d, t) - over(lt, t));
        return e;
    }

private:
    const Model& M;
    int K;
    double pen;
    std::vector<std::vector<int>> near;
    std::vector<int> owner;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    double over(double l, int i) const { return std::max(0.0, l - M.capacity[i]); }
    double sumLoad(const std::vector<int>& v) const {
        double l = 0.0;
        for (int j : v) l += M.demand[j];
        return l;
    }
    void buildOwner(const Sol& s) {
        std::fill(owner.begin(), owner.end(), -1);
        for (int i = 0; i < (int)s.size(); ++i)
            for (int j : s[i]) if (j >= 0 && j < M.m) owner[j] = i;
    }
    static Move mk(int a, int b, int c) {
        Move mv; mv.fill(0);
        mv[0] = a; mv[1] = b; mv[2] = c;
        return mv;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_nearest", 8.0);
    return std::make_unique<CustomerShiftKnn>(model, k);
}
