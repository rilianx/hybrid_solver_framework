// COMPONENT: {"name": "setup_bit_flip", "slot": "neighborhood", "params": {"max_window": {"type": "int", "range": [2, 8]}, "max_period": {"type": "int", "range": [1, 4]}}}
class SetupBitFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupBitFlip(const Model& m, int w, int p) : M(m), W(std::max(2, w)), P(std::max(1, p)) {}

    // Move: {kind, i, j_o_k, a, len, 0, 0}
    //  kind 0: intercambia setups de ítems i y j en [a, a+len)  (ventana mínima: difieren en ambos extremos)
    //  kind 1: ítem i, ventana [a, a+len): setup en a, a+k, a+2k, ... y 0 en el resto (>= 2 cambios)
    void moves(const Sol& s, std::vector<Move>& out) override {
        const int n = M.n, T = M.T;
        for (int i = 0; i < n; ++i)
            for (int j = i + 1; j < n; ++j)
                for (int a = 0; a < T; ++a) {
                    if ((s[i][a] != 0) == (s[j][a] != 0)) continue;
                    for (int len = 1; len <= W && a + len <= T; ++len) {
                        int e = a + len - 1;
                        if ((s[i][e] != 0) != (s[j][e] != 0)) out.push_back(Move{0, i, j, a, len, 0, 0});
                    }
                }
        for (int i = 0; i < n; ++i)
            for (int a = 0; a < T; ++a)
                for (int len = 2; len <= W && a + len <= T; ++len) {
                    int kmax = std::min(P, len);
                    for (int k = 1; k <= kmax + 1; ++k) {
                        int kk = (k == kmax + 1) ? len : k;   // siempre incluye la consolidación (k = len)
                        if (k == kmax + 1 && kmax == len) break;
                        int changes = 0;
                        for (int t = a; t < a + len; ++t) {
                            bool want = ((t - a) % kk) == 0;
                            if ((s[i][t] != 0) != want) ++changes;
                        }
                        if (changes >= 2) out.push_back(Move{1, i, kk, a, len, 0, 0});
                    }
                }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        const int a = m[3], len = m[4];
        if (m[0] == 0) {
            const int i = m[1], j = m[2];
            for (int t = a; t < a + len; ++t) {
                auto vi = r[i][t];
                r[i][t] = r[j][t];
                r[j][t] = vi;
            }
        } else {
            const int i = m[1], k = std::max(1, m[2]);
            for (int t = a; t < a + len; ++t) r[i][t] = (((t - a) % k) == 0) ? 1 : 0;
        }
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        Sol r = apply(s, m);
        return M.objective(r) - b;
    }
    bool has_estimate() const override { return false; }
    double estimate(const Sol& s, const Move& m) override { return delta(s, m); }

private:
    const Model& M;
    int W, P;
    Sol cS;
    double cObj = 0.0;
    bool cValid = false;

    double base(const Sol& s) {
        if (!cValid || s != cS) { cS = s; cObj = M.objective(s); cValid = true; }
        return cObj;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("max_window", 4);
    int p = (int)params.get("max_period", 3);
    return std::make_unique<SetupBitFlip>(model, w, p);
}
