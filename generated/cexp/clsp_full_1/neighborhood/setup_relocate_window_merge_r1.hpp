// COMPONENT: {"name": "setup_relocate_window_merge", "slot": "neighborhood", "params": {"window": {"type": "int", "range": [1, 6]}}}
class CachedEvalR {
public:
    using Sol = Model::Solution;
    explicit CachedEvalR(const Model& m) : m_(m) {}
    double base(const Sol& s) {
        if (!valid_ || s != base_) { base_ = s; work_ = s; baseObj_ = m_.objective(s); valid_ = true; }
        return baseObj_;
    }
    double delta(const Sol& s, const std::vector<std::array<int, 3>>& ch) {
        double b = base(s);
        old_.resize(ch.size());
        for (size_t k = 0; k < ch.size(); ++k) { old_[k] = work_[ch[k][0]][ch[k][1]]; work_[ch[k][0]][ch[k][1]] = ch[k][2]; }
        double o = m_.objective(work_);
        for (size_t k = ch.size(); k-- > 0;) work_[ch[k][0]][ch[k][1]] = old_[k];
        return o - b;
    }
    static Sol apply(const Sol& s, const std::vector<std::array<int, 3>>& ch) {
        Sol r = s;
        for (auto& c : ch) r[c[0]][c[1]] = c[2];
        return r;
    }
private:
    const Model& m_;
    bool valid_ = false;
    Sol base_, work_;
    double baseObj_ = 0.0;
    std::vector<int> old_;
};

class SetupRelocate : public hsf::Neighborhood<Model> {
public:
    SetupRelocate(const Model& m, int w) : m_(m), ev_(m), W_(std::max(1, w)) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        const int n = m_.n, T = m_.T;
        for (int i = 0; i < n; ++i) {
            const std::vector<int>& yi = s[i];
            bool any = false;
            for (int t = 0; t < T; ++t) {
                if (!yi[t]) continue;
                any = true;
                int lo = std::max(0, t - W_), hi = std::min(T - 1, t + W_);
                int mergeT = -1, bestDist = 1 << 30;
                for (int t2 = lo; t2 <= hi; ++t2) {
                    if (t2 == t) continue;
                    if (yi[t2]) {
                        int dd = std::abs(t2 - t) * 2 + (t2 > t ? 1 : 0);  // prefer earlier on ties
                        if (dd < bestDist) { bestDist = dd; mergeT = t2; }
                        continue;
                    }
                    Move mv{}; mv[0] = i; mv[1] = t; mv[2] = t2; out.push_back(mv);
                }
                if (mergeT >= 0) { Move mv{}; mv[0] = i; mv[1] = t; mv[2] = mergeT; out.push_back(mv); }
            }
            if (!any) {
                for (int t = 0; t < T; ++t) { Move mv{}; mv[0] = i; mv[1] = -1; mv[2] = t; out.push_back(mv); }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t) {
                    Move mv{}; mv[0] = i;
                    if (s[i][t]) { mv[1] = t; mv[2] = -1; } else { mv[1] = -1; mv[2] = t; }
                    out.push_back(mv);
                }
        }
    }
    Sol apply(const Sol& s, const Move& m) override { build(m); return CachedEvalR::apply(s, ch_); }
    double delta(const Sol& s, const Move& m) override { build(m); return ev_.delta(s, ch_); }
    Move tabu_key(const Move& m) override { Move k{}; k[0] = m[0]; k[1] = m[2]; k[2] = m[1]; return k; }
private:
    void build(const Move& m) {
        ch_.clear();
        if (m[1] >= 0) ch_.push_back({m[0], m[1], 0});
        if (m[2] >= 0) ch_.push_back({m[0], m[2], 1});
    }
    const Model& m_;
    CachedEvalR ev_;
    int W_;
    std::vector<std::array<int, 3>> ch_;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)std::lround(params.get("window", 2.0));
    return std::make_unique<SetupRelocate>(model, w);
}
