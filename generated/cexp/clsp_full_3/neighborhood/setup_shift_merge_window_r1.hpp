// COMPONENT: {"name": "setup_shift_merge_window", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 8]}}}
using Sol = Model::Solution;

struct ShiftEval {
    const Model& M;
    Sol base, work;
    double obj = 0.0;
    bool has = false;
    explicit ShiftEval(const Model& m) : M(m) {}
    double baseObj(const Sol& s) {
        if (!has || s != base) { base = s; work = s; obj = M.objective(s); has = true; }
        return obj;
    }
};

class SetupShiftMerge : public hsf::Neighborhood<Model> {
public:
    SetupShiftMerge(const Model& m, int w) : M(m), W(w), ev(m) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const std::vector<int>& y = s[i];
            bool any = false;
            for (int t = 0; t < M.T; ++t) {
                if (!y[t]) continue;
                any = true;
                int lo = std::max(0, t - W), hi = std::min(M.T - 1, t + W);
                for (int t2 = lo; t2 <= hi; ++t2) {
                    if (t2 == t) continue;
                    Move mv{}; mv[0] = i; mv[1] = t; mv[2] = t2;
                    out.push_back(mv);
                }
            }
            if (!any) {
                for (int t2 = 0; t2 < M.T; ++t2) {
                    Move mv{}; mv[0] = i; mv[1] = -1; mv[2] = t2;
                    out.push_back(mv);
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < M.n; ++i)
                for (int t2 = 0; t2 < M.T; ++t2) {
                    Move mv{}; mv[0] = i; mv[1] = -1; mv[2] = t2;
                    out.push_back(mv);
                }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        int i = m[0], t = m[1], t2 = m[2];
        if (t >= 0) r[i][t] = 0;
        r[i][t2] = 1;
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = ev.baseObj(s);
        int i = m[0], t = m[1], t2 = m[2];
        std::vector<int>& y = ev.work[i];
        int o1 = (t >= 0) ? y[t] : 0;
        int o2 = y[t2];
        if (t >= 0) y[t] = 0;
        y[t2] = 1;
        double a = M.objective(ev.work);
        y[t2] = o2;
        if (t >= 0) y[t] = o1;
        return a - b;
    }

    Move tabu_key(const Move& m) override {
        Move k{}; k[0] = m[0]; k[1] = m[2]; k[2] = m[1];
        return k;
    }

private:
    const Model& M;
    int W;
    ShiftEval ev;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)std::lround(params.get("window", 3.0));
    w = std::max(1, std::min(8, w));
    return std::make_unique<SetupShiftMerge>(model, w);
}
