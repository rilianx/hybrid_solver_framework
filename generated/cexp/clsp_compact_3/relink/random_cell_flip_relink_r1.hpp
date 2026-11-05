// COMPONENT: {"name": "random_cell_flip_relink", "slot": "relink", "params": {"max_flips": {"type": "int", "range": [1, 4]}}}
class RandomCellFlipRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    int maxFlips;
    std::vector<std::pair<int,int>> diff;
public:
    RandomCellFlipRelink(const Model& model, int mf) : m(model), maxFlips(std::max(1, mf)) {}

    int distance(const Sol& a, const Sol& b) override {
        int c = 0;
        for (size_t i = 0; i < a.size(); ++i) {
            const auto& ra = a[i]; const auto& rb = b[i];
            for (size_t t = 0; t < ra.size(); ++t) c += (ra[t] != rb[t]);
        }
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        diff.clear();
        for (size_t i = 0; i < cur.size(); ++i)
            for (size_t t = 0; t < cur[i].size(); ++t)
                if (cur[i][t] != guide[i][t]) diff.emplace_back((int)i, (int)t);
        Sol r = cur;
        if (diff.empty()) return r;
        int sz = (int)diff.size();
        int k = 1 + rng.below(std::min(maxFlips, sz));
        for (int j = 0; j < k; ++j) {
            int p = j + rng.below(sz - j);
            std::swap(diff[j], diff[p]);
            r[diff[j].first][diff[j].second] = guide[diff[j].first][diff[j].second];
        }
        return r;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int mf = (int)params.get("max_flips", 1.0);
    return std::make_unique<RandomCellFlipRelink>(model, mf);
}
