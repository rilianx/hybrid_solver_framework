// COMPONENT: {"name": "setup_flip_single", "slot": "neighborhood", "params": {}}
class SetupFlipSingle : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    explicit SetupFlipSingle(const Model& m) : M(m) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < (int)s.size(); ++i)
            for (int t = 0; t < (int)s[i].size(); ++t)
                out.push_back(Move{i, t, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        mutate(r, m);
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        work = s;
        mutate(work, m);
        return M.objective(work) - b;
    }

private:
    const Model& M;
    Sol cached, work;
    double cachedVal = 0.0;
    bool valid = false;

    static void mutate(Sol& r, const Move& m) { r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1; }
    double base(const Sol& s) {
        if (!valid || s != cached) { cached = s; cachedVal = M.objective(s); valid = true; }
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    (void)params;
    return std::make_unique<SetupFlipSingle>(model);
}
