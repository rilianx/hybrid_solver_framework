// COMPONENT: {"name": "random_flip_with_staged_undo", "slot": "perturbation", "params": {"flips_per_strength": {"type": "float", "range": [0.5, 4.0]}, "add_prob": {"type": "float", "range": [0.1, 0.9]}}}

static Model::Solution rfsu_fallback(const Model& m, const Model::Solution& s, Rng& rng) {
    const int n = m.n, T = m.T, N = n * T;
    Model::Solution y = s;
    if (N <= 0) return y;
    std::vector<int> order(N);
    std::iota(order.begin(), order.end(), 0);
    std::shuffle(order.begin(), order.end(), rng.g);
    for (int idx : order) {
        int i = idx / T, t = idx % T;
        y[i][t] = y[i][t] ? 0 : 1;
        if (m.feasible(y)) return y;
        y[i][t] = s[i][t];
    }
    for (int i = 0; i < n; ++i)
        for (int t = 0; t + 1 < T; ++t)
            if ((s[i][t] != 0) != (s[i][t + 1] != 0)) {
                std::swap(y[i][t], y[i][t + 1]);
                if (m.feasible(y)) return y;
                y[i][t] = s[i][t]; y[i][t + 1] = s[i][t + 1];
            }
    int c = order[0];
    y[c / T][c % T] = y[c / T][c % T] ? 0 : 1;
    return y;
}

class RandomFlipStagedUndo : public hsf::Perturbation<Model> {
public:
    RandomFlipStagedUndo(const Model& m, double fps, double ap) : m_(m), fps_(fps), ap_(ap) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T, N = n * T;
        if (N <= 0) return s;
        int k = (int)std::lround(std::max(1.0, strength) * fps_);
        k = std::clamp(k, 1, N);
        for (int attempt = 0; attempt < 3; ++attempt) {
            Sol y = s;
            adds_.clear(); rems_.clear();
            for (int c = 0; c < k; ++c) {
                bool wantAdd = rng.uniform() < ap_;
                int fi = -1, ft = -1;
                for (int tr = 0; tr < 32; ++tr) {
                    int i = rng.below(n), t = rng.below(T);
                    if (y[i][t] != s[i][t]) continue;
                    if ((s[i][t] == 0) == wantAdd) { fi = i; ft = t; break; }
                }
                if (fi < 0) {
                    for (int tr = 0; tr < 32; ++tr) {
                        int i = rng.below(n), t = rng.below(T);
                        if (y[i][t] == s[i][t]) { fi = i; ft = t; break; }
                    }
                }
                if (fi < 0) continue;
                if (s[fi][ft]) { y[fi][ft] = 0; rems_.push_back(fi * T + ft); }
                else { y[fi][ft] = 1; adds_.push_back(fi * T + ft); }
            }
            if (adds_.empty() && rems_.empty()) continue;
            if (m_.feasible(y)) return y;
            std::shuffle(rems_.begin(), rems_.end(), rng.g);
            std::shuffle(adds_.begin(), adds_.end(), rng.g);
            undo_.assign(rems_.begin(), rems_.end());
            undo_.insert(undo_.end(), adds_.begin(), adds_.end());
            for (size_t u = 0; u + 1 < undo_.size(); ++u) {
                int c = undo_[u];
                y[c / T][c % T] = s[c / T][c % T];
                if (m_.feasible(y)) return y;
            }
            k = std::max(1, k / 2);
        }
        return rfsu_fallback(m_, s, rng);
    }

private:
    const Model& m_;
    double fps_, ap_;
    std::vector<int> adds_, rems_, undo_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double fps = params.get("flips_per_strength", 1.5);
    double ap = params.get("add_prob", 0.4);
    return std::make_unique<RandomFlipStagedUndo>(model, fps, ap);
}
