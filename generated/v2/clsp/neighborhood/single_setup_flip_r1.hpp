// COMPONENT: {"name": "single_setup_flip", "slot": "neighborhood", "params": {"est_hold_weight": {"type": "float", "range": [0.5, 2.0]}}}
class SingleSetupFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SingleSetupFlip(const Model& m, double w) : M(m), w_(w) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.P; ++t) {
                Move mv{}; mv.fill(0); mv[0] = i; mv[1] = t;
                out.push_back(mv);
            }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        work_ = s;
        work_[m[0]][m[1]] = work_[m[0]][m[1]] ? 0 : 1;
        return M.objective(work_) - base;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override {
        int i = m[0], t = m[1];
        const auto& row = s[i];
        int prev = -1;
        for (int u = t - 1; u >= 0; --u) if (row[u]) { prev = u; break; }
        int next = M.P;
        for (int u = t + 1; u < M.P; ++u) if (row[u]) { next = u; break; }
        double D = 0.0;
        for (int u = t; u < next; ++u) D += M.d[i][u];
        double lotCost = (prev >= 0) ? w_ * M.h[i] * D * (double)(t - prev) : M.penalty * D;
        if (row[t]) return -M.s[i] + lotCost;
        return M.s[i] - lotCost;
    }

private:
    const Model& M;
    double w_;
    Sol work_, last_;
    double lastVal_ = 0.0;
    bool valid_ = false;
    double baseObj(const Sol& s) {
        if (valid_ && s == last_) return lastVal_;
        last_ = s; lastVal_ = M.objective(s); valid_ = true;
        return lastVal_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double w = params.get("est_hold_weight", 1.0);
    return std::make_unique<SingleSetupFlip>(model, w);
}
