// COMPONENT: {"name": "multi_start_polar_sweep_2opt", "slot": "constructor", "params": {"trials": {"type": "int", "range": [1, 16]}, "two_opt_passes": {"type": "int", "range": [0, 30]}, "direction": {"type": "cat", "values": ["both", "ccw"]}}}
class MultiStartPolarSweep : public hsf::Constructor<Model> {
public:
    MultiStartPolarSweep(const Model& m, int trials, int passes, bool both)
        : m_(m), trials_(std::max(1, trials)), passes_(std::max(0, passes)), both_(both) {}

    Sol build(Rng& rng) override {
        const int n = m_.n;
        if (n <= 0) return Sol();
        if (order_.empty()) prepare();
        Sol best;
        double bestCost = std::numeric_limits<double>::infinity();
        const double cap = m_.capacity + 1e-9;
        for (int t = 0; t < trials_; ++t) {
            int start = rng.below(n);
            int dir = (both_ && rng.below(2) == 1) ? -1 : 1;
            Sol cur;
            std::vector<int> route;
            double load = 0.0;
            for (int s = 0; s < n; ++s) {
                int idx = ((start + dir * s) % n + n) % n;
                int c = order_[idx];
                double d = m_.demand[c];
                if (!route.empty() && load + d > cap) {
                    cur.push_back(route);
                    route.clear();
                    load = 0.0;
                }
                route.push_back(c);
                load += d;
            }
            if (!route.empty()) cur.push_back(route);
            double cost = 0.0;
            for (auto& r : cur) cost += improveRoute(r);
            if (cost < bestCost) { bestCost = cost; best = std::move(cur); }
        }
        return best;
    }

private:
    void prepare() {
        const int n = m_.n;
        std::vector<std::pair<double, int>> a;
        a.reserve(n);
        for (int c = 1; c <= n; ++c)
            a.push_back({std::atan2(m_.ys[c] - m_.ys[0], m_.xs[c] - m_.xs[0]), c});
        std::sort(a.begin(), a.end());
        order_.reserve(n);
        for (auto& p : a) order_.push_back(p.second);
    }

    // reorders route by nearest neighbor + 2-opt, returns its length
    double improveRoute(std::vector<int>& r) {
        const int L = (int)r.size();
        tour_.assign(L + 2, 0);
        used_.assign(L, 0);
        int last = 0;
        for (int p = 1; p <= L; ++p) {
            int bi = -1; double bd = std::numeric_limits<double>::infinity();
            for (int q = 0; q < L; ++q) if (!used_[q]) {
                double d = m_.dist(last, r[q]);
                if (d < bd) { bd = d; bi = q; }
            }
            used_[bi] = 1;
            tour_[p] = r[bi];
            last = r[bi];
        }
        for (int pass = 0; pass < passes_; ++pass) {
            bool improved = false;
            for (int i = 1; i < L; ++i) {
                for (int j = i + 1; j <= L; ++j) {
                    int a = tour_[i - 1], b = tour_[i], c = tour_[j], e = tour_[j + 1];
                    double delta = m_.dist(a, c) + m_.dist(b, e) - m_.dist(a, b) - m_.dist(c, e);
                    if (delta < -1e-10) {
                        std::reverse(tour_.begin() + i, tour_.begin() + j + 1);
                        improved = true;
                    }
                }
            }
            if (!improved) break;
        }
        double len = 0.0;
        for (int p = 0; p <= L; ++p) len += m_.dist(tour_[p], tour_[p + 1]);
        for (int p = 0; p < L; ++p) r[p] = tour_[p + 1];
        return len;
    }

    const Model& m_;
    int trials_, passes_;
    bool both_;
    std::vector<int> order_, tour_;
    std::vector<char> used_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<MultiStartPolarSweep>(
        model, (int)params.get("trials", 4), (int)params.get("two_opt_passes", 10),
        params.text("direction", "both") == "both");
}
