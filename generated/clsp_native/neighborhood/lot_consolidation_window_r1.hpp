// COMPONENT: {"name": "lot_consolidation_window", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [1, 10]}}}
class LotConsolidationWindow : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    LotConsolidationWindow(const Model& m, int L) : M(m), L_(std::max(1, L)) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const std::vector<int>& row = s[i];
            for (int a = 0; a < M.T; ++a) {
                int hi = std::min(M.T - 1, a + L_);
                bool anyOn = false;  // algún setup en (a, b]
                for (int b = a + 1; b <= hi; ++b) {
                    if (row[b]) anyOn = true;
                    if (!row[a] || anyOn) out.push_back(mk(i, a, b));
                }
            }
        }
        if (out.empty()) {  // T==1 o sin cambios posibles: alternar setups
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t) out.push_back(mk(i, t, t));
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        mod(r, m);
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        work_ = s;
        mod(work_, m);
        return M.objective(work_) - b;
    }

private:
    const Model& M;
    int L_;
    Sol last_, work_;
    double lastObj_ = 0.0;
    bool have_ = false;

    static Move mk(int i, int a, int b) { Move m{}; m[0] = i; m[1] = a; m[2] = b; return m; }
    static void mod(Sol& y, const Move& m) {
        int i = m[0], a = m[1], b = m[2];
        if (a == b) { y[i][a] = y[i][a] ? 0 : 1; return; }
        y[i][a] = 1;
        for (int t = a + 1; t <= b; ++t) y[i][t] = 0;
    }
    double base(const Sol& s) {
        if (!have_ || last_ != s) { last_ = s; lastObj_ = M.objective(s); have_ = true; }
        return lastObj_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)params.get("max_len", 4);
    return std::make_unique<LotConsolidationWindow>(model, L);
}
