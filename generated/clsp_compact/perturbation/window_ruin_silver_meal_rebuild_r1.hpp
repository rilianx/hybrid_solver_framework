// COMPONENT: {"name": "window_ruin_silver_meal_rebuild", "slot": "perturbation", "params": {"window_per_strength": {"type": "float", "range": [0.5, 4.0]}, "item_frac": {"type": "float", "range": [0.1, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.6]}}}

static Model::Solution wrsm_fallback(const Model& m, const Model::Solution& s, Rng& rng) {
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

class WindowRuinSilverMeal : public hsf::Perturbation<Model> {
public:
    WindowRuinSilverMeal(const Model& m, double wps, double frac, double noise)
        : m_(m), wps_(wps), frac_(frac), noise_(noise) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 0) return s;
        int L = (int)std::lround(std::max(1.0, strength) * wps_);
        L = std::clamp(L, 1, T);
        for (int attempt = 0; attempt < 3; ++attempt) {
            int a = rng.below(T - L + 1), b = a + L - 1;
            items_.clear();
            for (int i = 0; i < n; ++i) if (rng.uniform() < frac_) items_.push_back(i);
            if (items_.empty()) items_.push_back(rng.below(n));
            Sol y = s;
            for (int i : items_) rebuild(y[i], i, a, b, rng);
            if (y == s) { L = std::min(T, L + 1); continue; }
            if (m_.feasible(y)) return y;
            Sol u = y;
            for (int i : items_)
                for (int t = a; t <= b; ++t) if (s[i][t]) u[i][t] = 1;
            if (u != s && m_.feasible(u)) return u;
            std::shuffle(items_.begin(), items_.end(), rng.g);
            for (size_t q = 0; q + 1 < items_.size(); ++q) {
                y[items_[q]] = s[items_[q]];
                if (y != s && m_.feasible(y)) return y;
            }
            L = std::min(T, L + 1);
        }
        return wrsm_fallback(m_, s, rng);
    }

private:
    void rebuild(std::vector<int>& row, int i, int a, int b, Rng& rng) {
        const int T = m_.T;
        int hi = T;
        for (int t = b + 1; t < T; ++t) if (row[t]) { hi = t; break; }
        for (int t = a; t <= b; ++t) row[t] = 0;
        double sc = m_.s[i] * (1.0 + noise_ * (2.0 * rng.uniform() - 1.0));
        if (sc < 0.0) sc = 0.0;
        const double hc = m_.h[i];
        int lastSet = -1;
        int t = a;
        while (t < hi) {
            if (m_.d[i][t] <= 1e-9) { ++t; continue; }
            if (t > b) {
                if (lastSet < 0) row[b] = 1;
                break;
            }
            int p = t;
            row[p] = 1; lastSet = p;
            double hold = 0.0;
            int j = p + 1;
            while (j < hi) {
                double add = hc * (double)(j - p) * m_.d[i][j];
                double nAvg = (sc + hold + add) / (double)(j - p + 1);
                double cAvg = (sc + hold) / (double)(j - p);
                if (nAvg > cAvg) break;
                hold += add;
                ++j;
            }
            t = j;
        }
    }

    const Model& m_;
    double wps_, frac_, noise_;
    std::vector<int> items_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double wps = params.get("window_per_strength", 1.5);
    double frac = params.get("item_frac", 0.4);
    double noise = params.get("noise", 0.2);
    return std::make_unique<WindowRuinSilverMeal>(model, wps, frac, noise);
}
