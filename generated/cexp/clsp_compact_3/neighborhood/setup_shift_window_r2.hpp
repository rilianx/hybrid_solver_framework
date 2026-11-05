// COMPONENT: {"name": "setup_shift_window", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 6]}}}
class SetupShiftWindow : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupShiftWindow(const Model& m, int w) : M(m), W(std::max(1, w)) {}

    // move = {item, a, b, ...}: toggle de s[item][a] y s[item][b] (b == -1 solo en el caso degenerado)
    // Traslado: a abierto, b cerrado, |a-b| <= W  -> cierra a y abre b (siempre 2 variables).
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                if (!s[i][t]) continue;
                int lo = std::max(0, t - W), hi = std::min(T - 1, t + W);
                for (int u = lo; u <= hi; ++u)
                    if (u != t && !s[i][u]) out.push_back(Move{i, t, u, 0, 0, 0, 0});
            }
        }
        if (!out.empty()) return;
        // Sin traslados posibles (todo abierto o todo cerrado por ítem): toggle conjunto de
        // dos posiciones cercanas del mismo ítem (fusionar dos setups / abrir un par).
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                int hi = std::min(T - 1, t + W);
                for (int u = t + 1; u <= hi; ++u) out.push_back(Move{i, t, u, 0, 0, 0, 0});
            }
        }
        if (!out.empty()) return;
        // Último recurso (p.ej. T == 1): toggle individual para no dejar el vecindario vacío.
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < (int)s[i].size(); ++t) out.push_back(Move{i, t, -1, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        mutate(r, m);
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        work = s;
        mutate(work, m);
        return M.objective(work) - b;
    }
    // doble toggle: auto-inverso, la clave tabú por defecto (el mismo movimiento) es correcta

private:
    const Model& M;
    int W;
    Sol cached, work;
    double cachedVal = 0.0;
    bool valid = false;

    static void mutate(Sol& r, const Move& m) {
        if (m[1] >= 0) r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        if (m[2] >= 0) r[m[0]][m[2]] = r[m[0]][m[2]] ? 0 : 1;
    }
    double base(const Sol& s) {
        if (!valid || s != cached) { cached = s; cachedVal = M.objective(s); valid = true; }
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 2);
    return std::make_unique<SetupShiftWindow>(model, w);
}
