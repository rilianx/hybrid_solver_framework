// COMPONENT: {"name": "setup_block_assign", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 8]}}}
class SetupBlockAssign : public hsf::Neighborhood<Model> {
    const Model& M;
    int L;
    Sol base, tmp;
    double baseVal = 0.0;
    bool valid = false;
    double objOf(const Sol& s) {
        if (!valid || s != base) { base = s; baseVal = M.objective(s); valid = true; }
        return baseVal;
    }
    static void applyIn(Sol& r, const Move& m) {
        int v = m[0] ? 1 : 0;
        std::vector<int>& row = r[m[1]];
        for (int t = m[2]; t <= m[3]; ++t) row[t] = v;
    }
public:
    SetupBlockAssign(const Model& m, int l) : M(m), L(std::max(2, l)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int a = 0; a < T; ++a) {
                int v = s[i][a] ? 0 : 1;  // the endpoint a must change
                int bmax = std::min(T - 1, a + L - 1);
                for (int b = a + 1; b <= bmax; ++b) {
                    if ((s[i][b] ? 1 : 0) == v) continue;  // endpoint b must change
                    Move m{}; m[0] = v; m[1] = i; m[2] = a; m[3] = b;
                    out.push_back(m);
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < (int)s[i].size(); ++t) {
                    Move m{}; m[0] = s[i][t] ? 0 : 1; m[1] = i; m[2] = t; m[3] = t;
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
        Move k = m;
        k[0] = m[0] ? 0 : 1;
        return k;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int l = (int)params.get("max_len", 4);
    return std::make_unique<SetupBlockAssign>(model, l);
}
