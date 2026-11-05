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
    // m[0]==1: intercambia los valores de los periodos m[2] < m[3] del ítem m[1] (desplaza un setup en el tiempo)
    // m[0]==2: invierte el bloque contiguo [m[2], m[3]] (longitud >= 2) del ítem m[1]
    static void applyIn(Sol& r, const Move& m) {
        int i = m[1], t = m[2], t2 = m[3];
        if (m[0] == 1) {
            int a = r[i][t] ? 1 : 0;
            int b = r[i][t2] ? 1 : 0;
            r[i][t] = b; r[i][t2] = a;
        } else {
            for (int k = t; k <= t2; ++k) r[i][k] = r[i][k] ? 0 : 1;
        }
    }
public:
    SetupTimeShift(const Model& m, int w) : M(m), W(std::max(1, w)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                int vt = s[i][t] ? 1 : 0;
                int hi = std::min(T - 1, t + W);
                for (int t2 = t + 1; t2 <= hi; ++t2) {
                    int v2 = s[i][t2] ? 1 : 0;
                    if (vt != v2) {
                        Move m{}; m[0] = 1; m[1] = i; m[2] = t; m[3] = t2;
                        out.push_back(m);
                    }
                    // bloque de longitud 2 con valores distintos == intercambio: no duplicar
                    if (t2 == t + 1 && vt != v2) continue;
                    Move m{}; m[0] = 2; m[1] = i; m[2] = t; m[3] = t2;
                    out.push_back(m);
                }
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
    // ambos movimientos son auto-inversos (intercambio y bloque invertido)
    Move tabu_key(const Move& m) override { return m; }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    return std::make_unique<SetupTimeShift>(model, w);
}
