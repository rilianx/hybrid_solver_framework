// COMPONENT: {"name": "item_row_copy_relink", "slot": "relink", "params": {"rows_per_step": {"type": "int", "range": [1, 3]}}}
class ItemRowCopyRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    int rowsPerStep;
    std::vector<int> diffRows;
public:
    ItemRowCopyRelink(const Model& model, int rps) : m(model), rowsPerStep(std::max(1, rps)) {}

    int distance(const Sol& a, const Sol& b) override {
        int dist = 0;
        size_t ni = std::min(a.size(), b.size());
        for (size_t i = 0; i < ni; ++i) dist += (a[i] != b[i]);
        dist += (int)(std::max(a.size(), b.size()) - ni);
        return dist;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) return guide;
        diffRows.clear();
        for (size_t i = 0; i < cur.size(); ++i)
            if (cur[i] != guide[i]) diffRows.push_back((int)i);
        if (diffRows.empty()) return guide;
        Sol r = cur;
        int k = 1 + rng.below(rowsPerStep);
        int sz = (int)diffRows.size();
        k = std::min(k, sz);
        for (int f = 0; f < k; ++f) {
            int idx = rng.below(sz);
            int i = diffRows[idx];
            r[i] = guide[i];
            std::swap(diffRows[idx], diffRows[sz - 1]);
            --sz;
        }
        return r;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int rps = (int)std::lround(params.get("rows_per_step", 1.0));
    return std::make_unique<ItemRowCopyRelink>(model, rps);
}
