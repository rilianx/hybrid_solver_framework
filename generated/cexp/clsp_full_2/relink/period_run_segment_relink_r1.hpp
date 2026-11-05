// COMPONENT: {"name": "period_run_segment_relink", "slot": "relink", "params": {"short_run_bias": {"type": "float", "range": [0.0, 1.0]}}}
class RunSegmentRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    RunSegmentRelink(const Model& m, double b) : m_(m), bias_(b) {}

    int distance(const Sol& a, const Sol& b) override {
        if (!sameShape(a, b)) return 1;
        int c = 0;
        for (size_t i = 0; i < a.size(); ++i) {
            const int* x = a[i].data(); const int* y = b[i].data();
            size_t L = a[i].size();
            bool prev = false;
            for (size_t t = 0; t < L; ++t) {
                bool df = (x[t] != y[t]);
                if (df && !prev) ++c;
                prev = df;
            }
        }
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!sameShape(cur, guide)) return guide;
        runs_.clear();
        int shortest = std::numeric_limits<int>::max();
        for (int i = 0; i < (int)cur.size(); ++i) {
            const int* x = cur[i].data(); const int* y = guide[i].data();
            int L = (int)cur[i].size();
            int t = 0;
            while (t < L) {
                if (x[t] == y[t]) { ++t; continue; }
                int s = t;
                while (t < L && x[t] != y[t]) ++t;
                runs_.push_back({i, s, t});  // [s, t)
                shortest = std::min(shortest, t - s);
            }
        }
        if (runs_.empty()) return cur;
        Run r;
        if (rng.uniform() < bias_) {
            idx_.clear();
            for (size_t k = 0; k < runs_.size(); ++k)
                if (runs_[k].e - runs_[k].s == shortest) idx_.push_back((int)k);
            r = runs_[idx_[rng.below((int)idx_.size())]];
        } else {
            r = runs_[rng.below((int)runs_.size())];
        }
        Sol out = cur;
        std::vector<int>& row = out[r.i];
        const std::vector<int>& g = guide[r.i];
        for (int t = r.s; t < r.e; ++t) row[t] = g[t];
        return out;
    }

private:
    struct Run { int i, s, e; };
    static bool sameShape(const Sol& a, const Sol& b) {
        if (a.size() != b.size()) return false;
        for (size_t i = 0; i < a.size(); ++i) if (a[i].size() != b[i].size()) return false;
        return true;
    }
    const Model& m_;
    double bias_;
    std::vector<Run> runs_;
    std::vector<int> idx_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double b = params.get("short_run_bias", 0.25);
    b = std::min(1.0, std::max(0.0, b));
    return std::make_unique<RunSegmentRelink>(model, b);
}
