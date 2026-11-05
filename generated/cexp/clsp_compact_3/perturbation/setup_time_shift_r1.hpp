// COMPONENT: {"name": "setup_time_shift", "slot": "perturbation", "params": {"shift_rate": {"type": "float", "range": [0.5, 3.0]}, "backward_prob": {"type": "float", "range": [0.3, 0.9]}, "max_dist": {"type": "int", "range": [1, 4]}, "max_tries": {"type": "int", "range": [3, 30]}}}
using Sol = Model::Solution;

static Sol fallbackPerturbC(const Model& m, const Sol& s, Rng& rng) {
    int n = (int)s.size(), T = n ? (int)s[0].size() : 0, N = n * T;
    if (N > 0) {
        Sol c = s;
        int off = rng.below(N);
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            if (t + 1 < T && c[i][t] != c[i][t + 1]) {
                std::swap(c[i][t], c[i][t + 1]);
                if (m.feasible(c)) return c;
                std::swap(c[i][t], c[i][t + 1]);
            }
        }
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            int old = c[i][t];
            c[i][t] = old ? 0 : 1;
            if (m.feasible(c)) return c;
            c[i][t] = old;
        }
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    if (N > 0) { Sol c = s; c[0][0] = c[0][0] ? 0 : 1; return c; }
    return s;
}

class SetupTimeShift : public hsf::Perturbation<Model> {
public:
    SetupTimeShift(const Model& m, double sr, double bp, int md, int mt)
        : m_(m), shiftRate_(sr), backProb_(bp), maxDist_(std::max(1, md)), maxTries_(std::max(1, mt)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = (int)s.size(), T = n ? (int)s[0].size() : 0;
        if (n == 0 || T < 2) return fallbackPerturbC(m_, s, rng);
        base_.clear();
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < T; ++t) if (s[i][t]) base_.push_back(i * T + t);
        if (base_.empty()) return fallbackPerturbC(m_, s, rng);
        int k = std::max(1, (int)std::ceil(std::max(1.0, strength) * shiftRate_));
        for (int tr = 0; tr < maxTries_; ++tr) {
            Sol c = s;
            ones_ = base_;
            int moved = 0, attempts = 0, limit = 4 * k + 8;
            while (moved < k && attempts < limit) {
                ++attempts;
                int r = rng.below((int)ones_.size());
                int i = ones_[r] / T, t = ones_[r] % T;
                int dir = rng.uniform() < backProb_ ? -1 : 1;
                int dist = 1 + rng.below(maxDist_);
                int t2 = t + dir * dist;
                if (t2 < 0 || t2 >= T) t2 = t - dir * dist;
                if (t2 < 0 || t2 >= T || c[i][t2]) continue;
                c[i][t] = 0;
                c[i][t2] = 1;
                ones_[r] = i * T + t2;
                ++moved;
            }
            if (moved > 0 && c != s && m_.feasible(c)) return c;
            k = std::max(1, (k * 2) / 3);
        }
        return fallbackPerturbC(m_, s, rng);
    }

private:
    const Model& m_;
    double shiftRate_, backProb_;
    int maxDist_, maxTries_;
    std::vector<int> base_, ones_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<SetupTimeShift>(model, params.get("shift_rate", 1.5),
        params.get("backward_prob", 0.6), (int)params.get("max_dist", 2), (int)params.get("max_tries", 10));
}
