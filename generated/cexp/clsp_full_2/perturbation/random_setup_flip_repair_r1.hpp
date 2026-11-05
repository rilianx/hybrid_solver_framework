// COMPONENT: {"name": "random_setup_flip_repair", "slot": "perturbation", "params": {"flip_scale": {"type": "float", "range": [0.5, 4.0]}, "add_bias": {"type": "float", "range": [0.0, 1.0]}, "cleanup": {"type": "int", "range": [0, 1]}}}
using Sol = Model::Solution;

class Repairer {
public:
    Repairer(const Model& m, double noise, bool clean) : m_(m), noise_(noise), clean_(clean) {}
    void finish(Sol& y, const Sol& s, Rng& rng) {
        bool ok = repair(y, rng);
        if (ok && clean_) cleanup(y);
        ensureDistinct(y, s, rng, ok);
    }
private:
    const Model& m_;
    double noise_;
    bool clean_;
    std::vector<int> cand_;

    double freeCap(int t) const { return m_.E[m_.srcEdge[t]].cap; }
    double unmet(int i, int t) const { int e = m_.sinkEdge[(size_t)i * m_.T + t]; return e < 0 ? 0.0 : m_.E[e].cap; }
    double prod(int i, int t) const { return m_.E[m_.prodEdge[i][t] + 1].cap; }

    bool repair(Sol& y, Rng& rng) {
        const int n = m_.n, T = m_.T;
        const int maxIter = 2 * n * T + 10;
        for (int it = 0; it < maxIter; ++it) {
            if (m_.feasible(y)) return true;
            int bt = -1, bi = -1;
            for (int t = 0; t < T && bt < 0; ++t) {
                int cnt = 0;
                for (int i = 0; i < n; ++i)
                    if (unmet(i, t) > 1e-9) { ++cnt; if (rng.below(cnt) == 0) bi = i; }
                if (cnt) bt = t;
            }
            if (bi < 0) return false;
            double need = unmet(bi, bt), sti = m_.st[bi];
            int fit = -1, best = -1; double bestSc = -1e300;
            cand_.clear();
            for (int p = bt; p >= 0; --p) {
                if (y[bi][p]) continue;
                double sc = freeCap(p) - sti;
                if (sc > 1e-9) cand_.push_back(p);
                if (fit < 0 && sc >= need - 1e-9 && sc > 1e-9) fit = p;
                if (sc > bestSc) { bestSc = sc; best = p; }
            }
            if (!cand_.empty()) {
                int p = (noise_ > 0 && rng.uniform() < noise_) ? cand_[rng.below((int)cand_.size())]
                                                              : (fit >= 0 ? fit : best);
                y[bi][p] = 1;
                continue;
            }
            bool removed = false;
            for (int p = 0; p <= bt; ++p)
                for (int i = 0; i < n; ++i)
                    if (y[i][p] && m_.st[i] > 0 && prod(i, p) <= 1e-10) { y[i][p] = 0; removed = true; }
            if (removed) continue;
            if (best >= 0) { y[bi][best] = 1; continue; }
            break;
        }
        return m_.feasible(y);
    }

    void cleanup(Sol& y) {
        if (!m_.feasible(y)) return;
        for (int i = 0; i < m_.n; ++i)
            for (int t = 0; t < m_.T; ++t)
                if (y[i][t] && prod(i, t) <= 1e-10) y[i][t] = 0;
    }

    void ensureDistinct(Sol& y, const Sol& s, Rng& rng, bool ok) {
        if (y != s) return;
        const int T = m_.T, N = m_.n * m_.T;
        if (ok && m_.feasible(y)) {
            cand_.clear();
            for (int i = 0; i < m_.n; ++i)
                for (int t = 0; t < T; ++t) {
                    if (!y[i][t]) { if (freeCap(t) >= m_.st[i] - 1e-12) cand_.push_back(i * T + t); }
                    else if (prod(i, t) <= 1e-10) cand_.push_back(i * T + t);
                }
            if (!cand_.empty()) {
                int c = cand_[rng.below((int)cand_.size())];
                int& v = y[c / T][c % T]; v = v ? 0 : 1;
                return;
            }
            for (int a = 0; a < 4 * N; ++a) {
                int c = rng.below(N);
                int& v = y[c / T][c % T]; int old = v; v = old ? 0 : 1;
                if (m_.feasible(y)) return;
                v = old;
            }
        }
        int c = rng.below(N);
        int& v = y[c / T][c % T]; v = v ? 0 : 1;
    }
};

class RandomSetupFlip : public hsf::Perturbation<Model> {
public:
    RandomSetupFlip(const Model& m, double scale, double addBias, bool clean)
        : m_(m), scale_(scale), addBias_(addBias), rep_(m, 0.0, clean) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol y = s;
        const int n = m_.n, T = m_.T, N = n * T;
        if (N == 0) return y;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * scale_));
        k = std::min(k, N);
        for (int c = 0; c < k; ++c) {
            bool wantZero = rng.uniform() < addBias_;  // flip a 0 -> 1 (add) or 1 -> 0 (remove)
            int cell = -1, r = 0;
            for (int tr = 0; tr < 16; ++tr) {
                r = rng.below(N);
                if ((y[r / T][r % T] == 0) == wantZero) { cell = r; break; }
            }
            if (cell < 0) cell = r;
            int& v = y[cell / T][cell % T]; v = v ? 0 : 1;
        }
        rep_.finish(y, s, rng);
        return y;
    }
private:
    const Model& m_;
    double scale_, addBias_;
    Repairer rep_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("flip_scale", 1.5);
    double bias = params.get("add_bias", 0.5);
    bool clean = params.get("cleanup", 1.0) >= 0.5;
    return std::make_unique<RandomSetupFlip>(model, scale, bias, clean);
}
