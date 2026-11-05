// COMPONENT: {"name": "lot_block_consolidation", "slot": "neighborhood", "params": {"max_span": {"type": "int", "range": [2, 8]}}}
class LotBlockConsolidation : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    LotBlockConsolidation(const Model& m, int L) : M(m), L_(std::max(2, L)) {}

    // m = {i, a, b, mode}; mode 0: y[i][a]=1, y[i][a+1..b]=0; mode 1: toggle y[i][a] (solo si T<2)
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const auto& row = s[i];
            for (int a = 0; a < M.T; ++a) {
                bool changed = (row[a] == 0);
                int hi = std::min(M.T - 1, a + L_ - 1);
                for (int b = a + 1; b <= hi; ++b) {
                    if (row[b]) changed = true;
                    if (changed) out.push_back(Move{i, a, b, 0, 0, 0, 0});
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t) out.push_back(Move{i, t, t, 1, 0, 0, 0});
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        auto& row = r[m[0]];
        if (m[3] == 1) {
            row[m[1]] = row[m[1]] ? 0 : 1;
        } else {
            row[m[1]] = 1;
            for (int t = m[1] + 1; t <= m[2]; ++t) row[t] = 0;
        }
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        Sol r = apply(s, m);
        return M.objective(r) - b;
    }

private:
    const Model& M;
    int L_;
    Sol cS;
    double cObj = 0.0;
    bool cValid = false;

    double base(const Sol& s) {
        if (!cValid || s != cS) { cS = s; cObj = M.objective(s); cValid = true; }
        return cObj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)std::lround(params.get("max_span", 4));
    return std::make_unique<LotBlockConsolidation>(model, L);
}
