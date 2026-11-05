// COMPONENT: {"name": "period_column_window_copy", "slot": "relink", "params": {"window": {"type": "int", "range": [1, 3]}}}
class PeriodColumnRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    PeriodColumnRelink(const Model& m, int w) : m_(m), w_(std::max(1, w)) {}

    bool shapeOk(const Sol& a, const Sol& b) const {
        if (a.size() != b.size()) return false;
        for (size_t i = 0; i < a.size(); ++i) if (a[i].size() != b[i].size()) return false;
        if (!a.empty()) for (size_t i = 1; i < a.size(); ++i) if (a[i].size() != a[0].size()) return false;
        return true;
    }

    void markDiff(const Sol& a, const Sol& b, int T) {
        mark_.assign(T, 0);
        for (size_t i = 0; i < a.size(); ++i) {
            const int* ra = a[i].data(); const int* rb = b[i].data();
            for (int t = 0; t < T; ++t) if (ra[t] != rb[t]) mark_[t] = 1;
        }
    }

    int distance(const Sol& a, const Sol& b) override {
        if (!shapeOk(a, b)) {
            if (a == b) return 0;
            return 1 + (int)std::max(a.size(), b.size()) + (a.empty() ? 0 : (int)a[0].size());
        }
        if (a.empty()) return 0;
        int T = (int)a[0].size();
        markDiff(a, b, T);
        int c = 0;
        for (int t = 0; t < T; ++t) c += mark_[t];
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!shapeOk(cur, guide) || guide.empty()) return guide;
        int T = (int)guide[0].size();
        markDiff(cur, guide, T);
        cols_.clear();
        for (int t = 0; t < T; ++t) if (mark_[t]) cols_.push_back(t);
        if (cols_.empty()) return guide;
        int K = (int)cols_.size();
        int j = rng.below(K);
        int e = std::min(K, j + w_);
        Sol r = cur;
        for (size_t i = 0; i < guide.size(); ++i) {
            auto& row = r[i];
            const auto& grow = guide[i];
            for (int q = j; q < e; ++q) { int t = cols_[q]; row[t] = grow[t]; }
        }
        return r;
    }

private:
    const Model& m_;
    int w_;
    std::vector<char> mark_;
    std::vector<int> cols_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 1);
    return std::make_unique<PeriodColumnRelink>(model, w);
}
