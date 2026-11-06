// COMPONENT: {"name": "segment_double_bridge_exchange", "slot": "perturbation", "params": {"max_seg_frac": {"type": "float", "range": [0.05, 0.5]}, "bridges_per_strength": {"type": "float", "range": [0.5, 3.0]}, "reverse_prob": {"type": "float", "range": [0.0, 0.5]}}}
class SegmentDoubleBridge : public hsf::Perturbation<Model> {
public:
    SegmentDoubleBridge(const Model& m, double f, double bps, double rp)
        : M(m), frac_(f), bps_(bps), revProb_(rp) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        const int n = M.n;
        sanitize(s);
        Model::Solution out(1);
        std::vector<int>& perm = out[0];
        perm = work_;
        if (n >= 3) {
            int maxL = std::max(1, (int)std::lround(frac_ * n));
            int k = std::max(1, (int)std::lround(bps_ * std::max(1.0, strength)));
            for (int t = 0; t < k; ++t) {
                int p1 = rng.below(n - 1);           // start of block B
                int room = n - p1;                   // >= 2
                int lb = 1 + rng.below(std::min(maxL, room - 1));
                int p2 = p1 + lb;
                int lc = 1 + rng.below(std::min(maxL, n - p2));
                int p3 = p2 + lc;
                std::rotate(perm.begin() + p1, perm.begin() + p2, perm.begin() + p3);
                if (rng.uniform() < revProb_) {
                    // reverse what is now the moved block B (positions p1+lc .. p3)
                    std::reverse(perm.begin() + p1 + lc, perm.begin() + p3);
                }
            }
        } else if (n == 2) {
            std::swap(perm[0], perm[1]);
        }
        if (n >= 2 && s.size() == 1 && s[0] == perm) {
            int a = rng.below(n);
            int b = rng.below(n - 1);
            if (b >= a) ++b;
            std::swap(perm[a], perm[b]);
        }
        return out;
    }

private:
    void sanitize(const Model::Solution& s) {
        const int n = M.n;
        work_.clear();
        seen_.assign(n, 0);
        if (!s.empty())
            for (int x : s[0])
                if (x >= 0 && x < n && !seen_[x]) { seen_[x] = 1; work_.push_back(x); }
        for (int j = 0; j < n; ++j) if (!seen_[j]) work_.push_back(j);
    }
    const Model& M;
    double frac_, bps_, revProb_;
    std::vector<int> work_;
    std::vector<char> seen_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double f = params.get("max_seg_frac", 0.15);
    double bps = params.get("bridges_per_strength", 1.0);
    double rp = params.get("reverse_prob", 0.1);
    return std::make_unique<SegmentDoubleBridge>(model, f, bps, rp);
}
