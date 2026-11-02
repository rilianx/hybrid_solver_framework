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
                    if (u != t && !s[i][u]) out.push_back(mk(i, t, u, 0));
            }
        // división de lote: abrir un setup adicional del mismo ítem (sin cerrar otro)
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t)
                if (!s[i][t]) out.push_back(mk(i, t, t, 2));
        // intercambio de la ranura de setup entre dos ítems en el mismo periodo
        for (int t = 0; t < M.T; ++t)
            for (int i = 0; i < M.n; ++i) {
                if (!s[i][t]) continue;
                for (int j = 0; j < M.n; ++j)
                    if (j != i && !s[j][t]) out.push_back(mk(i, t, j, 4));
            }
        if (out.empty()) {  // sin transferencias posibles: alternar pares adyacentes (dos variables)
            if (M.T >= 2) {
                for (int i = 0; i < M.n; ++i)
                    for (int t = 0; t + 1 < M.T; ++t) out.push_back(mk(i, t, t + 1, 1));
            } else {
                for (int i = 0; i < M.n; ++i)
                    for (int t = 0; t < M.T; ++t) out.push_back(mk(i, t, t, 2));
            }
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

    Move tabu_key(const Move& m) override {
        if (m[3] == 0) return mk(m[0], m[2], m[1], 0);
        if (m[3] == 4) return mk(m[2], m[1], m[0], 4);
        return m;  // dobles y simples flips son auto-inversos
    }

private:
    const Model& M;
    int W;
    Sol last_, work_;
    double lastObj_ = 0.0;
    bool have_ = false;

    static Move mk(int i, int t, int u, int k) { Move m{}; m[0] = i; m[1] = t; m[2] = u; m[3] = k; return m; }
    static void mod(Sol& y, const Move& m) {
        int i = m[0], t = m[1], u = m[2];
        if (m[3] == 2) { y[i][t] = y[i][t] ? 0 : 1; return; }
        if (m[3] == 4) { y[i][t] = 0; y[u][t] = 1; return; }
        if (m[3] == 1) {
            y[i][t] = y[i][t] ? 0 : 1;
            y[i][u] = y[i][u] ? 0 : 1;
            return;
        }
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
