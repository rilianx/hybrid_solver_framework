// COMPONENT: {"name": "window_ruin_silver_meal_rebuild", "slot": "perturbation", "params": {"win_base": {"type": "int", "range": [1, 6]}, "win_per_strength": {"type": "float", "range": [0.5, 3.0]}, "item_frac": {"type": "float", "range": [0.1, 1.0]}, "sm_noise": {"type": "float", "range": [0.0, 0.6]}, "repair_iters": {"type": "int", "range": [5, 80]}, "latest_bias": {"type": "float", "range": [0.3, 1.0]}}}
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

class WindowSilverMeal : public hsf::Perturbation<Model> {
public:
    WindowSilverMeal(const Model& m, int wb, double wps, double ifr, double nz, int ri, double lb)
        : m_(m), fx_(m), wb_(wb), wps_(wps), ifr_(ifr), nz_(nz), ri_(ri), lb_(lb) {
        items_.resize(m.n);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 0) return s;
        Sol y = s;
        int L = std::min(T, std::max(1, wb_ + (int)std::lround(std::max(1.0, strength) * wps_)));
        int a = rng.below(T - L + 1), b = a + L - 1;
        int k = std::min(n, std::max(1, (int)std::lround(ifr_ * n)));
        std::iota(items_.begin(), items_.end(), 0);
        for (int q = 0; q < k; ++q) {
            int j = q + rng.below(n - q);
            std::swap(items_[q], items_[j]);
            rebuild(y[items_[q]], items_[q], a, b, rng);
        }
        if (y == s) { int i = items_[0], t = a + rng.below(L); y[i][t] = !y[i][t]; }
        if (fx_.repair(y, rng, ri_, lb_) && y != s) return y;
        return fx_.fallback(s, rng);
    }
private:
    void rebuild(std::vector<int>& yi, int i, int a, int b, Rng& rng) {
        const std::vector<double>& di = m_.d[i];
        double hi = m_.h[i];
        for (int t = a; t <= b; ++t) yi[t] = 0;
        int p = a;
        while (p <= b) {
            if (di[p] <= 0) { ++p; continue; }
            yi[p] = 1;
            double sc = m_.s[i] * (1.0 + nz_ * (2.0 * rng.uniform() - 1.0));
            if (sc < 0) sc = 0;
            double maxLot = std::max(di[p], m_.cap[p] - m_.st[i]);
            double hold = 0.0, lot = di[p], best = sc;
            int q = p;
            while (q + 1 <= b) {
                double add = hi * di[q + 1] * (q + 1 - p);
                double avg = (sc + hold + add) / (double)(q + 2 - p);
                if (avg > best + 1e-12 || lot + di[q + 1] > maxLot) break;
                hold += add; lot += di[q + 1]; best = avg; ++q;
            }
            p = q + 1;
        }
    }
    const Model& m_;
    Fixer fx_;
    int wb_;
    double wps_, ifr_, nz_;
    int ri_;
    double lb_;
    std::vector<int> items_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int wb = (int)params.get("win_base", 3);
    double wps = params.get("win_per_strength", 1.0);
    double ifr = params.get("item_frac", 0.4);
    double nz = params.get("sm_noise", 0.3);
    int ri = (int)params.get("repair_iters", 30);
    double lb = params.get("latest_bias", 0.7);
    return std::make_unique<WindowSilverMeal>(model, wb, wps, ifr, nz, ri, lb);
}
