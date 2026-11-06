// COMPONENT: {"name": "random_feasible_setup_flips", "slot": "perturbation", "params": {"flips_per_strength": {"type": "float", "range": [0.5, 4.0]}, "p_remove": {"type": "float", "range": [0.2, 0.8]}, "tries_factor": {"type": "int", "range": [2, 10]}}}
using Sol = Model::Solution;

static const double kEps = 1e-6;

static double shortfallOf(const Model& m, const Sol& s) {
    double a = 0, b = 0, c = 0;
    m.evaluate(s, a, b, c);
    return c;
}

static Sol fallbackDistinct(const Model& m, const Sol& s, double base, Rng& rng) {
    int n = m.n, P = m.P;
    Sol c = s;
    if (n <= 0 || P <= 0) return c;
    std::vector<int> cells(n * P);
    std::iota(cells.begin(), cells.end(), 0);
    std::shuffle(cells.begin(), cells.end(), rng.g);
    for (int id : cells) {
        int i = id / P, t = id % P;
        c[i][t] ^= 1;
        if (shortfallOf(m, c) <= base + kEps) return c;
        c[i][t] ^= 1;
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    c[0][0] ^= 1;
    return c;
}

class RandomFeasibleSetupFlips : public hsf::Perturbation<Model> {
    const Model& m;
    double perStr, pRemove;
    int triesFactor;
    std::vector<int> buf;
public:
    RandomFeasibleSetupFlips(const Model& model, double ps, double pr, int tf)
        : m(model), perStr(ps), pRemove(pr), triesFactor(tf) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = m.n, P = m.P;
        if (n <= 0 || P <= 0) return s;
        Sol cur = s;
        double base = shortfallOf(m, cur);
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * perStr));
        int maxT = k * triesFactor + 10;
        int done = 0, tries = 0;
        while (done < k && tries < maxT) {
            ++tries;
            int i = rng.below(n);
            bool wantRemove = rng.uniform() < pRemove;
            int target = wantRemove ? 1 : 0;
            buf.clear();
            for (int t = 0; t < P; ++t) if (cur[i][t] == target) buf.push_back(t);
            int t;
            if (buf.empty()) t = rng.below(P);
            else t = buf[rng.below((int)buf.size())];
            cur[i][t] ^= 1;
            double v = shortfallOf(m, cur);
            if (v <= base + kEps) {
                ++done;
                base = std::min(base, v);
            } else {
                cur[i][t] ^= 1;
            }
        }
        if (cur != s) return cur;
        return fallbackDistinct(m, s, shortfallOf(m, s), rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("flips_per_strength", 1.5);
    double pr = params.get("p_remove", 0.5);
    int tf = (int)params.get("tries_factor", 4);
    return std::make_unique<RandomFeasibleSetupFlips>(model, ps, pr, std::max(1, tf));
}
