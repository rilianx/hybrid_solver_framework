// COMPONENT: {"name": "lot_shift_merge_split", "slot": "perturbation", "params": {"ops_per_strength": {"type": "float", "range": [0.5, 3.0]}, "p_shift": {"type": "float", "range": [0.2, 0.8]}, "shift_max": {"type": "int", "range": [1, 3]}, "repair_iters": {"type": "int", "range": [5, 80]}, "latest_bias": {"type": "float", "range": [0.3, 1.0]}}}
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

class LotShiftMergeSplit : public hsf::Perturbation<Model> {
public:
    LotShiftMergeSplit(const Model& m, double ops, double ps, int sm, int ri, double lb)
        : m_(m), fx_(m), ops_(ops), ps_(ps), sm_(sm), ri_(ri), lb_(lb) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        if (n <= 0 || T <= 0) return s;
        Sol y = s;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * ops_));
        k = std::min(k, 4 * n * T);
        for (int op = 0; op < k; ++op) {
            int i = rng.below(n);
            std::vector<int>& yi = y[i];
            sp_.clear();
            for (int t = 0; t < T; ++t) if (yi[t]) sp_.push_back(t);
            if (sp_.empty()) {
                int t0 = 0;
                while (t0 < T && m_.d[i][t0] <= 0) ++t0;
                yi[t0 < T ? t0 : rng.below(T)] = 1;
                continue;
            }
            int pos = rng.below((int)sp_.size());
            int t = sp_[pos];
            double r = rng.uniform();
            if (r < ps_) {
                int dist = 1 + rng.below(std::max(1, sm_));
                int nt = t + (rng.uniform() < 0.5 ? -dist : dist);
                if (nt >= 0 && nt < T && !yi[nt]) { yi[t] = 0; yi[nt] = 1; }
            } else if (r < ps_ + 0.5 * (1.0 - ps_)) {
                // merge: drop this lot into the previous one, or merge next into this if first
                if (pos > 0) yi[t] = 0;
                else if (pos + 1 < (int)sp_.size()) yi[sp_[pos + 1]] = 0;
            } else {
                int nx = (pos + 1 < (int)sp_.size()) ? sp_[pos + 1] : T;
                if (nx - t >= 2) yi[t + 1 + rng.below(nx - t - 1)] = 1;
                else if (t > 0 && !yi[t - 1]) yi[t - 1] = 1;
            }
        }
        if (y == s) { int i = rng.below(n), t = rng.below(T); y[i][t] = !y[i][t]; }
        if (fx_.repair(y, rng, ri_, lb_) && y != s) return y;
        return fx_.fallback(s, rng);
    }
private:
    const Model& m_;
    Fixer fx_;
    double ops_, ps_;
    int sm_, ri_;
    double lb_;
    std::vector<int> sp_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ops = params.get("ops_per_strength", 1.5);
    double ps = params.get("p_shift", 0.5);
    int sm = (int)params.get("shift_max", 2);
    int ri = (int)params.get("repair_iters", 30);
    double lb = params.get("latest_bias", 0.7);
    return std::make_unique<LotShiftMergeSplit>(model, ops, ps, sm, ri, lb);
}
