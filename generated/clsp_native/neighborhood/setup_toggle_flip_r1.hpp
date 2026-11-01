// COMPONENT: {"name": "setup_toggle_flip", "slot": "neighborhood", "params": {"sweep_items_first": {"type": "cat", "values": ["yes", "no"]}}}
class SetupToggleFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupToggleFlip(const Model& m, bool itemsFirst) : M(m), itemsFirst_(itemsFirst) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        (void)s;
        if (itemsFirst_) {
            for (int i = 0; i < M.n; ++i)
                for (int t = 0; t < M.T; ++t) out.push_back(mk(i, t));
        } else {
            for (int t = 0; t < M.T; ++t)
                for (int i = 0; i < M.n; ++i) out.push_back(mk(i, t));
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = r[m[0]][m[1]] ? 0 : 1;
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = base(s);
        work_ = s;
        work_[m[0]][m[1]] = work_[m[0]][m[1]] ? 0 : 1;
        return M.objective(work_) - b;
    }

private:
    const Model& M;
    bool itemsFirst_;
    Sol last_, work_;
    double lastObj_ = 0.0;
    bool have_ = false;

    static Move mk(int i, int t) { Move m{}; m[0] = i; m[1] = t; return m; }
    double base(const Sol& s) {
        if (!have_ || last_ != s) { last_ = s; lastObj_ = M.objective(s); have_ = true; }
        return lastObj_;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool f = params.text("sweep_items_first", "yes") == "yes";
    return std::make_unique<SetupToggleFlip>(model, f);
}
