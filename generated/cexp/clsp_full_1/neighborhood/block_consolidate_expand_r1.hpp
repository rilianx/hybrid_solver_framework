// COMPONENT: {"name": "block_consolidate_expand", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [1, 8]}, "expand": {"type": "cat", "values": ["on", "off"]}}}
class CachedEvalB {
public:
    using Sol = Model::Solution;
    explicit CachedEvalB(const Model& m) : m_(m) {}
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

class BlockConsolidateExpand : public hsf::Neighborhood<Model> {
public:
    BlockConsolidateExpand(const Model& m, int L, bool expand) : m_(m), ev_(m), L_(std::max(1, L)), expand_(expand) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        const int n = m_.n, T = m_.T;
        for (int i = 0; i < n; ++i) {
            const std::vector<int>& yi = s[i];
            for (int a = 0; a < T; ++a) {
                int innerOnes = 0;
                int zeros = yi[a] ? 0 : 1;
                for (int len = 1; len <= L_ && a + len < T; ++len) {
                    int b = a + len;
                    if (yi[b]) ++innerOnes; else ++zeros;
                    if (innerOnes >= 1) {  // kind 0: consolidate [a,b] into a single setup at a
                        Move mv{}; mv[0] = i; mv[1] = a; mv[2] = b; mv[3] = 0; out.push_back(mv);
                    }
                    if (expand_ && zeros >= 2) {  // kind 1: open every setup in [a,b]
                        Move mv{}; mv[0] = i; mv[1] = a; mv[2] = b; mv[3] = 1; out.push_back(mv);
                    }
                }
            }
        }
        if (out.empty()) {  // fallback: single-cell flips
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < T; ++t) { Move mv{}; mv[0] = i; mv[1] = t; mv[2] = t; mv[3] = 2; out.push_back(mv); }
        }
    }
    Sol apply(const Sol& s, const Move& m) override { build(s, m); return CachedEvalB::apply(s, ch_); }
    double delta(const Sol& s, const Move& m) override { build(s, m); return ev_.delta(s, ch_); }
    Move tabu_key(const Move& m) override {
        Move k = m;
        if (m[3] == 0) k[3] = 1; else if (m[3] == 1) k[3] = 0;
        return k;
    }
private:
    void build(const Sol& s, const Move& m) {
        ch_.clear();
        int i = m[0], a = m[1], b = m[2], kind = m[3];
        if (kind == 0) {
            ch_.push_back({i, a, 1});
            for (int t = a + 1; t <= b; ++t) ch_.push_back({i, t, 0});
        } else if (kind == 1) {
            for (int t = a; t <= b; ++t) ch_.push_back({i, t, 1});
        } else {
            ch_.push_back({i, a, s[i][a] ? 0 : 1});
        }
    }
    const Model& m_;
    CachedEvalB ev_;
    int L_;
    bool expand_;
    std::vector<std::array<int, 3>> ch_;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)std::lround(params.get("max_len", 3.0));
    bool expand = params.text("expand", "on") == "on";
    return std::make_unique<BlockConsolidateExpand>(model, L, expand);
}
