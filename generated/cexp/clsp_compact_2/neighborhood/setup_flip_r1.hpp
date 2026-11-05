// COMPONENT: {"name": "setup_flip", "slot": "neighborhood", "params": {}}
class SetupFlip : public hsf::Neighborhood<Model> {
    const Model& M;
    Sol base, tmp;
    double baseVal = 0.0;
    bool valid = false;
    double objOf(const Sol& s) {
        if (!valid || s != base) { base = s; baseVal = M.objective(s); valid = true; }
        return baseVal;
    }
public:
    explicit SetupFlip(const Model& m) : M(m) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                Move m{}; m[0] = 0; m[1] = i; m[2] = t;
                out.push_back(m);
            }
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[1]][m[2]] = r[m[1]][m[2]] ? 0 : 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = objOf(s);
        tmp = s;
        tmp[m[1]][m[2]] = tmp[m[1]][m[2]] ? 0 : 1;
        return M.objective(tmp) - b;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    (void)params;
    return std::make_unique<SetupFlip>(model);
}
