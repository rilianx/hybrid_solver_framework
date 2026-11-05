// COMPONENT: {"name": "hamming_cell_flip_relink", "slot": "relink", "params": {"max_flips": {"type": "int", "range": [1, 4]}, "same_item_prob": {"type": "float", "range": [0.0, 1.0]}}}
class HammingCellFlipRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    int maxFlips;
    double sameItem;
    std::vector<int> diffI, diffT;
    std::vector<int> pick;
public:
    HammingCellFlipRelink(const Model& model, int mf, double si)
        : m(model), maxFlips(std::max(1, mf)), sameItem(si) {}

    int distance(const Sol& a, const Sol& b) override {
        int dist = 0;
        size_t ni = std::min(a.size(), b.size());
        for (size_t i = 0; i < ni; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            size_t nt = std::min(ra.size(), rb.size());
            for (size_t t = 0; t < nt; ++t) dist += (ra[t] != rb[t]);
            dist += (int)(std::max(ra.size(), rb.size()) - nt);
        }
        size_t mx = std::max(a.size(), b.size());
        for (size_t i = ni; i < mx; ++i) dist += (int)(i < a.size() ? a[i].size() : b[i].size());
        return dist;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) return guide;
        diffI.clear(); diffT.clear();
        for (size_t i = 0; i < cur.size(); ++i) {
            if (cur[i].size() != guide[i].size()) return guide;
            for (size_t t = 0; t < cur[i].size(); ++t)
                if (cur[i][t] != guide[i][t]) { diffI.push_back((int)i); diffT.push_back((int)t); }
        }
        if (diffI.empty()) return guide;
        Sol r = cur;
        int k = 1 + rng.below(maxFlips);
        k = std::min<int>(k, (int)diffI.size());
        int sz = (int)diffI.size();
        int idx = rng.below(sz);
        int item = diffI[idx];
        r[item][diffT[idx]] = guide[item][diffT[idx]];
        std::swap(diffI[idx], diffI[sz - 1]); std::swap(diffT[idx], diffT[sz - 1]); --sz;
        for (int f = 1; f < k && sz > 0; ++f) {
            int chosen = -1;
            if (rng.uniform() < sameItem) {
                pick.clear();
                for (int j = 0; j < sz; ++j) if (diffI[j] == item) pick.push_back(j);
                if (!pick.empty()) chosen = pick[rng.below((int)pick.size())];
            }
            if (chosen < 0) chosen = rng.below(sz);
            int ii = diffI[chosen], tt = diffT[chosen];
            r[ii][tt] = guide[ii][tt];
            item = ii;
            std::swap(diffI[chosen], diffI[sz - 1]); std::swap(diffT[chosen], diffT[sz - 1]); --sz;
        }
        return r;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int mf = (int)std::lround(params.get("max_flips", 1.0));
    double si = params.get("same_item_prob", 0.5);
    return std::make_unique<HammingCellFlipRelink>(model, mf, si);
}
