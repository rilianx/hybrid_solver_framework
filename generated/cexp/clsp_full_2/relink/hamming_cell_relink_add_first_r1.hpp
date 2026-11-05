// COMPONENT: {"name": "hamming_cell_relink_add_first", "slot": "relink", "params": {"p_add_first": {"type": "float", "range": [0.0, 1.0]}}}
class HammingCellRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    HammingCellRelink(const Model& m, double p) : m_(m), pAdd_(p) {}

    int distance(const Sol& a, const Sol& b) override {
        if (!sameShape(a, b)) return 1;
        int c = 0;
        for (size_t i = 0; i < a.size(); ++i) {
            const int* x = a[i].data(); const int* y = b[i].data();
            size_t L = a[i].size();
            for (size_t t = 0; t < L; ++t) c += (x[t] != y[t]);
        }
        return c;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (!sameShape(cur, guide)) return guide;
        addC_.clear(); remC_.clear();
        for (int i = 0; i < (int)cur.size(); ++i) {
            const int* x = cur[i].data(); const int* y = guide[i].data();
            int L = (int)cur[i].size();
            for (int t = 0; t < L; ++t) {
                if (x[t] == y[t]) continue;
                if (y[t] != 0 && x[t] == 0) addC_.push_back({i, t});
                else remC_.push_back({i, t});
            }
        }
        if (addC_.empty() && remC_.empty()) return cur;
        const std::vector<std::pair<int,int>>* pool;
        if (remC_.empty()) pool = &addC_;
        else if (addC_.empty()) pool = &remC_;
        else pool = (rng.uniform() < pAdd_) ? &addC_ : &remC_;
        auto [i, t] = (*pool)[rng.below((int)pool->size())];
        Sol out = cur;
        out[i][t] = guide[i][t];
        return out;
    }

private:
    static bool sameShape(const Sol& a, const Sol& b) {
        if (a.size() != b.size()) return false;
        for (size_t i = 0; i < a.size(); ++i) if (a[i].size() != b[i].size()) return false;
        return true;
    }
    const Model& m_;
    double pAdd_;
    std::vector<std::pair<int,int>> addC_, remC_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double p = params.get("p_add_first", 0.6);
    p = std::min(1.0, std::max(0.0, p));
    return std::make_unique<HammingCellRelink>(model, p);
}
