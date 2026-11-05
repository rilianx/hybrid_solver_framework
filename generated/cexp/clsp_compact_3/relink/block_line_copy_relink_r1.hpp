// COMPONENT: {"name": "block_line_copy_relink", "slot": "relink", "params": {"axis": {"type": "cat", "values": ["item", "period"]}}}
class BlockLineCopyRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    bool byItem;
    std::vector<int> diff;

    bool colDiffers(const Sol& a, const Sol& b, size_t t) const {
        for (size_t i = 0; i < a.size(); ++i)
            if (t < a[i].size() && a[i][t] != b[i][t]) return true;
        return false;
    }
    size_t numCols(const Sol& a) const {
        size_t c = 0;
        for (const auto& r : a) c = std::max(c, r.size());
        return c;
    }
public:
    BlockLineCopyRelink(const Model& model, bool item) : m(model), byItem(item) {}

    int distance(const Sol& a, const Sol& b) override {
        int c = 0;
        if (byItem) {
            for (size_t i = 0; i < a.size(); ++i) c += (a[i] != b[i]);
        } else {
            size_t T = numCols(a);
            for (size_t t = 0; t < T; ++t) c += colDiffers(a, b, t);
        }
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        diff.clear();
        Sol r = cur;
        if (byItem) {
            for (size_t i = 0; i < cur.size(); ++i)
                if (cur[i] != guide[i]) diff.push_back((int)i);
            if (diff.empty()) return r;
            int i = diff[rng.below((int)diff.size())];
            r[i] = guide[i];
        } else {
            size_t T = numCols(cur);
            for (size_t t = 0; t < T; ++t)
                if (colDiffers(cur, guide, t)) diff.push_back((int)t);
            if (diff.empty()) return r;
            size_t t = (size_t)diff[rng.below((int)diff.size())];
            for (size_t i = 0; i < r.size(); ++i)
                if (t < r[i].size()) r[i][t] = guide[i][t];
        }
        return r;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string axis = params.text("axis", "item");
    return std::make_unique<BlockLineCopyRelink>(model, axis != "period");
}
