// COMPONENT: {"name": "feasible_setup_shift_chain", "slot": "perturbation", "params": {"shifts_per_strength": {"type": "float", "range": [0.5, 3.0]}, "max_dist": {"type": "int", "range": [1, 3]}, "prefer_earlier": {"type": "float", "range": [0.3, 0.9]}}}
using Sol = Model::Solution;

class SetupShiftChain : public hsf::Perturbation<Model> {
public:
    SetupShiftChain(const Model& m, double sps, int md, double pe) : m_(m), sps_(sps), maxDist_(std::max(1, md)), preferEarlier_(pe) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        if (n <= 0 || T <= 0) return y;
        int k = std::max(1, (int)std::lround(sps_ * std::max(1.0, strength)));
        int accepted = 0;
        int attempts = 0, maxAttempts = 4 * k + 8;
        while (accepted < k && attempts < maxAttempts) {
            ++attempts;
            if (T < 2) break;
            int i = rng.below(n);
            setups_.clear();
            for (int t = 0; t < T; ++t) if (y[i][t]) setups_.push_back(t);
            if (setups_.empty()) continue;
            int t = setups_[rng.below((int)setups_.size())];
            int dist = 1 + rng.below(maxDist_);
            int t2 = (rng.uniform() < preferEarlier_) ? t - dist : t + dist;
            if (t2 < 0 || t2 >= T) t2 = (t2 < 0) ? t + dist : t - dist;
            if (t2 < 0 || t2 >= T || y[i][t2]) continue;
            y[i][t] = 0; y[i][t2] = 1;
            if (m_.feasible(y)) ++accepted;
            else { y[i][t] = 1; y[i][t2] = 0; }
        }
        if (accepted == 0 || y == s) return fallback(s, rng);
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
    double sps_;
    int maxDist_;
    double preferEarlier_;
    std::vector<int> setups_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sps = params.get("shifts_per_strength", 1.5);
    int md = (int)params.get("max_dist", 2);
    double pe = params.get("prefer_earlier", 0.6);
    return std::make_unique<SetupShiftChain>(model, sps, md, pe);
}
