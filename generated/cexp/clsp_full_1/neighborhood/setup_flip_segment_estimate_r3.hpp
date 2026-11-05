// COMPONENT: {"name": "setup_flip_segment_estimate", "slot": "neighborhood", "params": {"est_penalty_scale": {"type": "float", "range": [0.1, 2.0]}, "seg_min": {"type": "int", "range": [2, 4]}, "seg_max": {"type": "int", "range": [3, 8]}}}
class CachedEvalF {
public:
    using Sol = Model::Solution;
    explicit CachedEvalF(const Model& m) : m_(m) {}
    double base(const Sol& s) {
        if (!valid_ || s != base_) { base_ = s; work_ = s; baseObj_ = m_.objective(s); valid_ = true; }
        return baseObj_;
    }
    double delta(const Sol& s, const std::vector<std::array<int, 3>>& ch) {
        double b = base(s);
        old_.resize(ch.size());
        for (size_t k = 0; k < ch.size(); ++k) { old_[k] = work_[ch[k][0]][ch[k][1]]; work_[ch[k][0]][ch[k][1]] = ch[k][2]; }
        double o = m_.objective(work_);
        for (size_t k = ch.size(); k-- > 0;) work_[ch[k][0]][ch[k][1]] = old_[k];
        return o - b;
    }
    static Sol apply(const Sol& s, const std::vector<std::array<int, 3>>& ch) {
        Sol r = s;
        for (auto& c : ch) r[c[0]][c[1]] = c[2];
        return r;
    }
private:
    const Model& m_;
    bool valid_ = false;
    Sol base_, work_;
    double baseObj_ = 0.0;
    std::vector<int> old_;
};

// Invierte un bloque contiguo y[i][a..a+L-1] (L en [segMin, segMax]): toca varias variables a la vez
class SetupSegmentFlip : public hsf::Neighborhood<Model> {
public:
    SetupSegmentFlip(const Model& m, double ps, int lmin, int lmax) : m_(m), ev_(m), ps_(ps) {
        int T = m.T;
        lmin_ = std::max(2, lmin);
        lmax_ = std::max(lmin_, lmax);
        lmax_ = std::min(lmax_, T);
        P_.assign(m.n, std::vector<double>(T + 1, 0.0));
        W_.assign(m.n, std::vector<double>(T + 1, 0.0));
        for (int i = 0; i < m.n; ++i)
            for (int t = 0; t < T; ++t) {
                double dt = (double)m.d[i][t];
                P_[i][t + 1] = P_[i][t] + dt;
                W_[i][t + 1] = W_[i][t] + dt * t;
            }
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        (void)s;
        int T = m_.T;
        if (lmin_ > lmax_) return;
        out.reserve(out.size() + (size_t)m_.n * T * (lmax_ - lmin_ + 1));
        for (int i = 0; i < m_.n; ++i)
            for (int a = 0; a < T; ++a)
                for (int L = lmin_; L <= lmax_ && a + L <= T; ++L) {
                    Move mv{}; mv[0] = i; mv[1] = a; mv[2] = L; out.push_back(mv);
                }
    }
    Sol apply(const Sol& s, const Move& m) override { build(s, m); return CachedEvalF::apply(s, ch_); }
    double delta(const Sol& s, const Move& m) override { build(s, m); return ev_.delta(s, ch_); }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override {
        int i = m[0], a = m[1], L = m[2], b = a + L - 1, T = m_.T;
        const std::vector<int>& yi = s[i];
        int p = a - 1; while (p >= 0 && !yi[p]) --p;
        if (p < 0) {
            // sin setup previo puede aparecer penalización por demanda no cubierta: delta exacto
            (void)ps_;
            return delta(s, m);
        }
        int q = b + 1; while (q < T && !yi[q]) ++q;
        double sc = (double)m_.s[i];
        double hi = (double)m_.h[i];
        const std::vector<double>& P = P_[i];
        const std::vector<double>& W = W_[i];
        auto hold = [&](int r, int e) { return hi * ((W[e] - W[r]) - r * (P[e] - P[r])); };
        auto cost = [&](bool flipped) {
            double c = sc;
            int r = p;
            for (int t = p + 1; t < q; ++t) {
                int bit = yi[t];
                if (flipped && t >= a && t <= b) bit = !bit;
                if (bit) { c += hold(r, t) + sc; r = t; }
            }
            return c + hold(r, q);
        };
        return cost(true) - cost(false);
    }
private:
    void build(const Sol& s, const Move& m) {
        ch_.clear();
        int i = m[0], a = m[1], L = m[2];
        for (int t = a; t < a + L; ++t) ch_.push_back({i, t, s[i][t] ? 0 : 1});
    }
    const Model& m_;
    CachedEvalF ev_;
    double ps_;
    int lmin_ = 3, lmax_ = 6;
    std::vector<std::vector<double>> P_, W_;
    std::vector<std::array<int, 3>> ch_;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("est_penalty_scale", 1.0);
    int lmin = (int)params.get("seg_min", 3);
    int lmax = (int)params.get("seg_max", 6);
    return std::make_unique<SetupSegmentFlip>(model, ps, lmin, lmax);
}
