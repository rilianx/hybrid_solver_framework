// COMPONENT: {"name": "swap_customers_between_near_facilities", "slot": "neighborhood", "params": {"k_near": {"type": "int", "range": [2, 50]}, "max_partners": {"type": "int", "range": [5, 200]}}}
class SwapNearFacilities : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SwapNearFacilities(const Model& model, int k, int p) : M(model) {
        nf = (int)M.capacity.size();
        nc = (int)M.demand.size();
        K = std::max(1, std::min(k, nf));
        P = std::max(1, p);
        near.assign(nc, {});
        nearMask.assign((size_t)nc * nf, 0);
        std::vector<int> idx(nf);
        for (int j = 0; j < nc; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            std::stable_sort(idx.begin(), idx.end(),
                             [&](int a, int b) { return M.cost[a][j] < M.cost[b][j]; });
            near[j].assign(idx.begin(), idx.begin() + K);
            for (int f : near[j]) nearMask[(size_t)j * nf + f] = 1;
        }
        bucket.assign(nf, {});
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const auto& a = s[0];
        for (auto& b : bucket) b.clear();
        for (int j = 0; j < nc; ++j)
            if (a[j] >= 0) bucket[a[j]].push_back(j);
        for (int j1 = 0; j1 < nc; ++j1) {
            int f1 = a[j1];
            if (f1 < 0) continue;
            for (int f : near[j1]) {
                if (f == f1) continue;
                const auto& B = bucket[f];
                int bs = (int)B.size();
                if (bs == 0) continue;
                int take = std::min(bs, P);
                int off = (bs > P) ? (int)(((long long)j1 * 7919LL) % bs) : 0;
                for (int t = 0; t < take; ++t) {
                    int j2 = B[(off + t) % bs];
                    // canónico: si el par también se genera desde j2, sólo una vez
                    if (j2 < j1 && nearMask[(size_t)j2 * nf + f1]) continue;
                    out.push_back(mk(j1, j2));
                }
            }
        }
        if (out.empty()) {
            int lim = 0;
            for (int j1 = 0; j1 < nc && lim < 2000; ++j1)
                for (int j2 = j1 + 1; j2 < nc && lim < 2000; ++j2)
                    if (a[j1] != a[j2]) { out.push_back(mk(j1, j2)); ++lim; }
            if (out.empty() && nc > 0) out.push_back(mk(0, 0));
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        std::swap(r[0][mv[0]], r[0][mv[1]]);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        int j1 = mv[0], j2 = mv[1];
        std::swap(work[0][j1], work[0][j2]);
        double v = M.objective(work);
        std::swap(work[0][j1], work[0][j2]);
        return v - base;
    }

    Move tabu_key(const Move& mv) override {
        return mk(std::min(mv[0], mv[1]), std::max(mv[0], mv[1]));
    }

private:
    const Model& M;
    int nf = 0, nc = 0, K = 1, P = 1;
    std::vector<std::vector<int>> near, bucket;
    std::vector<char> nearMask;
    Sol work;
    double base = 0.0;
    bool valid = false;

    static Move mk(int a, int b) {
        Move m{};
        m[0] = a; m[1] = b;
        return m;
    }
    void sync(const Sol& s) {
        if (!valid || work != s) {
            work = s;
            base = M.objective(work);
            valid = true;
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_near", 8);
    int p = (int)params.get("max_partners", 40);
    return std::make_unique<SwapNearFacilities>(model, k, p);
}
