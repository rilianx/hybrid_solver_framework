// COMPONENT: {"name": "period_window_ruin_recreate", "slot": "perturbation", "params": {"win_scale": {"type": "float", "range": [1.0, 5.0]}, "item_frac": {"type": "float", "range": [0.5, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.6]}, "cleanup": {"type": "int", "range": [0, 1]}, "mode": {"type": "cat", "values": ["consolidate", "shift", "merge", "mixed"]}, "back_bias": {"type": "float", "range": [0.5, 1.0]}}}
using Sol = Model::Solution;

class Repairer {
public:
    Repairer(const Model& m, double noise, bool clean) : m_(m), noise_(noise), clean_(clean) {}
    // lo..hi: banda de periodos donde se permite la limpieza (mantiene el cambio concentrado)
    void finish(Sol& y, const Sol& s, Rng& rng, int lo, int hi) {
        bool ok = repair(y, rng);
        if (ok && clean_) cleanup(y, lo, hi);
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

    void cleanup(Sol& y, int lo, int hi) {
        if (!m_.feasible(y)) return;
        for (int i = 0; i < m_.n; ++i)
            for (int t = lo; t <= hi; ++t)
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

class WindowRuinRecreate : public hsf::Perturbation<Model> {
public:
    WindowRuinRecreate(const Model& m, double ws, double frac, double noise, bool clean, int mode, double backBias)
        : m_(m), winScale_(ws), itemFrac_(frac), mode_(mode), backBias_(backBias), rep_(m, noise, clean) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol y = s;
        const int n = m_.n, T = m_.T;
        if (n == 0 || T == 0) return y;
        int L = (int)std::lround(std::max(1.0, strength) * winScale_) + 2;
        L = std::max(std::min(3, T), std::min(L, T));
        int start = 0, bestCnt = -1;
        for (int tr = 0; tr < 4; ++tr) {
            int s0 = rng.below(T - L + 1), cnt = 0;
            for (int i = 0; i < n; ++i)
                for (int t = s0; t < s0 + L; ++t) cnt += y[i][t] ? 1 : 0;
            if (cnt > bestCnt) { bestCnt = cnt; start = s0; }
        }
        if (bestCnt > 0) {
            items_.clear();
            for (int i = 0; i < n; ++i)
                for (int t = start; t < start + L; ++t)
                    if (y[i][t]) { items_.push_back(i); break; }
            // bloque: una fracción fija (alta) de los ítems activos de la ventana, todos a la vez
            int k = (int)std::lround(itemFrac_ * (double)items_.size());
            k = std::max(1, std::min(k, (int)items_.size()));
            for (int a = 0; a < k; ++a) {
                int b = a + rng.below((int)items_.size() - a);
                std::swap(items_[a], items_[b]);
            }
            int mode = (mode_ == 3) ? rng.below(3) : mode_;
            if (mode == 2) {
                // merge: todos los lotes de la ventana se funden en un periodo común
                int q = (rng.uniform() < backBias_) ? start : start + rng.below(L);
                for (int a = 0; a < k; ++a) {
                    int i = items_[a];
                    for (int t = start; t < start + L; ++t) y[i][t] = 0;
                    y[i][q] = 1;
                }
            } else if (mode == 1) {
                // shift: el bloque completo se desplaza un periodo en la misma dirección
                int d = (rng.uniform() < backBias_) ? -1 : 1;
                for (int a = 0; a < k; ++a) shiftItem(y, items_[a], start, L, d);
            } else {
                for (int a = 0; a < k; ++a) consolidateItem(y, items_[a], start, L);
            }
        }
        int lo = std::max(0, start - 1), hi = std::min(T - 1, start + L);
        rep_.finish(y, s, rng, lo, hi);
        return y;
    }
private:
    // consolidate: un único lote por ítem al inicio de la ventana (o justo al lado)
    void consolidateItem(Sol& y, int i, int start, int L) {
        const int T = m_.T;
        pos_.clear();
        for (int t = start; t < start + L; ++t)
            if (y[i][t]) { pos_.push_back(t); y[i][t] = 0; }
        if (pos_.empty()) return;
        int q = start;
        if (pos_.size() == 1 && pos_[0] == start) {
            if (start > 0) q = start - 1;
            else if (start + 1 < T) q = start + 1;
        }
        y[i][q] = 1;
    }

    void shiftItem(Sol& y, int i, int start, int L, int d) {
        const int T = m_.T;
        pos_.clear();
        for (int t = start; t < start + L; ++t)
            if (y[i][t]) { pos_.push_back(t); y[i][t] = 0; }
        for (int p : pos_) {
            int q = p + d;
            if (q < 0 || q >= T) q = p - d;
            if (q >= 0 && q < T) y[i][q] = 1;
        }
    }

    const Model& m_;
    double winScale_, itemFrac_;
    int mode_;
    double backBias_;
    Repairer rep_;
    std::vector<int> items_;
    std::vector<int> pos_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ws = params.get("win_scale", 2.5);
    double frac = params.get("item_frac", 0.85);
    double noise = params.get("noise", 0.2);
    bool clean = params.get("cleanup", 1.0) >= 0.5;
    std::string ms = params.text("mode", "mixed");
    int mode = (ms == "consolidate") ? 0 : (ms == "shift") ? 1 : (ms == "merge") ? 2 : 3;
    double bb = params.get("back_bias", 0.7);
    frac = std::max(0.5, std::min(1.0, frac));
    ws = std::max(1.0, ws);
    return std::make_unique<WindowRuinRecreate>(model, ws, frac, noise, clean, mode, bb);
}
