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
        // tope de longitud de bloque: dos bloques de igual tamaño deben caber
        int Lcap = std::min(std::max(2, (int)std::lround(frac_ * n)), n / 2);
        int reps = std::max(1, (int)std::lround(reps_ * std::max(1.0, strength)));
        for (int t = 0; t < reps; ++t) {
            // bloques de igual longitud L (>=2 cuando cabe): solo cambian 2L posiciones,
            // concentradas en dos zonas lejanas; lo que queda entre ellas no se mueve
            int L = (Lcap >= 2) ? 2 + rng.below(Lcap - 1) : 1;
            int a = rng.below(n - 2 * L + 1);
            int b = a + L + rng.below(n - L - (a + L) + 1);
            std::swap_ranges(v.begin() + a, v.begin() + a + L, v.begin() + b);
            bool rev = mode_ == "always" || (mode_ == "random" && rng.uniform() < 0.5);
            if (rev && L >= 2) {
                if (rng.uniform() < 0.5) std::reverse(v.begin() + a, v.begin() + a + L);
                else std::reverse(v.begin() + b, v.begin() + b + L);
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
