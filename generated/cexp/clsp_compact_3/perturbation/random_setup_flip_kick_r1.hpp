// COMPONENT: {"name": "random_setup_flip_kick", "slot": "perturbation", "params": {"flip_rate": {"type": "float", "range": [0.5, 3.0]}, "remove_prob": {"type": "float", "range": [0.2, 0.8]}, "max_tries": {"type": "int", "range": [3, 30]}}}
using Sol = Model::Solution;

static Sol fallbackPerturbA(const Model& m, const Sol& s, Rng& rng) {
    int n = (int)s.size(), T = n ? (int)s[0].size() : 0, N = n * T;
    if (N > 0) {
        Sol c = s;
        int off = rng.below(N);
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            int old = c[i][t];
            c[i][t] = old ? 0 : 1;
            if (m.feasible(c)) return c;
            c[i][t] = old;
        }
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            if (t + 1 < T && c[i][t] != c[i][t + 1]) {
                std::swap(c[i][t], c[i][t + 1]);
                if (m.feasible(c)) return c;
                std::swap(c[i][t], c[i][t + 1]);
            }
        }
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    if (N > 0) { Sol c = s; c[0][0] = c[0][0] ? 0 : 1; return c; }
    return s;
}

class RandomSetupFlipKick : public hsf::Perturbation<Model> {
public:
    RandomSetupFlipKick(const Model& m, double fr, double rp, int mt)
        : m_(m), flipRate_(fr), removeProb_(rp), maxTries_(std::max(1, mt)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = (int)s.size(), T = n ? (int)s[0].size() : 0, N = n * T;
        if (N == 0) return s;
        ones_.clear(); zeros_.clear();
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < T; ++t) (s[i][t] ? ones_ : zeros_).push_back(i * T + t);
        int k = std::max(1, (int)std::ceil(std::max(1.0, strength) * flipRate_));
        k = std::min(k, N);
        for (int tr = 0; tr < maxTries_; ++tr) {
            Sol c = s;
            int no = (int)ones_.size(), nz = (int)zeros_.size();
            int ro = 0, rz = 0, done = 0;
            for (int j = 0; j < k; ++j) {
                bool rem = rng.uniform() < removeProb_;
                if (rem && ro >= no) rem = false;
                if (!rem && rz >= nz) rem = true;
                if (rem && ro >= no) break;
                if (rem) {
                    int r = ro + rng.below(no - ro);
                    std::swap(ones_[ro], ones_[r]);
                    int idx = ones_[ro++];
                    c[idx / T][idx % T] = 0;
                } else {
                    int r = rz + rng.below(nz - rz);
                    std::swap(zeros_[rz], zeros_[r]);
                    int idx = zeros_[rz++];
                    c[idx / T][idx % T] = 1;
                }
                ++done;
            }
            if (done > 0 && m_.feasible(c)) return c;
            k = std::max(1, (k * 2) / 3);
        }
        return fallbackPerturbA(m_, s, rng);
    }

private:
    const Model& m_;
    double flipRate_, removeProb_;
    int maxTries_;
    std::vector<int> ones_, zeros_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<RandomSetupFlipKick>(model,
        params.get("flip_rate", 1.5), params.get("remove_prob", 0.5), (int)params.get("max_tries", 12));
}
