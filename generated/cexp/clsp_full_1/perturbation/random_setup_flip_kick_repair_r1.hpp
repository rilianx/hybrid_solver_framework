// COMPONENT: {"name": "random_setup_flip_kick_repair", "slot": "perturbation", "params": {"flip_per_strength": {"type": "float", "range": [0.5, 3.0]}, "add_bias": {"type": "float", "range": [0.2, 0.8]}, "repair_iters": {"type": "int", "range": [5, 80]}, "latest_bias": {"type": "float", "range": [0.3, 1.0]}}}
using Sol = Model::Solution;

class Fixer {
public:
    explicit Fixer(const Model& m) : m_(m) {}
    bool repair(Sol& y, Rng& rng, int maxIt, double pLatest) {
        const int n = m_.n, T = m_.T;
        for (int it = 0;; ++it) {
            if (m_.feasible(y)) return true;
            if (it >= maxIt) return false;
            cand_.clear();
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t) {
                    int e = m_.sinkEdge[(size_t)i * T + t];
                    if (e >= 0 && m_.E[e].cap > 1e-7) { cand_.push_back(i * T + t); break; }
                }
            if (cand_.empty()) return false;
            bool done = false;
            for (size_t k = 0; k < cand_.size() && !done; ++k) {
                size_t j = k + (size_t)rng.below((int)(cand_.size() - k));
                std::swap(cand_[k], cand_[j]);
                int i = cand_[k] / T, t = cand_[k] % T;
                free_.clear();
                for (int tt = 0; tt <= t; ++tt) if (!y[i][tt]) free_.push_back(tt);
                if (free_.empty()) continue;
                int pick = (rng.uniform() < pLatest) ? free_.back() : free_[rng.below((int)free_.size())];
                y[i][pick] = 1; done = true;
            }
            if (!done) {
                free_.clear();
                for (int i = 0; i < n; ++i)
                    for (int t = 0; t < T; ++t)
                        if (y[i][t] && m_.E[m_.prodEdge[i][t] + 1].cap <= 1e-9) free_.push_back(i * T + t);
                if (free_.empty()) return false;
                int c = free_[rng.below((int)free_.size())];
                y[c / T][c % T] = 0;
            }
        }
    }
    Sol fallback(const Sol& s, Rng& rng) {
        const int n = m_.n, T = m_.T, N = n * T;
        order_.resize(N);
        std::iota(order_.begin(), order_.end(), 0);
        std::shuffle(order_.begin(), order_.end(), rng.g);
        Sol y = s;
        for (int c : order_) {
            int i = c / T, t = c % T;
            y[i][t] = !y[i][t];
            if (m_.feasible(y)) return y;
            y[i][t] = !y[i][t];
        }
        if (N > 0) { int c = order_[0]; y[c / T][c % T] = !y[c / T][c % T]; }
        return y;
    }
private:
    const Model& m_;
    std::vector<int> cand_, free_, order_;
};

class RandomFlipKick : public hsf::Perturbation<Model> {
public:
    RandomFlipKick(const Model& m, double fps, double ab, int ri, double lb)
        : m_(m), fx_(m), fps_(fps), ab_(ab), ri_(ri), lb_(lb) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 0) return s;
        Sol y = s;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * fps_));
        k = std::min(k, n * T);
        for (int f = 0; f < k; ++f) {
            int want = rng.uniform() < ab_ ? 0 : 1;  // value to flip from
            int ci = rng.below(n), ct = rng.below(T);
            for (int a = 0; a < 8 && y[ci][ct] != want; ++a) { ci = rng.below(n); ct = rng.below(T); }
            y[ci][ct] = !y[ci][ct];
        }
        if (y == s) { int i = rng.below(n), t = rng.below(T); y[i][t] = !y[i][t]; }
        if (fx_.repair(y, rng, ri_, lb_) && y != s) return y;
        return fx_.fallback(s, rng);
    }
private:
    const Model& m_;
    Fixer fx_;
    double fps_, ab_;
    int ri_;
    double lb_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double fps = params.get("flip_per_strength", 1.5);
    double ab = params.get("add_bias", 0.5);
    int ri = (int)params.get("repair_iters", 30);
    double lb = params.get("latest_bias", 0.7);
    return std::make_unique<RandomFlipKick>(model, fps, ab, ri, lb);
}
