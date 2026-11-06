// COMPONENT: {"name": "random_insertion_chain_kick", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [0.5, 3.0]}, "locality": {"type": "int", "range": [0, 30]}}}
class RandomInsertionChainKick : public hsf::Perturbation<Model> {
    const Model& M;
    double mps;
    int locality;
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

    void insertion(int i, int j) {
        if (j > i) std::rotate(perm.begin() + i, perm.begin() + i + 1, perm.begin() + j + 1);
        else if (j < i) std::rotate(perm.begin() + j, perm.begin() + i, perm.begin() + i + 1);
    }

public:
    RandomInsertionChainKick(const Model& m, double a, int l) : M(m), mps(a), locality(l) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        to_perm(s);
        int n = M.n;
        if (n < 2) return Model::Solution{perm};
        int k = (int)std::lround(std::max(1.0, strength) * mps);
        k = std::max(1, std::min(k, 4 * n));
        for (int t = 0; t < k; ++t) {
            int i = rng.below(n);
            int lo = 0, hi = n - 1;
            if (locality > 0) { lo = std::max(0, i - locality); hi = std::min(n - 1, i + locality); }
            int span = hi - lo;  // número de destinos distintos de i
            if (span <= 0) continue;
            int j = lo + rng.below(span);
            if (j >= i) ++j;
            insertion(i, j);
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
    double mps = params.get("moves_per_strength", 1.0);
    int loc = (int)params.get("locality", 0);
    return std::make_unique<RandomInsertionChainKick>(model, mps, loc);
}
