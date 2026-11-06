// COMPONENT: {"name": "single_setup_flip", "slot": "neighborhood", "params": {}}
class SingleSetupFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    explicit SingleSetupFlip(const Model& m) : M(m) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        out.reserve(out.size() + (size_t)M.n * (size_t)M.P);
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
        auto& cell = last_[m[0]][m[1]];
        auto old = cell;
        cell = old ? 0 : 1;
        double v = M.objective(last_);
        cell = old;
        return v - base;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override { return delta(s, m); }

private:
    const Model& M;
    Sol last_;
    double lastVal_ = 0.0;
    bool valid_ = false;
    double baseObj(const Sol& s) {
        if (valid_ && s == last_) return lastVal_;
        last_ = s; lastVal_ = M.objective(s); valid_ = true;
        return lastVal_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    (void)params;
    return std::make_unique<SingleSetupFlip>(model);
}
