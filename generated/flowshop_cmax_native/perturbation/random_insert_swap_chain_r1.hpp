// COMPONENT: {"name": "random_insert_swap_chain", "slot": "perturbation", "params": {"k_base": {"type": "int", "range": [1, 10]}, "p_insert": {"type": "float", "range": [0.0, 1.0]}, "max_dist_frac": {"type": "float", "range": [0.05, 1.0]}}}
class RandomInsertSwapChain : public hsf::Perturbation<Model> {
public:
    RandomInsertSwapChain(const Model& M, int k, double pIns, double distFrac)
        : M_(M), k_(k), pIns_(pIns), distFrac_(distFrac) {}
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution out = s;
        if (out.empty()) return out;
        std::vector<int>& v = out[0];
        int n = (int)v.size();
        if (n < 2) return out;
        int maxD = std::max(1, std::min(n - 1, (int)std::lround(distFrac_ * n)));
        int moves = std::max(1, (int)std::lround(k_ * std::max(1.0, strength)));
        for (int t = 0; t < moves; ++t) {
            int a = rng.below(n);
            int dist = 1 + rng.below(maxD);
            int b = rng.uniform() < 0.5 ? a - dist : a + dist;
            if (b < 0 || b >= n) b = (a - dist >= 0) ? a - dist : a + dist;
            if (b < 0 || b >= n) b = (a == 0) ? 1 : a - 1;
            if (rng.uniform() < pIns_) {
                if (a < b) std::rotate(v.begin() + a, v.begin() + a + 1, v.begin() + b + 1);
                else std::rotate(v.begin() + b, v.begin() + a, v.begin() + a + 1);
            } else {
                std::swap(v[a], v[b]);
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
    int k_;
    double pIns_, distFrac_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_base", 3.0);
    double pIns = params.get("p_insert", 0.7);
    double df = params.get("max_dist_frac", 0.3);
    return std::make_unique<RandomInsertSwapChain>(model, k, pIns, df);
}
