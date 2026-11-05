// COMPONENT: {"name": "item_plan_row_copy", "slot": "relink", "params": {"rows_per_step": {"type": "int", "range": [1, 2]}}}
class ItemPlanRowCopy : public hsf::Relink<Model> {
public:
    using S = Model::Solution;
    ItemPlanRowCopy(const Model& m, int k) : m_(m), k_(std::max(1, k)) {}

    static bool rowDiff(const std::vector<int>& a, const std::vector<int>& b) {
        if (a.size() != b.size()) return true;
        for (size_t t = 0; t < a.size(); ++t) if (a[t] != b[t]) return true;
        return false;
    }

    int distance(const S& a, const S& b) override {
        int d = 0;
        const size_t n = std::max(a.size(), b.size());
        for (size_t i = 0; i < n; ++i) {
            if (i >= a.size() || i >= b.size()) { ++d; continue; }
            d += rowDiff(a[i], b[i]);
        }
        return d;
    }

    S step(const S& cur, const S& guide, Rng& rng) override {
        rows_.clear();
        const size_t n = std::min(cur.size(), guide.size());
        for (size_t i = 0; i < n; ++i)
            if (rowDiff(cur[i], guide[i])) rows_.push_back((int)i);
        S out = cur;
        if (out.size() != guide.size()) out.resize(guide.size());
        for (size_t i = n; i < guide.size(); ++i) out[i] = guide[i];
        if (rows_.empty()) return out;
        const int m = (int)rows_.size();
        const int k = std::min(k_, m);
        for (int j = 0; j < k; ++j) {
            int r = j + rng.below(m - j);
            std::swap(rows_[j], rows_[r]);
            out[rows_[j]] = guide[rows_[j]];
        }
        return out;
    }

private:
    const Model& m_;
    int k_;
    std::vector<int> rows_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)std::lround(params.get("rows_per_step", 1.0));
    k = std::min(2, std::max(1, k));
    return std::make_unique<ItemPlanRowCopy>(model, k);
}
