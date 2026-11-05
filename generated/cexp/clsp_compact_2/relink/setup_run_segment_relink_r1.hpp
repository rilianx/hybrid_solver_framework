// COMPONENT: {"name": "setup_run_segment_relink", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["uniform", "short_first", "long_first"]}}}
class SetupRunSegmentRelink : public hsf::Relink<Model> {
public:
    SetupRunSegmentRelink(const Model& m, int mode) : model(m), mode(mode) {}

    int distance(const Sol& a, const Sol& b) override {
        int d = 0;
        const size_t R = a.size();
        for (size_t i = 0; i < R; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            bool prev = false;
            const size_t C = ra.size();
            for (size_t t = 0; t < C; ++t) {
                bool df = ra[t] != rb[t];
                if (df && !prev) ++d;
                prev = df;
            }
        }
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        runI.clear(); runS.clear(); runE.clear(); w.clear();
        double total = 0.0;
        const size_t R = cur.size();
        for (size_t i = 0; i < R; ++i) {
            const auto& rc = cur[i];
            const auto& rg = guide[i];
            const int C = (int)rc.size();
            int t = 0;
            while (t < C) {
                if (rc[t] == rg[t]) { ++t; continue; }
                int s0 = t;
                while (t < C && rc[t] != rg[t]) ++t;
                int len = t - s0;
                double wi = 1.0;
                if (mode == 1) wi = 1.0 / len;
                else if (mode == 2) wi = (double)len;
                runI.push_back((int)i); runS.push_back(s0); runE.push_back(t);
                w.push_back(wi); total += wi;
            }
        }
        if (runI.empty()) return guide;
        size_t pick = runI.size() - 1;
        if (mode == 0) {
            pick = (size_t)rng.below((int)runI.size());
        } else {
            double r = rng.uniform() * total;
            for (size_t j = 0; j < runI.size(); ++j) {
                r -= w[j];
                if (r <= 0.0) { pick = j; break; }
            }
        }
        Sol out = cur;
        const int i = runI[pick];
        auto& ro = out[i];
        const auto& rg = guide[i];
        for (int t = runS[pick]; t < runE[pick]; ++t) ro[t] = rg[t];
        return out;
    }

private:
    const Model& model;
    int mode;
    std::vector<int> runI, runS, runE;
    std::vector<double> w;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string p = params.text("pick", "uniform");
    int mode = 0;
    if (p == "short_first") mode = 1;
    else if (p == "long_first") mode = 2;
    return std::make_unique<SetupRunSegmentRelink>(model, mode);
}
