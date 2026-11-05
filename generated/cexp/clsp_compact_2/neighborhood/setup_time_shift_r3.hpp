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
    // Movimiento emparejado entre dos ítems (desplazamiento temporal cruzado):
    // m[1]=i, m[2]=j, m[3]=t < m[4]=t2, con i: (t=1, t2=0) y j: (t=0, t2=1).
    // i desplaza su setup de t a t2 y j desplaza el suyo de t2 a t;
    // el número de setups en cada periodo se conserva (equilibrio de capacidad).
    static void applyIn(Sol& r, const Move& m) {
        int i = m[1], j = m[2], t = m[3], t2 = m[4];
        r[i][t] = 0; r[i][t2] = 1;
        r[j][t] = 1; r[j][t2] = 0;
    }
public:
    SetupTimeShift(const Model& m, int w) : M(m), W(std::max(1, w)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        if (n < 2) return;
        int T = 0;
        for (int i = 0; i < n; ++i) T = std::max(T, (int)s[i].size());
        for (int t = 0; t < T; ++t) {
            int hi = std::min(T - 1, t + W);
            for (int t2 = t + 1; t2 <= hi; ++t2) {
                for (int i = 0; i < n; ++i) {
                    if (t2 >= (int)s[i].size()) continue;
                    if (!(s[i][t] && !s[i][t2])) continue;
                    for (int j = 0; j < n; ++j) {
                        if (j == i || t2 >= (int)s[j].size()) continue;
                        if (!(!s[j][t] && s[j][t2])) continue;
                        Move m{}; m[0] = 1; m[1] = i; m[2] = j; m[3] = t; m[4] = t2;
                        out.push_back(m);
                    }
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
    // tras aplicar (i,j,t,t2), lo deshace el mismo movimiento con los ítems intercambiados
    Move tabu_key(const Move& m) override {
        Move k = m;
        std::swap(k[1], k[2]);
        return k;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    return std::make_unique<SetupTimeShift>(model, w);
}
