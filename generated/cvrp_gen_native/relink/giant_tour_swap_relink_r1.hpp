// COMPONENT: {"name": "giant_tour_swap_relink", "slot": "relink", "params": {"length_first": {"type": "float", "range": [0.0, 1.0]}}}
class GiantTourSwapRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    GiantTourSwapRelink(const Model& m, double lf) : m_(m), lenFirst_(lf) {}

    int distance(const Sol& a, const Sol& b) override {
        encode(a, ea_);
        encode(b, eb_);
        int d = ham(ea_, eb_);
        if (d == 0 && a != b) d = 1;
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        encode(cur, ea_);
        encode(guide, eb_);
        std::vector<int>& c = ea_;
        const std::vector<int>& g = eb_;
        if (ham(c, g) == 0) return guide;
        const int Lc = (int)c.size(), Lg = (int)g.size();
        const int Lm = std::min(Lc, Lg);
        M_.clear();
        for (int i = 0; i < Lm; ++i) if (c[i] != g[i]) M_.push_back(i);
        bool lenDiff = (Lc != Lg);
        bool done = false;
        if (!M_.empty() && !(lenDiff && rng.uniform() < lenFirst_)) {
            int i = M_[rng.below((int)M_.size())];
            int t = g[i];
            src_.clear();
            for (int j = 0; j < Lc; ++j)
                if (j != i && c[j] == t && (j >= Lg || c[j] != g[j])) src_.push_back(j);
            if (!src_.empty()) {
                int j = src_[rng.below((int)src_.size())];
                std::swap(c[i], c[j]);
                done = true;
            } else if (!lenDiff) {
                c[i] = t;
                done = true;
            }
        }
        if (!done) {
            if (Lc > Lg) {
                int t = c.back();
                c.pop_back();
                if (t != SEP) {
                    src_.clear();
                    for (int j = 0; j < (int)c.size(); ++j)
                        if (c[j] == SEP && (j >= Lg || c[j] != g[j])) src_.push_back(j);
                    if (!src_.empty()) c[src_[rng.below((int)src_.size())]] = t;
                }
            } else if (Lc < Lg) {
                int t = g[Lc];
                if (t != SEP) {
                    for (int j = 0; j < Lc; ++j)
                        if (c[j] == t && c[j] != g[j]) { c[j] = SEP; break; }
                }
                c.push_back(t);
            } else {
                return guide;
            }
        }
        if (c == g) return guide;
        return decode(c);
    }

private:
    static constexpr int SEP = std::numeric_limits<int>::min();
    const Model& m_;
    double lenFirst_;
    std::vector<int> ea_, eb_, M_, src_;

    static void encode(const Sol& s, std::vector<int>& e) {
        e.clear();
        for (size_t i = 0; i < s.size(); ++i) {
            e.insert(e.end(), s[i].begin(), s[i].end());
            if (i + 1 < s.size()) e.push_back(SEP);
        }
    }
    static int ham(const std::vector<int>& a, const std::vector<int>& b) {
        size_t L = std::min(a.size(), b.size());
        int d = (int)(std::max(a.size(), b.size()) - L);
        for (size_t i = 0; i < L; ++i) if (a[i] != b[i]) ++d;
        return d;
    }
    static Sol decode(const std::vector<int>& e) {
        Sol s(1);
        for (int t : e) {
            if (t == SEP) s.emplace_back();
            else s.back().push_back(t);
        }
        return s;
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double lf = params.get("length_first", 0.3);
    return std::make_unique<GiantTourSwapRelink>(model, lf);
}
