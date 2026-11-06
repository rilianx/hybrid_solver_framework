// COMPONENT: {"name": "setup_time_shift", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 8]}}}
class SetupTimeShift : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupTimeShift(const Model& m, int w) : M(m), W(std::max(1, w)) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const auto& row = s[i];
            for (int t1 = 0; t1 < M.P; ++t1) {
                int lim = std::min(M.P - 1, t1 + W);
                for (int t2 = t1 + 1; t2 <= lim; ++t2) {
                    if (row[t1] != row[t2]) {
                        Move mv{}; mv.fill(0);
                        mv[0] = 0; mv[1] = i; mv[2] = t1; mv[3] = t2;
                        out.push_back(mv);
                    }
                }
            }
        }
        if (out.empty()) {  // fila uniforme (todo 0 o todo 1): flips de respaldo
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.P; ++t) {
                    Move mv{}; mv.fill(0);
                    mv[0] = 1; mv[1] = i; mv[2] = t; mv[3] = t;
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
    int W;
    Sol work_, last_;
    double lastVal_ = 0.0;
    bool valid_ = false;
    static void modify(Sol& r, const Move& m) {
        auto& row = r[m[1]];
        if (m[0] == 0) std::swap(row[m[2]], row[m[3]]);
        else row[m[2]] = row[m[2]] ? 0 : 1;
    }
    double baseObj(const Sol& s) {
        if (valid_ && s == last_) return lastVal_;
        last_ = s; lastVal_ = M.objective(s); valid_ = true;
        return lastVal_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3.0);
    return std::make_unique<SetupTimeShift>(model, w);
}
