// COMPONENT: {"name": "setup_transfer_within_item", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 8]}}}
class SetupTransferWithinItem : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupTransferWithinItem(const Model& m, int w) : M(m), W(std::max(1, w)) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) {
                if (!s[i][t]) continue;
                int lo = std::max(0, t - W), hi = std::min(M.T - 1, t + W);
                for (int u = lo; u <= hi; ++u)
                    if (u != t) out.push_back(mk(i, t, u));
            }
        if (out.empty()) {  // sin setups (o T==1): abrir/alternar setups
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

    Move tabu_key(const Move& m) override { return mk(m[0], m[2], m[1]); }

private:
    const Model& M;
    int W;
    Sol last_, work_;
    double lastObj_ = 0.0;
    bool have_ = false;

    static Move mk(int i, int t, int u) { Move m{}; m[0] = i; m[1] = t; m[2] = u; return m; }
    static void mod(Sol& y, const Move& m) {
        int i = m[0], t = m[1], u = m[2];
        if (t == u) { y[i][t] = y[i][t] ? 0 : 1; return; }
        y[i][t] = 0;
        y[i][u] = 1;
    }
    double base(const Sol& s) {
        if (!have_ || last_ != s) { last_ = s; lastObj_ = M.objective(s); have_ = true; }
        return lastObj_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    return std::make_unique<SetupTransferWithinItem>(model, w);
}
