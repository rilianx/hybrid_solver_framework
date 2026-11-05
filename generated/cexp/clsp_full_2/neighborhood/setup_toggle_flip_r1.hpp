// COMPONENT: {"name": "setup_toggle_flip", "slot": "neighborhood", "params": {"only_relevant": {"type": "int", "range": [0, 1]}}}
class SetupToggleFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupToggleFlip(const Model& m, bool rel) : M(m), onlyRelevant(rel) {
        // hasDemandFrom[i][t] = existe demanda de i en algún período >= t
        hasDemandFrom.assign(M.n, std::vector<char>(M.T + 1, 0));
        for (int i = 0; i < M.n; ++i)
            for (int t = M.T - 1; t >= 0; --t)
                hasDemandFrom[i][t] = (M.d[i][t] > 0) || hasDemandFrom[i][t + 1];
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) {
                if (!s[i][t] && onlyRelevant && !hasDemandFrom[i][t]) continue;
                Move m{}; m[0] = i; m[1] = t;
                out.push_back(m);
            }
        if (out.empty()) { Move m{}; out.push_back(m); }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        work = s;
        work[m[0]][m[1]] = work[m[0]][m[1]] ? 0 : 1;
        return M.objective(work) - base;
    }
private:
    double baseObj(const Sol& s) {
        if (cValid && cKey == s) return cVal;
        cVal = M.objective(s); cKey = s; cValid = true;
        return cVal;
    }
    const Model& M;
    bool onlyRelevant;
    std::vector<std::vector<char>> hasDemandFrom;
    Sol work, cKey;
    double cVal = 0.0;
    bool cValid = false;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool rel = params.get("only_relevant", 1.0) >= 0.5;
    return std::make_unique<SetupToggleFlip>(model, rel);
}
