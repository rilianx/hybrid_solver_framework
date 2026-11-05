// COMPONENT: {"name": "setup_flip_toggle", "slot": "neighborhood", "params": {"use_estimate": {"type": "int", "range": [0, 1]}}}
using Sol = Model::Solution;

struct FlipEval {
    const Model& M;
    Sol base, work;
    double obj = 0.0;
    bool has = false;
    explicit FlipEval(const Model& m) : M(m) {}
    double baseObj(const Sol& s) {
        if (!has || s != base) { base = s; work = s; obj = M.objective(s); has = true; }
        return obj;
    }
};

class SetupFlipToggle : public hsf::Neighborhood<Model> {
public:
    SetupFlipToggle(const Model& m, bool est) : M(m), useEst(est), ev(m) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        out.reserve(out.size() + (size_t)M.n * M.T);
        for (int i = 0; i < M.n; ++i)
            for (int t = 0; t < M.T; ++t) {
                Move mv{}; mv[0] = i; mv[1] = t;
                out.push_back(mv);
            }
        (void)s;
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = s[m[0]][m[1]] ? 0 : 1;
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = ev.baseObj(s);
        int i = m[0], t = m[1];
        int old = ev.work[i][t];
        ev.work[i][t] = old ? 0 : 1;
        double a = M.objective(ev.work);
        ev.work[i][t] = old;
        return a - b;
    }

    bool has_estimate() const override { return useEst; }

    double estimate(const Sol& s, const Move& m) override {
        int i = m[0], t = m[1];
        const std::vector<int>& y = s[i];
        int p = -1;
        for (int u = t - 1; u >= 0; --u) if (y[u]) { p = u; break; }
        double D = 0.0;
        for (int u = t; u < M.T; ++u) {
            if (u > t && y[u]) break;
            D += M.d[i][u];
        }
        // Sin setup previo la demanda descubierta se penaliza de una forma que la fórmula
        // barata no captura bien: ahí se usa el delta exacto.
        if (p < 0) return delta(s, m);
        double shift = M.h[i] * (t - p) * D;
        if (y[t]) return -M.s[i] + shift;
        return M.s[i] - shift;
    }

private:
    const Model& M;
    bool useEst;
    FlipEval ev;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool est = params.get("use_estimate", 1.0) >= 0.5;
    return std::make_unique<SetupFlipToggle>(model, est);
}
