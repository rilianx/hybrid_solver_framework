// COMPONENT: {"name": "random_multi_insertion", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "extra": {"type": "int", "range": [0, 3]}}}
class RandomMultiInsertion : public hsf::Perturbation<Model> {
public:
    RandomMultiInsertion(const Model& m, double scale, int extra) : md(m), scale_(scale), extra_(extra) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out = s;
        if (out.empty()) return out;
        auto& v = out[0];
        int N = (int)v.size();
        if (N < 2) return out;
        int k = std::max(1, (int)std::lround(scale_ * std::max(1.0, strength)) + extra_);
        for (int t = 0; t < k; ++t) {
            int i = rng.below(N);
            int j = rng.below(N - 1);
            if (j >= i) ++j;
            int x = v[i];
            if (i < j) std::move(v.begin() + i + 1, v.begin() + j + 1, v.begin() + i);
            else std::move_backward(v.begin() + j, v.begin() + i, v.begin() + i + 1);
            v[j] = x;
        }
        if (v == s[0]) {
            int i = rng.below(N), j = rng.below(N - 1);
            if (j >= i) ++j;
            std::swap(v[i], v[j]);
        }
        return out;
    }
private:
    const Model& md;
    double scale_;
    int extra_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("scale", 1.0);
    int extra = (int)params.get("extra", 0);
    return std::make_unique<RandomMultiInsertion>(model, scale, extra);
}
