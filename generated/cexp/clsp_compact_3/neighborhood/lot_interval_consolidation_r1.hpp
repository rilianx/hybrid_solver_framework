// COMPONENT: {"name": "lot_interval_consolidation", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 8]}}}
class LotIntervalConsolidation : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    LotIntervalConsolidation(const Model& m, int L) : M(m), LMAX(std::max(2, L)) {}

    // move = {item, a, L}; L >= 2: consolidar [a, a+L); L == 0: toggle (respaldo degenerado)
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            const std::vector<int>& y = s[i];
            int T = (int)y.size();
            for (int a = 0; a + 1 < T; ++a) {
                int lim = std::min(LMAX, T - a);
                for (int L = 2; L <= lim; ++L) {
                    bool include = (L == 2) ? (y[a] == 0 || y[a + 1] != 0) : (y[a + L - 1] != 0);
                    if (include) out.push_back(Move{i, a, L, 0, 0, 0, 0});
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < (int)s[i].size(); ++t) out.push_back(Move{i, t, 0, 0, 0, 0, 0});
        }
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

private:
    const Model& M;
    int LMAX;
    Sol cached, work;
    double cachedVal = 0.0;
    bool valid = false;

    static void mutate(Sol& r, const Move& m) {
        std::vector<int>& y = r[m[0]];
        int a = m[1], L = m[2];
        if (L == 0) { y[a] = y[a] ? 0 : 1; return; }
        y[a] = 1;
        int e = std::min(a + L, (int)y.size());
        for (int k = a + 1; k < e; ++k) y[k] = 0;
    }
    double base(const Sol& s) {
        if (!valid || s != cached) { cached = s; cachedVal = M.objective(s); valid = true; }
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)params.get("max_len", 4);
    return std::make_unique<LotIntervalConsolidation>(model, L);
}
