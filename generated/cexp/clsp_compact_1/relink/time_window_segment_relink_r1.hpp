// COMPONENT: {"name": "time_window_segment_relink", "slot": "relink", "params": {"max_extend": {"type": "int", "range": [0, 6]}, "all_items_prob": {"type": "float", "range": [0.0, 1.0]}}}
class TimeWindowSegmentRelink : public hsf::Relink<Model> {
    using Sol = Model::Solution;
    const Model& m;
    int maxExt;
    double allItemsProb;
    std::vector<int> diffI, diffT;
public:
    TimeWindowSegmentRelink(const Model& model, int me, double ap)
        : m(model), maxExt(std::max(0, me)), allItemsProb(ap) {}

    int distance(const Sol& a, const Sol& b) override {
        int dist = 0;
        size_t ni = std::min(a.size(), b.size());
        for (size_t i = 0; i < ni; ++i) {
            const auto& ra = a[i];
            const auto& rb = b[i];
            size_t nt = std::min(ra.size(), rb.size());
            for (size_t t = 0; t < nt; ++t) dist += (ra[t] != rb[t]);
            dist += (int)(std::max(ra.size(), rb.size()) - nt);
        }
        size_t mx = std::max(a.size(), b.size());
        for (size_t i = ni; i < mx; ++i) dist += (int)(i < a.size() ? a[i].size() : b[i].size());
        return dist;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) return guide;
        diffI.clear(); diffT.clear();
        for (size_t i = 0; i < cur.size(); ++i) {
            if (cur[i].size() != guide[i].size()) return guide;
            for (size_t t = 0; t < cur[i].size(); ++t)
                if (cur[i][t] != guide[i][t]) { diffI.push_back((int)i); diffT.push_back((int)t); }
        }
        if (diffI.empty()) return guide;
        int idx = rng.below((int)diffI.size());
        int i0 = diffI[idx], t0 = diffT[idx];
        int left = maxExt > 0 ? rng.below(maxExt + 1) : 0;
        int right = maxExt > 0 ? rng.below(maxExt + 1) : 0;
        Sol r = cur;
        bool allItems = rng.uniform() < allItemsProb;
        if (allItems) {
            for (size_t i = 0; i < r.size(); ++i) {
                int T = (int)r[i].size();
                int lo = std::max(0, t0 - left), hi = std::min(T - 1, t0 + right);
                for (int t = lo; t <= hi; ++t) r[i][t] = guide[i][t];
            }
        } else {
            int T = (int)r[i0].size();
            int lo = std::max(0, t0 - left), hi = std::min(T - 1, t0 + right);
            for (int t = lo; t <= hi; ++t) r[i0][t] = guide[i0][t];
        }
        return r;  // (i0,t0) is always copied, so Hamming distance drops by >= 1
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    int me = (int)std::lround(params.get("max_extend", 2.0));
    double ap = params.get("all_items_prob", 0.2);
    return std::make_unique<TimeWindowSegmentRelink>(model, me, ap);
}
