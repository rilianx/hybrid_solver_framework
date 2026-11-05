// COMPONENT: {"name": "setup_bit_flip", "slot": "neighborhood", "params": {}}
class SetupBitFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    explicit SetupBitFlip(const Model& m) : M(m) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) out.push_back(Move{i, t, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        Sol r = apply(s, m);
        return M.objective(r) - b;
    }
    bool has_estimate() const override { return false; }
    double estimate(const Sol& s, const Move& m) override { return delta(s, m); }

private:
    const Model& M;
    Sol cS;
    double cObj = 0.0;
    bool cValid = false;

    double base(const Sol& s) {
        if (!cValid || s != cS) { cS = s; cObj = M.objective(s); cValid = true; }
        return cObj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    (void)params;
    return std::make_unique<SetupBitFlip>(model);
}
