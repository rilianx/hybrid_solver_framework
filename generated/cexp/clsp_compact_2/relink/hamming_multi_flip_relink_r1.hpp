// COMPONENT: {"name": "hamming_multi_flip_relink", "slot": "relink", "params": {"max_flips": {"type": "int", "range": [1, 4]}}}
class HammingMultiFlipRelink : public hsf::Relink<Model> {
public:
    HammingMultiFlipRelink(const Model& m, int k) : model(m), maxFlips(std::max(1, k)) {}

    int distance(const Sol& a, const Sol& b) override {
        int d = 0;
        const size_t R = a.size();
        for (size_t i = 0; i < R; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            const size_t C = ra.size();
            for (size_t t = 0; t < C; ++t) d += (ra[t] != rb[t]);
        }
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        diffI.clear(); diffT.clear();
        const size_t R = cur.size();
        for (size_t i = 0; i < R; ++i) {
            const auto& rc = cur[i];
            const auto& rg = guide[i];
            const size_t C = rc.size();
            for (size_t t = 0; t < C; ++t)
                if (rc[t] != rg[t]) { diffI.push_back((int)i); diffT.push_back((int)t); }
        }
        const int m = (int)diffI.size();
        if (m == 0) return guide;
        int k = 1 + rng.below(std::min(maxFlips, m));
        Sol out = cur;
        for (int j = 0; j < k; ++j) {
            int r = j + rng.below(m - j);
            std::swap(diffI[j], diffI[r]);
            std::swap(diffT[j], diffT[r]);
            out[diffI[j]][diffT[j]] = guide[diffI[j]][diffT[j]];
        }
        return out;
    }

private:
    const Model& model;
    int maxFlips;
    std::vector<int> diffI, diffT;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)std::lround(params.get("max_flips", 1.0));
    k = std::max(1, std::min(4, k));
    return std::make_unique<HammingMultiFlipRelink>(model, k);
}
