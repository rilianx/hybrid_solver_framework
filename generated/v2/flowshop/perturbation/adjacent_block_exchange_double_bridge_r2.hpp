// COMPONENT: {"name": "adjacent_block_exchange_double_bridge", "slot": "perturbation", "params": {"bridges_per_strength": {"type": "float", "range": [0.5, 2.0]}, "min_span_frac": {"type": "float", "range": [0.3, 1.0]}, "reverse_prob": {"type": "float", "range": [0.0, 0.5]}}}
class AdjacentBlockExchange : public hsf::Perturbation<Model> {
    const Model& M;
    double bps, span, revp;
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
    AdjacentBlockExchange(const Model& m, double b, double sp, double r) : M(m), bps(b), span(sp), revp(r) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        to_perm(s);
        int n = M.n;
        if (n < 2) return Model::Solution{perm};
        if (n == 2) {
            std::swap(perm[0], perm[1]);
            return Model::Solution{perm};
        }
        int k = (int)std::lround(std::max(1.0, strength) * bps);
        k = std::max(1, std::min(k, 4));
        int minSpan = std::max(3, (int)std::lround(span * n));
        minSpan = std::min(minSpan, n);
        for (int t = 0; t < k; ++t) {
            // ventana amplia [a, a+L): doble puente con cortes a, a+c1, a+L
            int L = minSpan + rng.below(n - minSpan + 1);
            int a = rng.below(n - L + 1);
            int lo = std::max(1, L / 4);
            int hi = std::min(L - 1, L - L / 4);
            if (hi < lo) hi = lo;
            int c1 = lo + rng.below(hi - lo + 1);   // bloques B y C equilibrados
            auto first = perm.begin() + a;
            std::rotate(first, first + c1, first + L);  // B C -> C B
            int lc = L - c1, lb = c1;
            if (revp > 0.0 && rng.uniform() < revp) {
                if (rng.below(2) == 0) std::reverse(first, first + lc);        // invierte C
                else std::reverse(first + lc, first + lc + lb);               // invierte B
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
    double sp = params.get("min_span_frac", 0.5);
    double r = params.get("reverse_prob", 0.1);
    return std::make_unique<AdjacentBlockExchange>(model, b, sp, r);
}
