// COMPONENT: {"name": "setup_shift_merge", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 6]}}}
class SetupShiftMerge : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupShiftMerge(const Model& m, int w) : M(m), W(std::max(1, w)) {}

    // m = {i, t, t2, mode}; mode 0: mover setup t->t2; 1: quitar t (fusión con lote previo); 2: abrir setup en t2
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const auto& row = s[i];
            bool any = false;
            int prev = -1;
            for (int t = 0; t < M.T; ++t) {
                if (!row[t]) continue;
                any = true;
                int lo = std::max(0, t - W), hi = std::min(M.T - 1, t + W);
                for (int t2 = lo; t2 <= hi; ++t2)
                    if (t2 != t && !row[t2]) out.push_back(Move{i, t, t2, 0, 0, 0, 0});
                if (prev >= 0 && t - prev <= W) out.push_back(Move{i, t, prev, 1, 0, 0, 0});
                prev = t;
            }
            if (!any && M.T > 0) {
                int f = 0;
                while (f < M.T && M.d[i][f] <= 0) ++f;
                if (f >= M.T) f = 0;
                out.push_back(Move{i, f, f, 2, 0, 0, 0});
            }
        }
        if (out.empty()) {
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t)
                    out.push_back(s[i][t] ? Move{i, t, t, 1, 0, 0, 0} : Move{i, t, t, 2, 0, 0, 0});
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        auto& row = r[m[0]];
        if (m[3] == 0) { row[m[1]] = 0; row[m[2]] = 1; }
        else if (m[3] == 1) row[m[1]] = 0;
        else row[m[2]] = 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        Sol r = apply(s, m);
        return M.objective(r) - b;
    }
    Move tabu_key(const Move& m) override {
        if (m[3] == 0) return Move{m[0], m[2], m[1], 0, 0, 0, 0};
        return m;
    }

private:
    const Model& M;
    int W;
    Sol cS;
    double cObj = 0.0;
    bool cValid = false;

    double base(const Sol& s) {
        if (!cValid || s != cS) { cS = s; cObj = M.objective(s); cValid = true; }
        return cObj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)std::lround(params.get("window", 3));
    return std::make_unique<SetupShiftMerge>(model, w);
}
