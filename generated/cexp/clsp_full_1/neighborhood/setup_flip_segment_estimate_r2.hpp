// COMPONENT: {"name": "setup_flip_segment_estimate", "slot": "neighborhood", "params": {"est_penalty_scale": {"type": "float", "range": [0.1, 2.0]}}}
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

class SetupFlip : public hsf::Neighborhood<Model> {
public:
    SetupFlip(const Model& m, double ps) : m_(m), ev_(m), ps_(ps) {
        pre_.assign(m.n, std::vector<double>(m.T + 1, 0.0));
        for (int i = 0; i < m.n; ++i)
            for (int t = 0; t < m.T; ++t) pre_[i][t + 1] = pre_[i][t] + m.d[i][t];
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        (void)s;
        out.reserve(out.size() + (size_t)m_.n * m_.T);
        for (int i = 0; i < m_.n; ++i)
            for (int t = 0; t < m_.T; ++t) { Move mv{}; mv[0] = i; mv[1] = t; out.push_back(mv); }
    }
    Sol apply(const Sol& s, const Move& m) override { build(s, m); return CachedEvalF::apply(s, ch_); }
    double delta(const Sol& s, const Move& m) override { build(s, m); return ev_.delta(s, ch_); }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override {
        int i = m[0], t = m[1], T = m_.T;
        const std::vector<int>& yi = s[i];
        int p = t - 1; while (p >= 0 && !yi[p]) --p;
        int q = t + 1; while (q < T && !yi[q]) ++q;
        if (p < 0) {
            // sin setup previo la penalización domina y la fórmula barata la sobrestima: delta exacto
            (void)ps_;
            return delta(s, m);
        }
        double D = pre_[i][q] - pre_[i][t];
        double mv = m_.h[i] * (t - p) * D;
        if (yi[t]) return -m_.s[i] + mv;
        return m_.s[i] - mv;
    }
private:
    void build(const Sol& s, const Move& m) {
        ch_.clear();
        ch_.push_back({m[0], m[1], s[m[0]][m[1]] ? 0 : 1});
    }
    const Model& m_;
    CachedEvalF ev_;
    double ps_;
    std::vector<std::vector<double>> pre_;
    std::vector<std::array<int, 3>> ch_;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("est_penalty_scale", 1.0);
    return std::make_unique<SetupFlip>(model, ps);
}
