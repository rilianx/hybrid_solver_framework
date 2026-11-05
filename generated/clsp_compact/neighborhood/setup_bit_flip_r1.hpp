// COMPONENT: {"name": "setup_bit_flip", "slot": "neighborhood", "params": {"est_unmet_factor": {"type": "float", "range": [1.0, 10.0]}}}
class SetupBitFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupBitFlip(const Model& m, double uf) : M(m), uf_(uf) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) out.push_back(Move{i, t, 0, 0, 0, 0, 0});
    }
    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        return r;
    }
    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        Sol r = apply(s, m);
        return M.objective(r) - b;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& m) override {
        int i = m[0], t = m[1];
        double sc = s[i][t] ? -M.s[i] : M.s[i];
        return sc + rowCost(s, i, t) - rowCost(s, i, -1);
    }

private:
    const Model& M;
    double uf_;
    Sol cS;
    double cObj = 0.0;
    bool cValid = false;

    double base(const Sol& s) {
        if (!cValid || s != cS) { cS = s; cObj = M.objective(s); cValid = true; }
        return cObj;
    }
    // costo de inventario + demanda no cubierta (sin capacidad) de la fila i, con el bit flipT invertido
    double rowCost(const Sol& s, int i, int flipT) const {
        const auto& row = s[i];
        double U = uf_ * (M.h[i] * M.T + M.s[i] + 1.0);
        double c = 0.0;
        int last = -1;
        for (int t = 0; t < M.T; ++t) {
            int b = row[t] ^ (t == flipT ? 1 : 0);
            if (b) last = t;
            double dd = M.d[i][t];
            if (dd <= 0) continue;
            if (last < 0) c += dd * U;
            else c += dd * M.h[i] * (t - last);
        }
        return c;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double uf = params.get("est_unmet_factor", 3.0);
    return std::make_unique<SetupBitFlip>(model, uf);
}
