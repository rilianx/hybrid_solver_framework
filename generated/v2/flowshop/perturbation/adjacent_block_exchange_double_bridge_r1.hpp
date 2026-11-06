// COMPONENT: {"name": "adjacent_block_exchange_double_bridge", "slot": "perturbation", "params": {"bridges_per_strength": {"type": "float", "range": [0.5, 2.0]}, "max_block_frac": {"type": "float", "range": [0.05, 0.5]}, "reverse_prob": {"type": "float", "range": [0.0, 0.5]}}}
class AdjacentBlockExchange : public hsf::Perturbation<Model> {
    const Model& M;
    double bps, frac, revp;
    std::vector<char> seen;
    std::vector<int> perm;

    void to_perm(const Model::Solution& s) {
        perm.clear();
        perm.reserve(M.n);
        seen.assign(M.n, 0);
        if (!s.empty())
            for (int j : s[0])
                if (j >= 0 && j < M.n && !seen[j]) { seen[j] = 1; perm.push_back(j); }
        for (int j = 0; j < M.n; ++j) if (!seen[j]) perm.push_back(j);
    }

public:
    AdjacentBlockExchange(const Model& m, double b, double f, double r) : M(m), bps(b), frac(f), revp(r) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        to_perm(s);
        int n = M.n;
        if (n < 2) return Model::Solution{perm};
        int k = (int)std::lround(std::max(1.0, strength) * bps);
        k = std::max(1, std::min(k, n));
        int maxSeg = std::max(1, (int)std::lround(frac * n));
        for (int t = 0; t < k; ++t) {
            int lb = 1 + rng.below(std::min(maxSeg, n - 1));
            int lc = 1 + rng.below(std::min(maxSeg, n - lb));
            int a = rng.below(n - lb - lc + 1);
            auto first = perm.begin() + a;
            std::rotate(first, first + lb, first + lb + lc);  // B C -> C B
            if (revp > 0.0 && rng.uniform() < revp) {
                if (rng.below(2) == 0) std::reverse(first, first + lc);           // invierte C
                else std::reverse(first + lc, first + lc + lb);                  // invierte B
            }
        }
        if (s.size() == 1 && s[0] == perm) {
            int a = rng.below(n), b = rng.below(n - 1);
            if (b >= a) ++b;
            std::swap(perm[a], perm[b]);
        }
        return Model::Solution{perm};
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double b = params.get("bridges_per_strength", 1.0);
    double f = params.get("max_block_frac", 0.15);
    double r = params.get("reverse_prob", 0.1);
    return std::make_unique<AdjacentBlockExchange>(model, b, f, r);
}
