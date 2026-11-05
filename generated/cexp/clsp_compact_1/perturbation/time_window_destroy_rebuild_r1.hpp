// COMPONENT: {"name": "time_window_destroy_rebuild", "slot": "perturbation", "params": {"window_frac": {"type": "float", "range": [0.1, 0.5]}, "item_frac": {"type": "float", "range": [0.2, 1.0]}, "rebuild_prob": {"type": "float", "range": [0.2, 0.9]}}}
using Sol = Model::Solution;

class WindowDestroyRebuild : public hsf::Perturbation<Model> {
public:
    WindowDestroyRebuild(const Model& m, double wf, double itf, double rp) : m_(m), wf_(wf), itf_(itf), rp_(rp) {
        firstDem_.assign(m.n, -1);
        for (int i = 0; i < m.n; ++i)
            for (int t = 0; t < m.T; ++t)
                if (m.d[i][t] > Model::EPS) { firstDem_[i] = t; break; }
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        const int n = m_.n, T = m_.T;
        Sol y = s;
        if (n <= 0 || T <= 0) return y;
        double str = std::max(1.0, strength);
        int w = std::max(1, (int)std::lround(wf_ * T)) + (int)std::lround(str) - 1;
        w = std::min(w, T);
        int a = rng.below(T - w + 1);
        int b = a + w;
        int mi = std::min(n, std::max(1, (int)std::lround(itf_ * n * std::sqrt(str))));
        items_.resize(n);
        std::iota(items_.begin(), items_.end(), 0);
        for (int q = 0; q < mi; ++q) { int r = q + rng.below(n - q); std::swap(items_[q], items_[r]); }
        for (int q = 0; q < mi; ++q) {
            int i = items_[q];
            for (int t = a; t < b; ++t)
                y[i][t] = (m_.d[i][t] > Model::EPS && rng.uniform() < rp_) ? 1 : 0;
            int tf = firstDem_[i];
            if (tf >= 0) {
                bool has = false;
                for (int t = 0; t <= tf; ++t) if (y[i][t]) { has = true; break; }
                if (!has) y[i][tf] = 1;
            }
        }
        if (y == s) {  // force a change inside the window
            int i = items_[rng.below(mi)];
            int t = a + rng.below(w);
            y[i][t] = 1 - (y[i][t] ? 1 : 0);
        }
        if (!m_.feasible(y)) {
            diffs_.clear();
            std::vector<int> adds;
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t)
                    if ((y[i][t] != 0) != (s[i][t] != 0)) {
                        if (s[i][t]) diffs_.push_back(i * T + t); else adds.push_back(i * T + t);
                    }
            std::shuffle(diffs_.begin(), diffs_.end(), rng.g);
            std::shuffle(adds.begin(), adds.end(), rng.g);
            diffs_.insert(diffs_.end(), adds.begin(), adds.end());  // re-add lost setups first
            int D = (int)diffs_.size();
            int chunk = std::max(1, D / 6);
            bool ok = false;
            int pos = 0;
            while (pos < D - 1) {
                int end = std::min(D - 1, pos + chunk);  // never revert the last diff
                for (; pos < end; ++pos) { int c = diffs_[pos]; y[c / T][c % T] = s[c / T][c % T]; }
                if (m_.feasible(y)) { ok = true; break; }
            }
            if (!ok) return fallback(s, rng);
        }
        if (y == s) return fallback(s, rng);
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
    double wf_, itf_, rp_;
    std::vector<int> firstDem_, items_, diffs_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double wf = params.get("window_frac", 0.25);
    double itf = params.get("item_frac", 0.5);
    double rp = params.get("rebuild_prob", 0.5);
    return std::make_unique<WindowDestroyRebuild>(model, wf, itf, rp);
}
