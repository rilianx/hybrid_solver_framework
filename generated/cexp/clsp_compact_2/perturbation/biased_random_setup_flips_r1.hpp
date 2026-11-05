// COMPONENT: {"name": "biased_random_setup_flips", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "close_bias": {"type": "float", "range": [0.0, 1.0]}, "attempts": {"type": "int", "range": [2, 20]}}}
using Sol = Model::Solution;

static Sol fallbackFlipBF(const Model& m, const Sol& s, Rng& rng) {
    int n = m.n, T = m.T, N = n * T;
    if (N == 0) return s;
    std::vector<int> idx(N);
    std::iota(idx.begin(), idx.end(), 0);
    std::shuffle(idx.begin(), idx.end(), rng.g);
    Sol y = s;
    for (int c : idx) {
        int i = c / T, t = c % T;
        y[i][t] = 1 - y[i][t];
        if (m.feasible(y)) return y;
        y[i][t] = 1 - y[i][t];
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    y[idx[0] / T][idx[0] % T] = 1 - y[idx[0] / T][idx[0] % T];
    return y;
}

class BiasedRandomSetupFlips : public hsf::Perturbation<Model> {
    const Model& m;
    double scale, closeBias;
    int attempts;
public:
    BiasedRandomSetupFlips(const Model& model, double sc, double cb, int at)
        : m(model), scale(sc), closeBias(cb), attempts(at) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int N = m.n * m.T;
        if (N == 0) return s;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * scale));
        k = std::min(k, N);
        for (int a = 0; a < attempts; ++a) {
            Sol y = s;
            for (int f = 0; f < k; ++f) {
                int want = rng.uniform() < closeBias ? 1 : 0;
                int i = rng.below(m.n), t = rng.below(m.T);
                for (int tr = 0; tr < 8 && y[i][t] != want; ++tr) {
                    i = rng.below(m.n);
                    t = rng.below(m.T);
                }
                y[i][t] = 1 - y[i][t];
            }
            if (y != s && m.feasible(y)) return y;
            if (a % 2 == 1) k = std::max(1, k / 2);
        }
        return fallbackFlipBF(m, s, rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("scale", 1.0);
    double cb = params.get("close_bias", 0.5);
    int at = (int)params.get("attempts", 8);
    return std::make_unique<BiasedRandomSetupFlips>(model, sc, cb, std::max(1, at));
}
