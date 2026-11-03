// COMPONENT: {"name": "block_exchange_double_bridge", "slot": "perturbation", "params": {"segments_base": {"type": "int", "range": [3, 8]}, "window_frac": {"type": "float", "range": [0.3, 1.0]}, "reverse_mode": {"type": "cat", "values": ["none", "random", "always"]}}}
class BlockExchange : public hsf::Perturbation<Model> {
public:
    BlockExchange(const Model& M, int segs, double frac, std::string mode)
        : M_(M), segs_(segs), frac_(frac), mode_(std::move(mode)) {}
    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        Model::Solution out = s;
        if (out.empty()) return out;
        std::vector<int>& v = out[0];
        int n = (int)v.size();
        if (n < 2) return out;
        // ventana ancha: la reestructuración afecta a una gran porción de la secuencia
        int W = std::min(n, std::max(4, (int)std::lround(frac_ * n)));
        if (W >= 3) {
            int k = (int)std::lround(segs_ * std::max(1.0, strength));
            k = std::max(3, std::min(k, W));
            int start = rng.below(n - W + 1);
            // k-1 puntos de corte distintos en (0, W)
            cand_.resize(W - 1);
            for (int i = 0; i < W - 1; ++i) cand_[i] = i + 1;
            for (int i = 0; i < k - 1; ++i) {
                int j = i + rng.below(W - 1 - i);
                std::swap(cand_[i], cand_[j]);
            }
            cuts_.assign(cand_.begin(), cand_.begin() + (k - 1));
            std::sort(cuts_.begin(), cuts_.end());
            bounds_.clear();
            bounds_.push_back(0);
            for (int c : cuts_) bounds_.push_back(c);
            bounds_.push_back(W);
            // permutación de segmentos distinta de la identidad
            perm_.resize(k);
            for (int i = 0; i < k; ++i) perm_[i] = i;
            if (k == 3) {
                // double bridge clásico: A B C -> A C B, o rotaciones
                int r = rng.below(3);
                if (r == 0) { perm_ = {0, 2, 1}; }
                else if (r == 1) { perm_ = {1, 2, 0}; }
                else { perm_ = {2, 0, 1}; }
            } else {
                std::shuffle(perm_.begin(), perm_.end(), rng.g);
                bool ident = true;
                for (int i = 0; i < k; ++i) if (perm_[i] != i) { ident = false; break; }
                if (ident) std::swap(perm_[1], perm_[2]);
            }
            tmp_.clear();
            tmp_.reserve(W);
            for (int idx = 0; idx < k; ++idx) {
                int p = perm_[idx];
                int b0 = start + bounds_[p], b1 = start + bounds_[p + 1];
                size_t pos = tmp_.size();
                tmp_.insert(tmp_.end(), s[0].begin() + b0, s[0].begin() + b1);
                bool rev = mode_ == "always" || (mode_ == "random" && rng.uniform() < 0.5);
                if (rev && b1 - b0 >= 2) std::reverse(tmp_.begin() + pos, tmp_.end());
            }
            std::copy(tmp_.begin(), tmp_.end(), v.begin() + start);
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
    int segs_;
    double frac_;
    std::string mode_;
    std::vector<int> cand_, cuts_, bounds_, perm_, tmp_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int segs = (int)params.get("segments_base", 3.0);
    double frac = params.get("window_frac", 0.6);
    std::string mode = params.text("reverse_mode", "random");
    return std::make_unique<BlockExchange>(model, segs, frac, mode);
}
