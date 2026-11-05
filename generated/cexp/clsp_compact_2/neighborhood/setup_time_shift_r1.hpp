// COMPONENT: {"name": "setup_time_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 12]}}}
class SetupTimeShift : public hsf::Neighborhood<Model> {
    const Model& M;
    int W;
    Sol base, tmp;
    double baseVal = 0.0;
    bool valid = false;
    double objOf(const Sol& s) {
        if (!valid || s != base) { base = s; baseVal = M.objective(s); valid = true; }
        return baseVal;
    }
    static void applyIn(Sol& r, const Move& m) {
        if (m[0] == 1) { r[m[1]][m[2]] = 0; r[m[1]][m[3]] = 1; }
        else { r[m[1]][m[2]] = r[m[1]][m[2]] ? 0 : 1; }
    }
public:
    SetupTimeShift(const Model& m, int w) : M(m), W(std::max(1, w)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                if (!s[i][t]) continue;
                int lo = std::max(0, t - W), hi = std::min(T - 1, t + W);
                for (int t2 = lo; t2 <= hi; ++t2) {
                    if (t2 == t || s[i][t2]) continue;
                    Move m{}; m[0] = 1; m[1] = i; m[2] = t; m[3] = t2;
                    out.push_back(m);
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < (int)s[i].size(); ++t) {
                    Move m{}; m[0] = 2; m[1] = i; m[2] = t;
                    out.push_back(m);
                }
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        applyIn(r, m);
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = objOf(s);
        tmp = s;
        applyIn(tmp, m);
        return M.objective(tmp) - b;
    }
    Move tabu_key(const Move& m) override {
        if (m[0] != 1) return m;
        Move k{}; k[0] = 1; k[1] = m[1]; k[2] = m[3]; k[3] = m[2];
        return k;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    return std::make_unique<SetupTimeShift>(model, w);
}
