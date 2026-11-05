// COMPONENT: {"name": "hamming_cell_flip_setup_first", "slot": "relink", "params": {"on_first": {"type": "float", "range": [0.0, 1.0]}, "flips": {"type": "int", "range": [1, 3]}}}
class HammingCellFlipRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    HammingCellFlipRelink(const Model& m, double onFirst, int flips)
        : m_(m), onFirst_(onFirst), flips_(std::max(1, flips)) {}

    int distance(const Sol& a, const Sol& b) override {
        int dsum = 0;
        size_t rows = std::min(a.size(), b.size());
        for (size_t i = 0; i < rows; ++i) {
            const auto& ra = a[i]; const auto& rb = b[i];
            size_t cols = std::min(ra.size(), rb.size());
            for (size_t t = 0; t < cols; ++t) dsum += (ra[t] != rb[t]);
            dsum += (int)(std::max(ra.size(), rb.size()) - cols);
        }
        for (size_t i = rows; i < a.size(); ++i) dsum += (int)a[i].size() + 1;
        for (size_t i = rows; i < b.size(); ++i) dsum += (int)b[i].size() + 1;
        return dsum;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) return guide;
        for (size_t i = 0; i < cur.size(); ++i) if (cur[i].size() != guide[i].size()) return guide;
        on_.clear(); off_.clear();
        int T = guide.empty() ? 0 : (int)guide[0].size();
        for (size_t i = 0; i < guide.size(); ++i) {
            const auto& rc = cur[i]; const auto& rg = guide[i];
            for (int t = 0; t < (int)rg.size(); ++t) {
                if (rc[t] != rg[t]) {
                    int code = (int)i * T + t;
                    if (rg[t] != 0) on_.push_back(code); else off_.push_back(code);
                }
            }
        }
        if (on_.empty() && off_.empty()) return guide;
        Sol r = cur;
        int k = std::min<int>(flips_, (int)(on_.size() + off_.size()));
        for (int f = 0; f < k; ++f) {
            std::vector<int>* L;
            if (!on_.empty() && (off_.empty() || rng.uniform() < onFirst_)) L = &on_;
            else L = &off_;
            int j = rng.below((int)L->size());
            int code = (*L)[j];
            (*L)[j] = L->back(); L->pop_back();
            int i = code / T, t = code % T;
            r[i][t] = guide[i][t];
        }
        return r;
    }

private:
    const Model& m_;
    double onFirst_;
    int flips_;
    std::vector<int> on_, off_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double onFirst = params.get("on_first", 0.6);
    int flips = (int)params.get("flips", 1);
    return std::make_unique<HammingCellFlipRelink>(model, onFirst, flips);
}
