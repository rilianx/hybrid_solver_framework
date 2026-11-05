// COMPONENT: {"name": "setup_time_shift_merge", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [0.5, 3.0]}, "max_shift": {"type": "int", "range": [1, 6]}, "early_prob": {"type": "float", "range": [0.2, 0.8]}, "merge_prob": {"type": "float", "range": [0.0, 0.6]}, "window": {"type": "int", "range": [2, 8]}}}

static Model::Solution stsm_fallback(const Model& m, const Model::Solution& s, Rng& rng) {
    const int n = m.n, T = m.T, N = n * T;
    Model::Solution y = s;
    if (N <= 0) return y;
    std::vector<int> order(N);
    std::iota(order.begin(), order.end(), 0);
    std::shuffle(order.begin(), order.end(), rng.g);
    for (int i = 0; i < n; ++i)
        for (int t = 0; t + 1 < T; ++t)
            if ((s[i][t] != 0) != (s[i][t + 1] != 0)) {
                std::swap(y[i][t], y[i][t + 1]);
                if (m.feasible(y)) return y;
                y[i][t] = s[i][t]; y[i][t + 1] = s[i][t + 1];
            }
    for (int idx : order) {
        int i = idx / T, t = idx % T;
        y[i][t] = y[i][t] ? 0 : 1;
        if (m.feasible(y)) return y;
        y[i][t] = s[i][t];
    }
    int c = order[0];
    y[c / T][c % T] = y[c / T][c % T] ? 0 : 1;
    return y;
}

class SetupShiftMerge : public hsf::Perturbation<Model> {
public:
    SetupShiftMerge(const Model& m, double mps, int ms, double ep, double mp, int win)
        : m_(m), mps_(mps), maxShift_(std::max(1, ms)), early_(ep), merge_(mp),
          window_(std::max(2, win)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 1) return stsm_fallback(m_, s, rng);
        int k = (int)std::lround(std::max(1.0, strength) * mps_);
        k = std::clamp(k, 1, std::max(1, n));
        for (int attempt = 0; attempt < 3; ++attempt) {
            Sol y = s;
            changes_.clear();
            groupEnd_.clear();
            for (int c = 0; c < k; ++c) {
                bool done = false;
                for (int tr = 0; tr < 20 && !done; ++tr) {
                    int i = rng.below(n);
                    int w = std::min(T, 2 + rng.below(window_ - 1));
                    int a = rng.below(T - w + 1);
                    ones_.clear();
                    for (int t = a; t < a + w; ++t) if (y[i][t]) ones_.push_back(t);
                    if (ones_.empty()) continue;
                    bool early = rng.uniform() < early_;
                    size_t before = changes_.size();
                    if (ones_.size() >= 2 && rng.uniform() < merge_) {
                        // consolidación: un solo setup absorbe los lotes de la ventana
                        int keep = early ? ones_.front() : ones_.back();
                        for (int t : ones_) if (t != keep) setCell(y, i, t, 0);
                    } else {
                        // desplazamiento en bloque de todos los setups de la ventana
                        int d = (early ? -1 : 1) * (1 + rng.below(maxShift_));
                        for (int t : ones_) setCell(y, i, t, 0);
                        for (int t : ones_) setCell(y, i, std::clamp(t + d, 0, T - 1), 1);
                    }
                    if (changes_.size() > before) {
                        groupEnd_.push_back(changes_.size());
                        done = true;
                    }
                }
            }
            if (groupEnd_.empty() || y == s) { k = std::min(std::max(1, n), k + 1); continue; }
            if (m_.feasible(y)) return y;
            // deshacer movimientos completos, del último al segundo
            for (int g = (int)groupEnd_.size() - 1; g >= 1; --g) {
                size_t lo = groupEnd_[g - 1];
                while (changes_.size() > lo) {
                    auto& ch = changes_.back();
                    y[ch[0]][ch[1]] = ch[2];
                    changes_.pop_back();
                }
                if (y != s && m_.feasible(y)) return y;
            }
            k = std::max(1, k / 2);
        }
        return stsm_fallback(m_, s, rng);
    }

private:
    void setCell(Sol& y, int i, int t, int v) {
        int old = (int)y[i][t];
        if ((old != 0) == (v != 0)) return;
        changes_.push_back({i, t, old});
        y[i][t] = v;
    }

    const Model& m_;
    double mps_;
    int maxShift_;
    double early_, merge_;
    int window_;
    std::vector<std::array<int, 3>> changes_;
    std::vector<size_t> groupEnd_;
    std::vector<int> ones_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mps = params.get("moves_per_strength", 1.0);
    int ms = (int)std::lround(params.get("max_shift", 2));
    double ep = params.get("early_prob", 0.5);
    double mp = params.get("merge_prob", 0.25);
    int win = (int)std::lround(params.get("window", 4));
    return std::make_unique<SetupShiftMerge>(model, mps, ms, ep, mp, win);
}
