// COMPONENT: {"name": "single_setup_flip", "slot": "neighborhood", "params": {}}
class SingleSetupFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    explicit SingleSetupFlip(const Model& m) : M(m) {}

    // Intercambio de setup entre dos ítems en el mismo período:
    // mv = {i, j, t}, con i<j y s[i][t] != s[j][t]; se intercambian sus valores.
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int t = 0; t < M.P; ++t)
            for (int i = 0; i < M.n; ++i) {
                const bool vi = s[i][t] != 0;
                for (int j = i + 1; j < M.n; ++j) {
                    if ((s[j][t] != 0) == vi) continue;
                    Move mv{}; mv.fill(0); mv[0] = i; mv[1] = j; mv[2] = t;
                    out.push_back(mv);
                }
            }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        auto a = r[m[0]][m[2]];
        r[m[0]][m[2]] = r[m[1]][m[2]];
        r[m[1]][m[2]] = a;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        auto& ca = last_[m[0]][m[2]];
        auto& cb = last_[m[1]][m[2]];
        if ((ca != 0) == (cb != 0)) return 0.0;
        auto oa = ca, ob = cb;
        ca = ob; cb = oa;
        double v = M.objective(last_);
        ca = oa; cb = ob;
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
