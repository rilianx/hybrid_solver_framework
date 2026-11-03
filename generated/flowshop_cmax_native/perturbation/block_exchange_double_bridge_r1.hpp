// COMPONENT: {"name": "block_exchange_double_bridge", "slot": "perturbation", "params": {"reps_base": {"type": "int", "range": [1, 4]}, "max_block_frac": {"type": "float", "range": [0.05, 0.5]}, "reverse_mode": {"type": "cat", "values": ["none", "random", "always"]}}}
class BlockExchange : public hsf::Perturbation<Model> {
public:
    BlockExchange(const Model& M, int reps, double frac, std::string mode)
        : M_(M), reps_(reps), frac_(frac), mode_(std::move(mode)) {}
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution out = s;
        if (out.empty()) return out;
        std::vector<int>& v = out[0];
        int n = (int)v.size();
        if (n < 2) return out;
        int maxL = std::max(1, (int)std::lround(frac_ * n));
        int reps = std::max(1, (int)std::lround(reps_ * std::max(1.0, strength)));
        for (int t = 0; t < reps; ++t) {
            int L1 = 1 + rng.below(maxL), L2 = 1 + rng.below(maxL);
            L1 = std::min(L1, n - 1);
            L2 = std::min(L2, n - L1);
            int a = rng.below(n - L1 - L2 + 1);
            auto beg = v.begin() + a;
            // [a,a+L1) y [a+L1,a+L1+L2) intercambian lugar
            std::rotate(beg, beg + L1, beg + L1 + L2);
            bool rev = mode_ == "always" || (mode_ == "random" && rng.uniform() < 0.5);
            if (rev) {
                if (rng.uniform() < 0.5) std::reverse(beg, beg + L2);
                else std::reverse(beg + L2, beg + L2 + L1);
            }
        }
        if (v == s[0]) {
            for (int tries = 0; tries < 64; ++tries) {
                int a = rng.below(n), b = rng.below(n);
                if (v[a] != v[b]) { std::swap(v[a], v[b]); break; }
            }
            if (v == s[0])
                for (int a = 0; a + 1 < n; ++a)
                    if (v[a] != v[a + 1]) { std::swap(v[a], v[a + 1]); break; }
        }
        return out;
    }
private:
    const Model& M_;
    int reps_;
    double frac_;
    std::string mode_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int reps = (int)params.get("reps_base", 1.0);
    double frac = params.get("max_block_frac", 0.2);
    std::string mode = params.text("reverse_mode", "random");
    return std::make_unique<BlockExchange>(model, reps, frac, mode);
}
