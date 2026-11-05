// COMPONENT: {"name": "setup_time_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 10]}, "block": {"type": "int", "range": [2, 8]}}}
class SetupTimeShift : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupTimeShift(const Model& m, int w, int b) : M(m), W(std::max(1, w)), B(std::max(2, b)) {}

    // m = {0, i, t, t2}: mueve el setup del ítem i de t a t2 (|t2-t| <= W), toca 2 variables.
    // m = {1, i, t, len, v}: en un ítem uniforme (sin desplazamientos posibles) fija el bloque
    //     [t, t+len) al valor v (len >= 2): abre o cierra varios períodos consecutivos a la vez.
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            bool any = false;
            for (int t = 0; t < T; ++t) {
                if (s[i][t] != 1) continue;
                int lo = std::max(0, t - W), hi = std::min(T - 1, t + W);
                for (int t2 = lo; t2 <= hi; ++t2) {
                    if (t2 == t || s[i][t2] != 0) continue;
                    out.push_back(Move{0, i, t, t2, 0, 0, 0});
                    any = true;
                }
            }
            if (!any && T >= 2) {
                // ítem uniforme: todos los períodos con el mismo valor
                int cur = (s[i][0] == 1) ? 1 : 0;
                int v = 1 - cur;
                int len = std::min(B, T);
                for (int t = 0; t + len <= T; ++t)
                    out.push_back(Move{1, i, t, len, v, 0, 0});
            }
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

    Move tabu_key(const Move& m) override {
        if (m[0] == 0) return Move{0, m[1], m[3], m[2], 0, 0, 0};
        return Move{1, m[1], m[2], m[3], 1 - m[4], 0, 0};
    }

private:
    const Model& M;
    int W, B;
    Sol work, cached;
    double cachedVal = 0.0;
    bool cacheValid = false;

    static void modify(Sol& r, const Move& m) {
        int i = m[1];
        if (m[0] == 0) { r[i][m[2]] = 0; r[i][m[3]] = 1; }
        else {
            int end = std::min((int)r[i].size(), m[2] + m[3]);
            for (int t = m[2]; t < end; ++t) r[i][t] = m[4];
        }
    }

    double baseObj(const Sol& s) {
        if (cacheValid && s == cached) return cachedVal;
        cachedVal = M.objective(s);
        cached = s;
        cacheValid = true;
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    int b = (int)params.get("block", 3);
    return std::unique_ptr<hsf::Neighborhood<Model>>(new SetupTimeShift(model, w, b));
}
