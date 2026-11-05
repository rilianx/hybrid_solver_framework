// COMPONENT: {"name": "setup_time_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 10]}, "block": {"type": "int", "range": [2, 8]}}}
class SetupTimeShift : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupTimeShift(const Model& m, int w, int b) : M(m), W(std::max(1, w)), B(std::max(2, b)) {}

    // m = {0, i, t, t2}: mueve el setup del ítem i de t a t2 (|t2-t| <= W), toca 2 variables.
    // m = {1, i, off, step}: reescribe TODO el horizonte del ítem i con un patrón periódico
    //     (setup en off, off+step, off+2*step, ...; 2 <= step <= B), con al menos dos setups
    //     separados: no contiguo, no alcanzable reescribiendo un bloque.
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                if (s[i][t] != 1) continue;
                int lo = std::max(0, t - W), hi = std::min(T - 1, t + W);
                for (int t2 = lo; t2 <= hi; ++t2) {
                    if (t2 == t || s[i][t2] != 0) continue;
                    out.push_back(Move{0, i, t, t2, 0, 0, 0});
                }
            }
            for (int step = 2; step <= B; ++step) {
                for (int off = 0; off < step; ++off) {
                    if (off + step >= T) continue;  // al menos dos setups separados
                    bool same = true;
                    for (int t = 0; t < T && same; ++t) {
                        int want = (t >= off && (t - off) % step == 0) ? 1 : 0;
                        int have = (s[i][t] == 1) ? 1 : 0;
                        if (want != have) same = false;
                    }
                    if (!same) out.push_back(Move{1, i, off, step, 0, 0, 0});
                }
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
        return m;  // prohíbe volver a imponer el mismo patrón
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
            int T = (int)r[i].size(), off = m[2], step = m[3];
            for (int t = 0; t < T; ++t)
                r[i][t] = (t >= off && (t - off) % step == 0) ? 1 : 0;
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
