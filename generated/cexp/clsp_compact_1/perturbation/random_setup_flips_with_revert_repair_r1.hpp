// COMPONENT: {"name": "random_setup_flips_with_revert_repair", "slot": "perturbation", "params": {"flips_per_strength": {"type": "float", "range": [0.5, 4.0]}, "add_bias": {"type": "float", "range": [0.2, 0.8]}}}
using Sol = Model::Solution;

class RandomFlipsRevert : public hsf::Perturbation<Model> {
public:
    RandomFlipsRevert(const Model& m, double fps, double ab) : m_(m), fps_(fps), addBias_(ab) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        if (n <= 0 || T <= 0) return y;
        int total = n * T;
        int k = std::max(1, (int)std::lround(fps_ * std::max(1.0, strength)));
        k = std::min(k, total);
        removed_.clear(); added_.clear();
        mark_.assign(total, 0);
        for (int f = 0; f < k; ++f) {
            bool wantAdd = rng.uniform() < addBias_;
            int cell = -1;
            for (int tries = 0; tries < 24; ++tries) {
                int c = rng.below(total);
                if (mark_[c]) continue;
                int v = y[c / T][c % T];
                if ((wantAdd && v == 0) || (!wantAdd && v != 0) || tries >= 16) { cell = c; break; }
            }
            if (cell < 0) continue;
            mark_[cell] = 1;
            int i = cell / T, t = cell % T;
            if (y[i][t]) { y[i][t] = 0; removed_.push_back(cell); }
            else { y[i][t] = 1; added_.push_back(cell); }
        }
        if (removed_.empty() && added_.empty()) return fallback(s, rng);
        if (!m_.feasible(y)) {
            std::shuffle(removed_.begin(), removed_.end(), rng.g);
            std::shuffle(added_.begin(), added_.end(), rng.g);
            std::vector<int> order(removed_);
            order.insert(order.end(), added_.begin(), added_.end());
            bool ok = false;
            for (size_t q = 0; q + 1 < order.size(); ++q) {  // keep at least one change
                int c = order[q];
                y[c / T][c % T] = s[c / T][c % T];
                if (m_.feasible(y)) { ok = true; break; }
            }
            if (!ok) return fallback(s, rng);
        }
        if (y == s) return fallback(s, rng);
        return y;
    }

private:
    Sol fallback(const Sol& s, Rng& rng) {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        std::vector<int> idx(n * T);
        std::iota(idx.begin(), idx.end(), 0);
        std::shuffle(idx.begin(), idx.end(), rng.g);
        for (int c : idx) {
            int i = c / T, t = c % T;
            y[i][t] = 1 - (y[i][t] ? 1 : 0);
            if (m_.feasible(y)) return y;
            y[i][t] = s[i][t];
        }
        if (!idx.empty()) { int c = idx[0]; y[c / T][c % T] = 1 - (s[c / T][c % T] ? 1 : 0); }
        return y;
    }
    const Model& m_;
    double fps_, addBias_;
    std::vector<int> removed_, added_;
    std::vector<char> mark_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double fps = params.get("flips_per_strength", 1.5);
    double ab = params.get("add_bias", 0.5);
    return std::make_unique<RandomFlipsRevert>(model, fps, ab);
}
