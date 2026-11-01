// COMPONENT: {"name": "differing_run_segment_copy", "slot": "relink", "params": {"prefer_short": {"type": "float", "range": [0.0, 1.0]}}}
class DifferingRunSegmentCopy : public hsf::Relink<Model> {
public:
    DifferingRunSegmentCopy(const Model& m, double ps) : m_(m), ps_(ps) {}

    int distance(const Sol& a, const Sol& b) override {
        int runs = 0;
        for (int i = 0; i < m_.n; ++i) {
            bool prev = false;
            for (int t = 0; t < m_.T; ++t) {
                bool df = a[i][t] != b[i][t];
                if (df && !prev) ++runs;
                prev = df;
            }
        }
        return runs;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        runs_.clear();
        int minLen = std::numeric_limits<int>::max();
        for (int i = 0; i < m_.n; ++i) {
            int t = 0;
            while (t < m_.T) {
                if (cur[i][t] != guide[i][t]) {
                    int s = t;
                    while (t < m_.T && cur[i][t] != guide[i][t]) ++t;
                    runs_.push_back({i, s, t});
                    minLen = std::min(minLen, t - s);
                } else ++t;
            }
        }
        if (runs_.empty()) return guide;
        const std::array<int, 3>* pick;
        if (rng.uniform() < ps_) {
            shortIdx_.clear();
            for (int k = 0; k < (int)runs_.size(); ++k)
                if (runs_[k][2] - runs_[k][1] == minLen) shortIdx_.push_back(k);
            pick = &runs_[shortIdx_[rng.below((int)shortIdx_.size())]];
        } else {
            pick = &runs_[rng.below((int)runs_.size())];
        }
        Sol out = cur;
        int i = (*pick)[0];
        for (int t = (*pick)[1]; t < (*pick)[2]; ++t) out[i][t] = guide[i][t];
        return out;
    }

private:
    const Model& m_;
    double ps_;
    std::vector<std::array<int, 3>> runs_;
    std::vector<int> shortIdx_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("prefer_short", 0.3);
    return std::make_unique<DifferingRunSegmentCopy>(model, ps);
}
