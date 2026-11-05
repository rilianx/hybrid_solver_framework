// COMPONENT: {"name": "setup_time_shift_merge", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "window": {"type": "int", "range": [1, 4]}, "early_bias": {"type": "float", "range": [0.0, 1.0]}, "attempts": {"type": "int", "range": [2, 20]}}}
using Sol = Model::Solution;

static Sol fallbackFlipSS(const Model& m, const Sol& s, Rng& rng) {
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

class SetupTimeShiftMerge : public hsf::Perturbation<Model> {
    const Model& m;
    double scale, earlyBias;
    int window, attempts;
    std::vector<int> ones;
public:
    SetupTimeShiftMerge(const Model& model, double sc, int w, double eb, int at)
        : m(model), scale(sc), earlyBias(eb), window(w), attempts(at) {}

    void shiftOne(Sol& y, Rng& rng) {
        int T = m.T;
        int i = rng.below(m.n);
        ones.clear();
        for (int t = 0; t < T; ++t) if (y[i][t]) ones.push_back(t);
        if (ones.empty()) { y[i][rng.below(T)] = 1; return; }
        int t = ones[rng.below((int)ones.size())];
        if (T == 1) { y[i][t] = 0; return; }
        int dir = rng.uniform() < earlyBias ? -1 : 1;
        int dist = 1 + rng.below(window);
        int t2 = t + dir * dist;
        if (t2 < 0 || t2 >= T) t2 = t - dir * dist;
        t2 = std::max(0, std::min(T - 1, t2));
        if (t2 == t) t2 = (t == 0) ? 1 : t - 1;
        y[i][t] = 0;     // si y[i][t2] ya era 1, esto es una fusión de lotes
        y[i][t2] = 1;
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        if (m.n == 0 || m.T == 0) return s;
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * scale));
        k = std::min(k, m.n * m.T);
        for (int a = 0; a < attempts; ++a) {
            Sol y = s;
            for (int f = 0; f < k; ++f) shiftOne(y, rng);
            if (y != s && m.feasible(y)) return y;
            if (a % 2 == 1) k = std::max(1, k / 2);
        }
        return fallbackFlipSS(m, s, rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("scale", 1.0);
    int w = (int)params.get("window", 2);
    double eb = params.get("early_bias", 0.6);
    int at = (int)params.get("attempts", 8);
    return std::make_unique<SetupTimeShiftMerge>(model, sc, std::max(1, w), eb, std::max(1, at));
}
