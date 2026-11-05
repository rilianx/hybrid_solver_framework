// COMPONENT: {"name": "noisy_wagner_whitin_item_regen", "slot": "perturbation", "params": {"items_scale": {"type": "float", "range": [0.5, 3.0]}, "sigma": {"type": "float", "range": [0.0, 1.5]}, "load_penalty": {"type": "float", "range": [0.0, 2.0]}, "cleanup": {"type": "int", "range": [0, 1]}}}
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

class NoisyWWRegen : public hsf::Perturbation<Model> {
public:
    NoisyWWRegen(const Model& m, double is, double sigma, double lp, bool clean)
        : m_(m), itemsScale_(is), sigma_(sigma), loadPen_(lp), rep_(m, 0.0, clean) {
        load_.assign(m.T, 0.0);
        for (int t = 0; t < m.T; ++t) {
            double dem = 0.0;
            for (int i = 0; i < m.n; ++i) dem += m.d[i][t];
            load_[t] = m.cap[t] > 0 ? std::min(2.0, dem / m.cap[t]) : 2.0;
        }
        f_.resize(m.T + 1); pred_.resize(m.T + 1); S_.resize(m.T);
        perm_.resize(m.n);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol y = s;
        const int n = m_.n, T = m_.T;
        if (n == 0 || T == 0) return y;
        int k = (int)std::lround(std::max(1.0, strength) * itemsScale_);
        k = std::max(1, std::min(k, n));
        std::iota(perm_.begin(), perm_.end(), 0);
        for (int a = 0; a < k; ++a) {
            int b = a + rng.below(n - a);
            std::swap(perm_[a], perm_[b]);
            regenItem(perm_[a], y[perm_[a]], rng);
        }
        rep_.finish(y, s, rng);
        return y;
    }

private:
    const Model& m_;
    double itemsScale_, sigma_, loadPen_;
    Repairer rep_;
    std::vector<double> load_, f_, S_;
    std::vector<int> pred_, perm_;

    void regenItem(int i, std::vector<int>& row, Rng& rng) {
        const int T = m_.T;
        const std::vector<double>& d = m_.d[i];
        const double h = m_.h[i];
        for (int t = 0; t < T; ++t)
            S_[t] = m_.s[i] * std::exp(sigma_ * (2.0 * rng.uniform() - 1.0)) * (1.0 + loadPen_ * load_[t]);
        const double INF = 1e300;
        f_[0] = 0.0;
        for (int t = 1; t <= T; ++t) { f_[t] = INF; pred_[t] = -2; }
        for (int j = 0; j < T; ++j) {
            if (f_[j] >= INF) continue;
            if (d[j] <= 0 && f_[j] < f_[j + 1]) { f_[j + 1] = f_[j]; pred_[j + 1] = -1; }
            double base = f_[j] + S_[j], hold = 0.0;
            for (int t = j; t < T; ++t) {
                hold += h * (t - j) * d[t];
                double v = base + hold;
                if (v < f_[t + 1]) { f_[t + 1] = v; pred_[t + 1] = j; }
            }
        }
        std::fill(row.begin(), row.end(), 0);
        int t = T;
        while (t > 0) {
            int p = pred_[t];
            if (p == -1) { --t; }
            else if (p < 0) { break; }
            else { row[p] = 1; t = p; }
        }
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double is = params.get("items_scale", 1.0);
    double sigma = params.get("sigma", 0.5);
    double lp = params.get("load_penalty", 0.5);
    bool clean = params.get("cleanup", 1.0) >= 0.5;
    return std::make_unique<NoisyWWRegen>(model, is, sigma, lp, clean);
}
