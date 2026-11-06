// COMPONENT: {"name": "shift_customer_near_or_open", "slot": "neighborhood", "params": {"k_near": {"type": "int", "range": [3, 100]}}}
class ShiftNearOrOpen : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    ShiftNearOrOpen(const Model& model, int k) : M(model) {
        nf = (int)M.capacity.size();
        nc = (int)M.demand.size();
        K = std::max(1, std::min(k, nf));
        near.assign(nc, {});
        std::vector<int> idx(nf);
        for (int j = 0; j < nc; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            std::stable_sort(idx.begin(), idx.end(),
                             [&](int a, int b) { return M.cost[a][j] < M.cost[b][j]; });
            near[j].assign(idx.begin(), idx.begin() + K);
        }
        mark.assign(nf, 0);
        cnt.assign(nf, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const auto& a = s[0];
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j = 0; j < nc; ++j)
            if (a[j] >= 0) cnt[a[j]]++;
        openList.clear();
        for (int f = 0; f < nf; ++f)
            if (cnt[f] > 0) openList.push_back(f);
        for (int j = 0; j < nc; ++j) {
            int cur = a[j];
            ++stamp;
            for (int f : near[j]) {
                if (f == cur) continue;
                mark[f] = stamp;
                out.push_back(mk(j, f, cur));
            }
            for (int f : openList) {
                if (f == cur || mark[f] == stamp) continue;
                mark[f] = stamp;
                out.push_back(mk(j, f, cur));
            }
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        r[0][mv[0]] = mv[1];
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        int j = mv[0];
        int old = work[0][j];
        work[0][j] = mv[1];
        double v = M.objective(work);
        work[0][j] = old;
        return v - base;
    }

    Move tabu_key(const Move& mv) override { return mk(mv[0], mv[2], mv[1]); }

private:
    const Model& M;
    int nf = 0, nc = 0, K = 1;
    std::vector<std::vector<int>> near;
    std::vector<int> mark, cnt, openList;
    int stamp = 0;
    Sol work;
    double base = 0.0;
    bool valid = false;

    static Move mk(int a, int b, int c) {
        Move m{};
        m[0] = a; m[1] = b; m[2] = c;
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
    int k = (int)params.get("k_near", 15);
    return std::make_unique<ShiftNearOrOpen>(model, k);
}
