// COMPONENT: {"name": "setup_time_shift_merge", "slot": "perturbation", "params": {"moves_per_strength": {"type": "float", "range": [0.5, 3.0]}, "max_shift": {"type": "int", "range": [1, 6]}, "early_prob": {"type": "float", "range": [0.2, 0.8]}, "merge_prob": {"type": "float", "range": [0.0, 0.6]}}}

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
    SetupShiftMerge(const Model& m, double mps, int ms, double ep, double mp)
        : m_(m), mps_(mps), maxShift_(std::max(1, ms)), early_(ep), merge_(mp) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 1) return stsm_fallback(m_, s, rng);
        int k = (int)std::lround(std::max(1.0, strength) * mps_);
        k = std::clamp(k, 1, n * T);
        for (int attempt = 0; attempt < 3; ++attempt) {
            Sol y = s;
            moves_.clear();
            for (int c = 0; c < k; ++c) {
                bool done = false;
                for (int tr = 0; tr < 20 && !done; ++tr) {
                    int i = rng.below(n);
                    ones_.clear();
                    for (int t = 0; t < T; ++t) if (y[i][t]) ones_.push_back(t);
                    if (ones_.empty()) continue;
                    int t = ones_[rng.below((int)ones_.size())];
                    int dist = 1 + rng.below(maxShift_);
                    int dir = rng.uniform() < early_ ? -1 : 1;
                    for (int side = 0; side < 2 && !done; ++side, dir = -dir) {
                        int t2 = t + dir * dist;
                        if (t2 < 0) t2 = 0;
                        if (t2 >= T) t2 = T - 1;
                        if (t2 == t) continue;
                        if (!y[i][t2]) {
                            y[i][t] = 0; y[i][t2] = 1;
                            moves_.push_back({i, t, t2});
                            done = true;
                        } else if (rng.uniform() < merge_) {
                            y[i][t] = 0;
                            moves_.push_back({i, t, -1});
                            done = true;
                        }
                    }
                }
            }
            if (moves_.empty() || y == s) { k = std::min(n * T, k + 1); continue; }
            if (m_.feasible(y)) return y;
            for (int u = (int)moves_.size() - 1; u >= 1; --u) {
                auto& mv = moves_[u];
                y[mv[0]][mv[1]] = 1;
                if (mv[2] >= 0) y[mv[0]][mv[2]] = 0;
                if (y != s && m_.feasible(y)) return y;
            }
            k = std::max(1, k / 2);
        }
        return stsm_fallback(m_, s, rng);
    }

private:
    const Model& m_;
    double mps_;
    int maxShift_;
    double early_, merge_;
    std::vector<std::array<int, 3>> moves_;
    std::vector<int> ones_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double mps = params.get("moves_per_strength", 1.0);
    int ms = (int)std::lround(params.get("max_shift", 2));
    double ep = params.get("early_prob", 0.5);
    double mp = params.get("merge_prob", 0.25);
    return std::make_unique<SetupShiftMerge>(model, mps, ms, ep, mp);
}
