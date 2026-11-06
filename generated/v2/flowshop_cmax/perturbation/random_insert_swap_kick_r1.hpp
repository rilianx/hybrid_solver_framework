// COMPONENT: {"name": "random_insert_swap_kick", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [0.5, 4.0]}, "swap_prob": {"type": "float", "range": [0.0, 1.0]}}}
class RandomInsertSwapKick : public hsf::Perturbation<Model> {
public:
    RandomInsertSwapKick(const Model& m, double mps, double sp) : M(m), mps_(mps), swapProb_(sp) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const int n = M.n;
        sanitize(s);
        Model::Solution out(1);
        std::vector<int>& perm = out[0];
        perm = work_;
        if (n >= 2) {
            int k = std::max(1, (int)std::lround(mps_ * std::max(1.0, strength)));
            for (int t = 0; t < k; ++t) {
                int a = rng.below(n);
                int b = rng.below(n - 1);
                if (b >= a) ++b;
                if (rng.uniform() < swapProb_) {
                    std::swap(perm[a], perm[b]);
                } else {
                    if (a < b) std::rotate(perm.begin() + a, perm.begin() + a + 1, perm.begin() + b + 1);
                    else std::rotate(perm.begin() + b, perm.begin() + a, perm.begin() + a + 1);
                }
            }
            if (s.size() == 1 && s[0] == perm) {
                int a = rng.below(n);
                int b = rng.below(n - 1);
                if (b >= a) ++b;
                std::swap(perm[a], perm[b]);
            }
        }
        return out;
    }

private:
    void sanitize(const Model::Solution& s) {
        const int n = M.n;
        work_.clear();
        seen_.assign(n, 0);
        if (!s.empty())
            for (int x : s[0])
                if (x >= 0 && x < n && !seen_[x]) { seen_[x] = 1; work_.push_back(x); }
        for (int j = 0; j < n; ++j) if (!seen_[j]) work_.push_back(j);
    }
    const Model& M;
    double mps_, swapProb_;
    std::vector<int> work_;
    std::vector<char> seen_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mps = params.get("moves_per_strength", 1.5);
    double sp = params.get("swap_prob", 0.3);
    return std::make_unique<RandomInsertSwapKick>(model, mps, sp);
}
