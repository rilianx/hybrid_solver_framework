// COMPONENT: {"name": "lot_window_consolidation", "slot": "neighborhood", "params": {"max_span": {"type": "int", "range": [2, 8]}}}
class LotWindowConsolidation : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    LotWindowConsolidation(const Model& m, int span) : M(m), L(std::max(1, span)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const std::vector<int>& yi = s[i];
            for (int a = 0; a + 1 < M.T; ++a) {
                int lim = std::min(M.T - 1, a + L);
                for (int b = a + 1; b <= lim; ++b) {
                    if (!yi[b]) continue;
                    Move m{}; m[0] = i; m[1] = a; m[2] = b;
                    out.push_back(m);
                }
            }
        }
        if (out.empty()) {
            // sin lotes que consolidar: abrir un lote en el primer período con demanda de cada ítem
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t)
                    if (M.d[i][t] > 0) { Move m{}; m[0] = i; m[1] = t; m[2] = t; out.push_back(m); break; }
            if (out.empty()) { Move m{}; out.push_back(m); }
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        modify(r, m);
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        work = s;
        modify(work, m);
        return M.objective(work) - base;
    }
private:
    static void modify(Sol& r, const Move& m) {
        std::vector<int>& yi = r[m[0]];
        yi[m[1]] = 1;
        for (int t = m[1] + 1; t <= m[2]; ++t) yi[t] = 0;
    }
    double baseObj(const Sol& s) {
        if (cValid && cKey == s) return cVal;
        cVal = M.objective(s); cKey = s; cValid = true;
        return cVal;
    }
    const Model& M;
    int L;
    Sol work, cKey;
    double cVal = 0.0;
    bool cValid = false;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int span = (int)std::lround(params.get("max_span", 4.0));
    return std::make_unique<LotWindowConsolidation>(model, span);
}
