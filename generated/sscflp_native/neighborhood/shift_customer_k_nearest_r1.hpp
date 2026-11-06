// COMPONENT: {"name": "shift_customer_k_nearest", "slot": "neighborhood", "params": {"k_near": {"type": "int", "range": [2, 60]}}}
class ShiftCustomerKNearest : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    ShiftCustomerKNearest(const Model& md, int k) : M(md) {
        int n = M.n, m = M.m;
        K = std::max(1, std::min(k, n));
        nearL.assign((size_t)m * K, 0);
        std::vector<int> idx(n);
        double maxF = 0, maxC = 0;
        for (int i = 0; i < n; ++i) maxF = std::max(maxF, M.fixed[i]);
        for (double v : M.cost) maxC = std::max(maxC, v);
        W = M.penalty * (1.0 + maxF + maxC);
        for (int j = 0; j < m; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(), [&](int a, int b) {
                double ca = cst(a, j), cb = cst(b, j);
                return ca < cb || (ca == cb && a < b);
            });
            for (int t = 0; t < K; ++t) nearL[(size_t)j * K + t] = idx[t];
        }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const std::vector<int>& a = s[0];
        for (int j = 0; j < M.m; ++j) {
            int f = a[j];
            const int* nl = &nearL[(size_t)j * K];
            for (int t = 0; t < K; ++t) {
                int i = nl[t];
                if (i == f) continue;
                Move mv{}; mv[0] = j; mv[1] = i; mv[2] = f;
                out.push_back(mv);
            }
        }
        if (out.empty() && M.m > 0) { Move mv{}; mv[0] = 0; mv[1] = a[0]; mv[2] = a[0]; out.push_back(mv); }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        r[0][mv[0]] = mv[1];
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        tmp = s;
        tmp[0][mv[0]] = mv[1];
        return M.objective(tmp) - obj;
    }

    Move tabu_key(const Move& mv) override {
        Move k{}; k[0] = mv[0]; k[1] = mv[2]; k[2] = mv[1];
        return k;
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        sync(s);
        int j = mv[0], i = mv[1], f = ca[j];
        if (i == f) return 0.0;
        double d = M.demand[j], est = cst(i, j);
        if (cnt[i] == 0) est += M.fixed[i];
        est += W * (exc(i, load[i] + d) - exc(i, load[i]));
        if (f >= 0) {
            est -= cst(f, j);
            if (cnt[f] == 1) est -= M.fixed[f];
            est += W * (exc(f, load[f] - d) - exc(f, load[f]));
        } else {
            est -= W * (1.0 + d);
        }
        return est;
    }

private:
    const Model& M;
    int K = 1;
    double W = 1.0;
    std::vector<int> nearL;
    std::vector<int> ca, cnt;
    std::vector<double> load;
    double obj = 0;
    bool valid = false;
    Sol tmp;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    double exc(int i, double l) const { return std::max(0.0, l - M.capacity[i]); }

    void sync(const Sol& s) {
        const std::vector<int>& a = s[0];
        if (valid && a == ca) return;
        ca = a;
        load.assign(M.n, 0.0);
        cnt.assign(M.n, 0);
        for (int j = 0; j < M.m; ++j) {
            int f = a[j];
            if (f >= 0 && f < M.n) { load[f] += M.demand[j]; cnt[f]++; }
        }
        obj = M.objective(s);
        valid = true;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_near", 10);
    return std::make_unique<ShiftCustomerKNearest>(model, k);
}
