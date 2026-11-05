// COMPONENT: {"name": "item_row_copy_relink", "slot": "relink", "params": {"bias": {"type": "cat", "values": ["uniform", "setup_cost", "diff_size"]}}}
class ItemRowCopyRelink : public hsf::Relink<Model> {
public:
    ItemRowCopyRelink(const Model& m, int mode) : model(m), mode(mode) {}

    int distance(const Sol& a, const Sol& b) override {
        int d = 0;
        const size_t R = a.size();
        for (size_t i = 0; i < R; ++i) d += (a[i] != b[i]);
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        items.clear(); w.clear();
        double total = 0.0;
        const size_t R = cur.size();
        for (size_t i = 0; i < R; ++i) {
            const auto& rc = cur[i];
            const auto& rg = guide[i];
            int cnt = 0;
            const size_t C = rc.size();
            for (size_t t = 0; t < C; ++t) cnt += (rc[t] != rg[t]);
            if (cnt == 0) continue;
            double wi = 1.0;
            if (mode == 1) wi = (i < model.s.size() ? std::max(0.0, model.s[i]) : 0.0) + 1e-6;
            else if (mode == 2) wi = (double)cnt;
            items.push_back((int)i);
            w.push_back(wi);
            total += wi;
        }
        if (items.empty()) return guide;
        int pick = items.back();
        if (mode == 0 || total <= 0.0) {
            pick = items[rng.below((int)items.size())];
        } else {
            double r = rng.uniform() * total;
            for (size_t j = 0; j < items.size(); ++j) {
                r -= w[j];
                if (r <= 0.0) { pick = items[j]; break; }
            }
        }
        Sol out = cur;
        out[pick] = guide[pick];
        return out;
    }

private:
    const Model& model;
    int mode;
    std::vector<int> items;
    std::vector<double> w;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string b = params.text("bias", "uniform");
    int mode = 0;
    if (b == "setup_cost") mode = 1;
    else if (b == "diff_size") mode = 2;
    return std::make_unique<ItemRowCopyRelink>(model, mode);
}
