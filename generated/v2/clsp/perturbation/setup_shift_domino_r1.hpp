// COMPONENT: {"name": "setup_shift_domino", "slot": "perturbation", "params": {"shifts_per_strength": {"type": "float", "range": [0.5, 4.0]}, "max_radius": {"type": "int", "range": [1, 6]}, "p_chain": {"type": "float", "range": [0.0, 0.8]}}}
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

class SetupShiftDomino : public hsf::Perturbation<Model> {
    const Model& m;
    double perStr, pChain;
    int radius;
    std::vector<int> ones, cand;

    // try to move setup (i,t) by a random offset in direction dir (0 = any); returns new period or -1
    int tryShift(Sol& cur, int i, int t, int dir, double& base, Rng& rng) {
        int P = m.P;
        cand.clear();
        for (int dlt = 1; dlt <= radius; ++dlt) {
            if (dir >= 0 && t + dlt < P && !cur[i][t + dlt]) cand.push_back(t + dlt);
            if (dir <= 0 && t - dlt >= 0 && !cur[i][t - dlt]) cand.push_back(t - dlt);
        }
        if (cand.empty()) return -1;
        std::shuffle(cand.begin(), cand.end(), rng.g);
        int lim = std::min<int>(2, (int)cand.size());
        for (int c = 0; c < lim; ++c) {
            int t2 = cand[c];
            cur[i][t] = 0; cur[i][t2] = 1;
            double v = shortfallOf(m, cur);
            if (v <= base + kEps) { base = std::min(base, v); return t2; }
            cur[i][t] = 1; cur[i][t2] = 0;
        }
        return -1;
    }

public:
    SetupShiftDomino(const Model& model, double ps, int r, double pc)
        : m(model), perStr(ps), pChain(pc), radius(std::max(1, r)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = m.n, P = m.P;
        if (n <= 0 || P <= 0) return s;
        Sol cur = s;
        double base = shortfallOf(m, cur);
        int k = std::max(1, (int)std::lround(std::max(1.0, strength) * perStr));
        int maxT = 4 * k + 10;
        int done = 0, tries = 0;
        while (done < k && tries < maxT) {
            ++tries;
            int i = rng.below(n);
            ones.clear();
            for (int t = 0; t < P; ++t) if (cur[i][t]) ones.push_back(t);
            if (ones.empty()) continue;
            int t = ones[rng.below((int)ones.size())];
            int t2 = tryShift(cur, i, t, 0, base, rng);
            if (t2 < 0) continue;
            ++done;
            int dir = (t2 > t) ? 1 : -1;
            // domino: push the next setup of the same item in the same direction
            int pos = t2;
            while (done < k && rng.uniform() < pChain) {
                int nxt = -1;
                for (int u = pos + dir; u >= 0 && u < P; u += dir)
                    if (cur[i][u]) { nxt = u; break; }
                if (nxt < 0) break;
                int moved = tryShift(cur, i, nxt, dir, base, rng);
                if (moved < 0) break;
                ++done;
                pos = moved;
            }
        }
        if (cur != s) return cur;
        return fallbackDistinct(m, s, shortfallOf(m, s), rng);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("shifts_per_strength", 1.5);
    int r = (int)params.get("max_radius", 2);
    double pc = params.get("p_chain", 0.3);
    return std::make_unique<SetupShiftDomino>(model, ps, r, pc);
}
