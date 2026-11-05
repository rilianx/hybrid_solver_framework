// COMPONENT: {"name": "item_run_segment_copy", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["uniform", "short", "long"]}}}
class ItemRunSegmentRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    struct Run { int i, a, b; };
    ItemRunSegmentRelink(const Model& m, int mode) : m_(m), mode_(mode) {}

    int distance(const Sol& a, const Sol& b) override {
        if (a.size() != b.size()) return 1 + (int)std::max(a.size(), b.size());
        int runs = 0;
        for (size_t i = 0; i < a.size(); ++i) {
            const auto& ra = a[i]; const auto& rb = b[i];
            if (ra.size() != rb.size()) { runs += 1 + (int)std::max(ra.size(), rb.size()); continue; }
            bool prev = false;
            for (size_t t = 0; t < ra.size(); ++t) {
                bool df = ra[t] != rb[t];
                if (df && !prev) ++runs;
                prev = df;
            }
        }
        return runs;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) return guide;
        for (size_t i = 0; i < cur.size(); ++i) if (cur[i].size() != guide[i].size()) return guide;
        runs_.clear();
        for (size_t i = 0; i < guide.size(); ++i) {
            const auto& rc = cur[i]; const auto& rg = guide[i];
            int Tn = (int)rg.size();
            int t = 0;
            while (t < Tn) {
                if (rc[t] != rg[t]) {
                    int s = t;
                    while (t < Tn && rc[t] != rg[t]) ++t;
                    runs_.push_back({(int)i, s, t});
                } else ++t;
            }
        }
        if (runs_.empty()) return guide;
        int R = (int)runs_.size();
        int j = rng.below(R);
        if (mode_ != 0 && R > 1) {
            int j2 = rng.below(R);
            int l1 = runs_[j].b - runs_[j].a, l2 = runs_[j2].b - runs_[j2].a;
            if ((mode_ == 1 && l2 < l1) || (mode_ == 2 && l2 > l1)) j = j2;
        }
        const Run& ru = runs_[j];
        Sol r = cur;
        auto& row = r[ru.i];
        const auto& grow = guide[ru.i];
        for (int t = ru.a; t < ru.b; ++t) row[t] = grow[t];
        return r;
    }

private:
    const Model& m_;
    int mode_;
    std::vector<Run> runs_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string p = params.text("pick", "uniform");
    int mode = (p == "short") ? 1 : (p == "long") ? 2 : 0;
    return std::make_unique<ItemRunSegmentRelink>(model, mode);
}
