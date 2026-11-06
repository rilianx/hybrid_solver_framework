// COMPONENT: {"name": "pairwise_customer_exchange", "slot": "neighborhood", "params": {"k_near": {"type": "int", "range": [2, 40]}, "prune": {"type": "cat", "values": ["cost", "none"]}}}
class PairwiseCustomerExchange : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    PairwiseCustomerExchange(const Model& md, int k, bool prune) : M(md), pruneCost(prune) {
        int n = M.n, m = M.m;
        K = std::max(1, std::min(k, n));
        nearL.assign((size_t)m * K, 0);
        isNear.assign((size_t)m * n, 0);
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
            for (int t = 0; t < K; ++t) {
                nearL[(size_t)j * K + t] = idx[t];
                isNear[(size_t)j * n + idx[t]] = 1;
            }
        }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        sync(s);
        const std::vector<int>& a = s[0];
        int n = M.n;
        for (int j1 = 0; j1 < M.m; ++j1) {
            int f1 = a[j1];
            if (f1 < 0) continue;
            const int* nl = &nearL[(size_t)j1 * K];
            for (int t = 0; t < K; ++t) {
                int f2 = nl[t];
                if (f2 == f1) continue;
                for (int j2 : custs[f2]) {
                    bool sym = isNear[(size_t)j2 * n + f1] != 0;
                    if (sym && j2 < j1) continue;  // lo emite j2
                    if (pruneCost && cst(f2, j1) + cst(f1, j2) >= cst(f1, j1) + cst(f2, j2)) continue;
                    Move mv{}; mv[0] = j1; mv[1] = j2; mv[2] = f1; mv[3] = f2;
                    out.push_back(mv);
                }
            }
        }
        if (out.empty()) {
            // respaldo: cualquier par con centros distintos (o un no-op)
            for (int j1 = 0; j1 < M.m && out.empty(); ++j1)
                for (int j2 = j1 + 1; j2 < M.m; ++j2)
                    if (a[j1] >= 0 && a[j2] >= 0 && a[j1] != a[j2]) {
                        Move mv{}; mv[0] = j1; mv[1] = j2; mv[2] = a[j1]; mv[3] = a[j2];
                        out.push_back(mv); break;
                    }
            if (out.empty() && M.m > 0) { Move mv{}; mv[2] = a[0]; mv[3] = a[0]; out.push_back(mv); }
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::swap(r[0][mv[0]], r[0][mv[1]]);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        tmp = s;
        std::swap(tmp[0][mv[0]], tmp[0][mv[1]]);
        return M.objective(tmp) - obj;
    }

    Move tabu_key(const Move& mv) override {
        Move k{}; k[0] = mv[0]; k[1] = mv[1]; k[2] = mv[3]; k[3] = mv[2];
        return k;
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        sync(s);
        int j1 = mv[0], j2 = mv[1];
        int f1 = ca[j1], f2 = ca[j2];
        if (f1 == f2 || f1 < 0 || f2 < 0) return 0.0;
        double d1 = M.demand[j1], d2 = M.demand[j2];
        double est = cst(f2, j1) + cst(f1, j2) - cst(f1, j1) - cst(f2, j2);
        est += W * (exc(f1, load[f1] - d1 + d2) - exc(f1, load[f1]));
        est += W * (exc(f2, load[f2] - d2 + d1) - exc(f2, load[f2]));
        return est;
    }

private:
    const Model& M;
    bool pruneCost = true;
    int K = 1;
    double W = 1.0;
    std::vector<int> nearL;
    std::vector<char> isNear;
    std::vector<int> ca;
    std::vector<double> load;
    std::vector<std::vector<int>> custs;
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
        custs.resize(M.n);
        for (auto& v : custs) v.clear();
        for (int j = 0; j < M.m; ++j) {
            int f = a[j];
            if (f >= 0 && f < M.n) { load[f] += M.demand[j]; custs[f].push_back(j); }
        }
        obj = M.objective(s);
        valid = true;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_near", 8);
    bool prune = params.text("prune", "cost") == "cost";
    return std::make_unique<PairwiseCustomerExchange>(model, k, prune);
}
