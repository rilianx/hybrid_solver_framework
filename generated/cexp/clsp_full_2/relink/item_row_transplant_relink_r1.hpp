// COMPONENT: {"name": "item_row_transplant_relink", "slot": "relink", "params": {"min_change_bias": {"type": "float", "range": [0.0, 1.0]}}}
class ItemRowRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    ItemRowRelink(const Model& m, double b) : m_(m), bias_(b) {}

    int distance(const Sol& a, const Sol& b) override {
        if (!sameShape(a, b)) return 1;
        int c = 0;
        for (size_t i = 0; i < a.size(); ++i) c += (a[i] != b[i]);
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!sameShape(cur, guide)) return guide;
        rows_.clear(); cnt_.clear();
        int best = std::numeric_limits<int>::max();
        for (int i = 0; i < (int)cur.size(); ++i) {
            const int* x = cur[i].data(); const int* y = guide[i].data();
            int L = (int)cur[i].size(), c = 0;
            for (int t = 0; t < L; ++t) c += (x[t] != y[t]);
            if (c > 0) { rows_.push_back(i); cnt_.push_back(c); best = std::min(best, c); }
        }
        if (rows_.empty()) return cur;
        int pick;
        if (rng.uniform() < bias_) {
            mins_.clear();
            for (size_t k = 0; k < rows_.size(); ++k) if (cnt_[k] == best) mins_.push_back(rows_[k]);
            pick = mins_[rng.below((int)mins_.size())];
        } else {
            pick = rows_[rng.below((int)rows_.size())];
        }
        Sol out = cur;
        out[pick] = guide[pick];
        return out;
    }

private:
    static bool sameShape(const Sol& a, const Sol& b) {
        if (a.size() != b.size()) return false;
        for (size_t i = 0; i < a.size(); ++i) if (a[i].size() != b[i].size()) return false;
        return true;
    }
    const Model& m_;
    double bias_;
    std::vector<int> rows_, cnt_, mins_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double b = params.get("min_change_bias", 0.3);
    b = std::min(1.0, std::max(0.0, b));
    return std::make_unique<ItemRowRelink>(model, b);
}
