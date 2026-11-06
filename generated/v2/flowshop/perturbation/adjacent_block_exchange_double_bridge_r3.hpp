// COMPONENT: {"name": "adjacent_block_exchange_double_bridge", "slot": "perturbation", "params": {"bridges_per_strength": {"type": "float", "range": [0.5, 2.0]}, "max_block": {"type": "int", "range": [1, 6]}, "reverse_prob": {"type": "float", "range": [0.0, 0.5]}}}
class AdjacentBlockExchange : public hsf::Perturbation<Model> {
    const Model& M;
    double bps;
    int maxb;
    double revp;
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
    AdjacentBlockExchange(const Model& m, double b, int mb, double r) : M(m), bps(b), maxb(std::max(1, mb)), revp(r) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        to_perm(s);
        int n = M.n;
        if (n < 2) return Model::Solution{perm};
        if (n == 2) {
            std::swap(perm[0], perm[1]);
            return Model::Solution{perm};
        }
        int k = (int)std::lround(std::max(1.0, strength) * bps);
        k = std::max(1, std::min(k, 8));
        for (int t = 0; t < k; ++t) {
            // intercambio local de dos bloques cortos adyacentes B C -> C B
            int lb = 1 + rng.below(std::min(maxb, n - 1));
            int lc = 1 + rng.below(std::min(maxb, n - lb));
            int L = lb + lc;
            int a = rng.below(n - L + 1);
            auto first = perm.begin() + a;
            std::rotate(first, first + lb, first + L);  // B C -> C B
            if (revp > 0.0 && rng.uniform() < revp) {
                if (rng.below(2) == 0) { if (lc > 1) std::reverse(first, first + lc); }        // invierte C
                else if (lb > 1) std::reverse(first + lc, first + lc + lb);                    // invierte B
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
    int mb = (int)std::lround(params.get("max_block", 3));
    mb = std::max(1, std::min(mb, 6));
    double r = params.get("reverse_prob", 0.1);
    return std::make_unique<AdjacentBlockExchange>(model, b, mb, r);
}
