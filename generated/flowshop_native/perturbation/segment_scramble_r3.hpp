// COMPONENT: {"name": "segment_scramble", "slot": "perturbation", "params": {"len_factor": {"type": "float", "range": [1.0, 4.0]}, "mode": {"type": "cat", "values": ["shuffle", "reverse", "rotate", "mixed"]}}}
class SegmentScramble : public hsf::Perturbation<Model> {
public:
    SegmentScramble(const Model& m, double lf, int mode) : md(m), lf_(lf), mode_(mode) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        auto rows = s.to_assignment();
        int R = (int)rows.size();
        if (R == 0) return s;
        int cnt = 0, row = -1;
        for (int k = 0; k < R; ++k) {
            if ((int)rows[k].size() >= 2) {
                ++cnt;
                if (rng.below(cnt) == 0) row = k;
            }
        }
        if (row < 0) return s;
        auto& v = rows[row];
        auto orig = v;
        int N = (int)v.size();
        int L = 2 + (int)std::lround(lf_ * std::max(1.0, strength));
        L = std::min(L, N);
        int a = rng.below(N - L + 1);
        auto b = v.begin() + a, e = v.begin() + a + L;
        int mode = mode_ == 3 ? rng.below(3) : mode_;
        if (mode == 0) {
            for (int i = L - 1; i > 0; --i) std::swap(b[i], b[rng.below(i + 1)]);
        } else if (mode == 1) {
            std::reverse(b, e);
        } else {
            int r = 1 + rng.below(L - 1);
            std::rotate(b, b + r, e);
        }
        if (v == orig) {
            int i = rng.below(N), j = rng.below(N - 1);
            if (j >= i) ++j;
            std::swap(v[i], v[j]);
        }
        return Sol(md, rows);
    }
private:
    const Model& md;
    double lf_;
    int mode_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double lf = params.get("len_factor", 2.0);
    std::string m = params.text("mode", "mixed");
    int mode = m == "shuffle" ? 0 : m == "reverse" ? 1 : m == "rotate" ? 2 : 3;
    return std::make_unique<SegmentScramble>(model, lf, mode);
}
