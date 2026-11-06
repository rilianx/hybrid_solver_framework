// COMPONENT: {"name": "lot_merge_interval", "slot": "neighborhood", "params": {"max_span": {"type": "int", "range": [1, 6]}}}
class LotMergeInterval : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    LotMergeInterval(const Model& m, int L) : M(m), L_(std::max(1, L)) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const auto& row = s[i];
            for (int a = 0; a < M.P; ++a) {
                int lim = std::min(M.P - 1, a + L_);
                for (int b = a + 1; b <= lim; ++b) {
                    if (row[b]) {  // b con setup: fusión real, sin duplicados
                        Move mv{}; mv.fill(0);
                        mv[0] = i; mv[1] = a; mv[2] = b;
                        out.push_back(mv);
                    }
                }
            }
        }
        if (out.empty()) {  // sin setups fusionables: abrir un lote (b == a)
            for (int i = 0; i < M.n; ++i)
                for (int a = 0; a < M.P; ++a)
                    if (!s[i][a]) {
                        Move mv{}; mv.fill(0);
                        mv[0] = i; mv[1] = a; mv[2] = a;
                        out.push_back(mv);
                    }
        }
        if (out.empty()) {  // degenerado (P == 1 y todo con setup): quitar setup
            for (int i = 0; i < M.n; ++i) {
                Move mv{}; mv.fill(0);
                mv[0] = i; mv[1] = 0; mv[2] = -1;
                out.push_back(mv);
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
        work_ = s;
        modify(work_, m);
        return M.objective(work_) - base;
    }

private:
    const Model& M;
    int L_;
    Sol work_, last_;
    double lastVal_ = 0.0;
    bool valid_ = false;
    static void modify(Sol& r, const Move& m) {
        auto& row = r[m[0]];
        if (m[2] < 0) { row[m[1]] = 0; return; }
        row[m[1]] = 1;
        for (int u = m[1] + 1; u <= m[2]; ++u) row[u] = 0;
    }
    double baseObj(const Sol& s) {
        if (valid_ && s == last_) return lastVal_;
        last_ = s; lastVal_ = M.objective(s); valid_ = true;
        return lastVal_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)params.get("max_span", 3.0);
    return std::make_unique<LotMergeInterval>(model, L);
}
