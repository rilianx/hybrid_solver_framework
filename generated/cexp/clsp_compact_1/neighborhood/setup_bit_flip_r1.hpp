// COMPONENT: {"name": "setup_bit_flip", "slot": "neighborhood", "params": {"skip_period0_drop": {"type": "cat", "values": ["no", "yes"]}}}
class SetupBitFlip : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupBitFlip(const Model& m, bool skip0) : M(m), skipPeriod0Drop(skip0) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            for (int t = 0; t < T; ++t) {
                // dejar sin setup el período 0 con demanda positiva es casi siempre infactible
                if (skipPeriod0Drop && t == 0 && s[i][t] == 1 && i < (int)M.d.size() &&
                    !M.d[i].empty() && M.d[i][0] > 0) continue;
                out.push_back(Move{i, t, 0, 0, 0, 0, 0});
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < (int)s[i].size(); ++t) out.push_back(Move{i, t, 0, 0, 0, 0, 0});
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = 1 - r[m[0]][m[1]];
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        work = s;
        work[m[0]][m[1]] = 1 - work[m[0]][m[1]];
        return M.objective(work) - base;
    }

private:
    const Model& M;
    bool skipPeriod0Drop;
    Sol work, cached;
    double cachedVal = 0.0;
    bool cacheValid = false;

    double baseObj(const Sol& s) {
        if (cacheValid && s == cached) return cachedVal;
        cachedVal = M.objective(s);
        cached = s;
        cacheValid = true;
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool skip0 = params.text("skip_period0_drop", "no") == "yes";
    return std::unique_ptr<hsf::Neighborhood<Model>>(new SetupBitFlip(model, skip0));
}
