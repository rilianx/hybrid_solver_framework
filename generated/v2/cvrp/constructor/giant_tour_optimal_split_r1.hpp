// COMPONENT: {"name": "giant_tour_optimal_split", "slot": "constructor", "params": {"rcl": {"type": "int", "range": [1, 5]}, "neighbors": {"type": "int", "range": [5, 40]}, "trials": {"type": "int", "range": [1, 8]}}}
class GiantTourOptimalSplit : public hsf::Constructor<Model> {
public:
    GiantTourOptimalSplit(const Model& m, int rcl, int k, int trials)
        : m_(m), rcl_(std::max(1, rcl)), k_(std::max(1, k)), trials_(std::max(1, trials)) {}

    Sol build(Rng& rng) override {
        const int n = m_.n;
        if (n <= 0) return Sol();
        if (nbr_.empty()) prepare();
        Sol best;
        double bestCost = std::numeric_limits<double>::infinity();
        for (int t = 0; t < trials_; ++t) {
            giantTour(rng);
            Sol s;
            double c = split(s);
            if (c < bestCost) { bestCost = c; best = std::move(s); }
        }
        return best;
    }

private:
    void prepare() {
        const int n = m_.n;
        nbr_.assign(n + 1, std::vector<int>());
        std::vector<std::pair<double, int>> cand;
        cand.reserve(n);
        for (int i = 0; i <= n; ++i) {
            cand.clear();
            for (int j = 1; j <= n; ++j) if (j != i) cand.push_back({m_.dist(i, j), j});
            int K = std::min<int>(k_, (int)cand.size());
            std::partial_sort(cand.begin(), cand.begin() + K, cand.end());
            nbr_[i].reserve(K);
            for (int q = 0; q < K; ++q) nbr_[i].push_back(cand[q].second);
        }
    }

    void giantTour(Rng& rng) {
        const int n = m_.n;
        tour_.assign(n + 1, 0);
        vis_.assign(n + 1, 0);
        int cur = 0;
        int pick[8];
        for (int p = 1; p <= n; ++p) {
            int cnt = 0;
            const int lim = std::min(rcl_, 8);
            for (int c : nbr_[cur]) {
                if (!vis_[c]) { pick[cnt++] = c; if (cnt >= lim) break; }
            }
            int nxt;
            if (cnt > 0) {
                nxt = pick[rng.below(cnt)];
            } else {
                nxt = -1;
                double bd = std::numeric_limits<double>::infinity();
                for (int c = 1; c <= n; ++c) if (!vis_[c]) {
                    double d = m_.dist(cur, c);
                    if (d < bd) { bd = d; nxt = c; }
                }
            }
            vis_[nxt] = 1;
            tour_[p] = nxt;
            cur = nxt;
        }
    }

    double split(Sol& out) {
        const int n = m_.n;
        const double INF = std::numeric_limits<double>::infinity();
        const double cap = m_.capacity + 1e-9;
        V_.assign(n + 1, INF);
        pred_.assign(n + 1, 0);
        V_[0] = 0.0;
        for (int i = 0; i < n; ++i) {
            if (V_[i] == INF) continue;
            double load = 0.0, cost = 0.0;
            for (int j = i + 1; j <= n; ++j) {
                int c = tour_[j];
                load += m_.demand[c];
                if (j == i + 1) {
                    cost = m_.dist(0, c) + m_.dist(c, 0);
                } else {
                    if (load > cap) break;
                    int b = tour_[j - 1];
                    cost += m_.dist(b, c) + m_.dist(c, 0) - m_.dist(b, 0);
                }
                if (V_[i] + cost < V_[j]) { V_[j] = V_[i] + cost; pred_[j] = i; }
                if (load > cap) break;  // oversized single customer: alone
            }
        }
        out.clear();
        int j = n;
        while (j > 0) {
            int i = pred_[j];
            out.emplace_back(tour_.begin() + i + 1, tour_.begin() + j + 1);
            j = i;
        }
        std::reverse(out.begin(), out.end());
        return V_[n];
    }

    const Model& m_;
    int rcl_, k_, trials_;
    std::vector<std::vector<int>> nbr_;
    std::vector<int> tour_, pred_;
    std::vector<char> vis_;
    std::vector<double> V_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<GiantTourOptimalSplit>(
        model, (int)params.get("rcl", 2), (int)params.get("neighbors", 15), (int)params.get("trials", 3));
}
