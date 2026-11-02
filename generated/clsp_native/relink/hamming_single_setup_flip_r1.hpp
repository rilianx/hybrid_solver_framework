// COMPONENT: {"name": "hamming_single_setup_flip", "slot": "relink", "params": {"add_bias": {"type": "float", "range": [0.0, 1.0]}}}
class HammingSingleSetupFlip : public hsf::Relink<Model> {
public:
    HammingSingleSetupFlip(const Model& m, double bias) : m_(m), bias_(bias) {}

    int distance(const Sol& a, const Sol& b) override {
        int dcount = 0;
        for (int i = 0; i < m_.n; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            for (int t = 0; t < m_.T; ++t) dcount += (ra[t] != rb[t]);
        }
        return dcount;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        adds_.clear();
        rems_.clear();
        for (int i = 0; i < m_.n; ++i)
            for (int t = 0; t < m_.T; ++t)
                if (cur[i][t] != guide[i][t]) {
                    if (guide[i][t]) adds_.push_back(i * m_.T + t);
                    else rems_.push_back(i * m_.T + t);
                }
        if (adds_.empty() && rems_.empty()) return guide;
        int code;
        if (!adds_.empty() && (rems_.empty() || rng.uniform() < bias_)) {
            code = adds_[rng.below((int)adds_.size())];
        } else if (adds_.empty()) {
            code = rems_[rng.below((int)rems_.size())];
        } else {
            int tot = (int)(adds_.size() + rems_.size());
            int k = rng.below(tot);
            code = k < (int)adds_.size() ? adds_[k] : rems_[k - adds_.size()];
        }
        Sol out = cur;
        int i = code / m_.T, t = code % m_.T;
        out[i][t] = guide[i][t];
        return out;
    }

private:
    const Model& m_;
    double bias_;
    std::vector<int> adds_, rems_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double b = params.get("add_bias", 0.5);
    return std::make_unique<HammingSingleSetupFlip>(model, b);
}
