// COMPONENT: {"name": "period_column_transplant", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["random", "fewest_diffs", "most_diffs"]}}}
class PeriodColumnTransplant : public hsf::Relink<Model> {
public:
    PeriodColumnTransplant(const Model& m, int mode) : m_(m), mode_(mode) {}

    int distance(const Sol& a, const Sol& b) override {
        int cols = 0;
        for (int t = 0; t < m_.T; ++t) {
            for (int i = 0; i < m_.n; ++i)
                if (a[i][t] != b[i][t]) { ++cols; break; }
        }
        return cols;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        cnt_.assign(m_.T, 0);
        for (int i = 0; i < m_.n; ++i)
            for (int t = 0; t < m_.T; ++t)
                cnt_[t] += (cur[i][t] != guide[i][t]);
        cand_.clear();
        int best = mode_ == 1 ? std::numeric_limits<int>::max() : 0;
        for (int t = 0; t < m_.T; ++t) {
            int c = cnt_[t];
            if (c == 0) continue;
            if (mode_ == 0) { cand_.push_back(t); continue; }
            bool better = mode_ == 1 ? c < best : c > best;
            if (better) { best = c; cand_.clear(); cand_.push_back(t); }
            else if (c == best) cand_.push_back(t);
        }
        if (cand_.empty()) return guide;
        int t = cand_[rng.below((int)cand_.size())];
        Sol out = cur;
        for (int i = 0; i < m_.n; ++i) out[i][t] = guide[i][t];
        return out;
    }

private:
    const Model& m_;
    int mode_;
    std::vector<int> cnt_, cand_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string p = params.text("pick", "random");
    int mode = p == "fewest_diffs" ? 1 : (p == "most_diffs" ? 2 : 0);
    return std::make_unique<PeriodColumnTransplant>(model, mode);
}
