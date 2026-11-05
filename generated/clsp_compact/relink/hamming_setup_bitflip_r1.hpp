// COMPONENT: {"name": "hamming_setup_bitflip", "slot": "relink", "params": {"flips_per_step": {"type": "int", "range": [1, 3]}}}
class HammingSetupBitflip : public hsf::Relink<Model> {
public:
    using S = Model::Solution;
    HammingSetupBitflip(const Model& m, int k) : m_(m), k_(std::max(1, k)) {}

    int distance(const S& a, const S& b) override {
        int d = 0;
        const size_t n = std::min(a.size(), b.size());
        for (size_t i = 0; i < n; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            const size_t T = std::min(ra.size(), rb.size());
            for (size_t t = 0; t < T; ++t) d += (ra[t] != rb[t]);
        }
        return d;
    }

    S step(const S& cur, const S& guide, Rng& rng) override {
        diff_.clear();
        const size_t n = std::min(cur.size(), guide.size());
        for (size_t i = 0; i < n; ++i) {
            const size_t T = std::min(cur[i].size(), guide[i].size());
            for (size_t t = 0; t < T; ++t)
                if (cur[i][t] != guide[i][t]) diff_.emplace_back((int)i, (int)t);
        }
        S out = cur;
        if (diff_.empty()) return out;
        const int m = (int)diff_.size();
        const int k = std::min(k_, m);
        for (int j = 0; j < k; ++j) {
            int r = j + rng.below(m - j);
            std::swap(diff_[j], diff_[r]);
            out[diff_[j].first][diff_[j].second] = guide[diff_[j].first][diff_[j].second];
        }
        return out;
    }

private:
    const Model& m_;
    int k_;
    std::vector<std::pair<int, int>> diff_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)std::lround(params.get("flips_per_step", 1.0));
    k = std::min(3, std::max(1, k));
    return std::make_unique<HammingSetupBitflip>(model, k);
}
