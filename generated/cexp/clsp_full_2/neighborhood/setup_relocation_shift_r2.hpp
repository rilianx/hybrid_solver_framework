// COMPONENT: {"name": "setup_relocation_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 6]}}}
class SetupRelocationShift : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupRelocationShift(const Model& m, int w) : M(m), W(std::max(1, w)) {}
    // Movimiento: m[0]=ítem, m[1]=a, m[2]=b (a<b) => invierte y[i][a] e y[i][b].
    // Con valores distintos es un desplazamiento del setup (a->b o b->a) a un período LIBRE;
    // nunca hay fusión (que equivaldría a un flip simple). m[2]=-1 solo en el caso degenerado T==1.
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const std::vector<int>& yi = s[i];
            for (int t = 0; t < M.T; ++t) {
                int lim = std::min(M.T - 1, t + W);
                for (int t2 = t + 1; t2 <= lim; ++t2) {
                    if ((yi[t] != 0) == (yi[t2] != 0)) continue;
                    Move m{}; m[0] = i; m[1] = t; m[2] = t2;
                    out.push_back(m);
                }
            }
        }
        if (out.empty()) {
            // sin desplazamientos posibles (todo activo o todo inactivo en cada ventana):
            // pares fusión/división de dos setups del mismo ítem, siempre dos variables a la vez
            for (int i = 0; i < M.n; ++i) {
                for (int t = 0; t < M.T; ++t) {
                    int lim = std::min(M.T - 1, t + W);
                    for (int t2 = t + 1; t2 <= lim; ++t2) {
                        Move m{}; m[0] = i; m[1] = t; m[2] = t2;
                        out.push_back(m);
                    }
                }
            }
        }
        if (out.empty()) {
            // caso degenerado T==1: no existe ningún par
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t) { Move m{}; m[0] = i; m[1] = t; m[2] = -1; out.push_back(m); }
            if (out.empty()) { Move m{}; m[0] = -1; m[1] = -1; m[2] = -1; out.push_back(m); }
        }
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        modify(r, m);
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        if (m[0] < 0) return 0.0;
        double base = baseObj(s);
        work = s;
        modify(work, m);
        return M.objective(work) - base;
    }
    // invertir los mismos dos bits deshace el movimiento: auto-inverso con clave canónica
    Move tabu_key(const Move& m) override {
        Move k{}; k[0] = m[0]; k[1] = m[1]; k[2] = m[2];
        return k;
    }
private:
    static void modify(Sol& r, const Move& m) {
        if (m[0] < 0) return;
        std::vector<int>& yi = r[m[0]];
        if (m[1] >= 0) yi[m[1]] = yi[m[1]] ? 0 : 1;
        if (m[2] >= 0) yi[m[2]] = yi[m[2]] ? 0 : 1;
    }
    double baseObj(const Sol& s) {
        if (cValid && cKey == s) return cVal;
        cVal = M.objective(s); cKey = s; cValid = true;
        return cVal;
    }
    const Model& M;
    int W;
    Sol work, cKey;
    double cVal = 0.0;
    bool cValid = false;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)std::lround(params.get("window", 2.0));
    return std::make_unique<SetupRelocationShift>(model, w);
}
