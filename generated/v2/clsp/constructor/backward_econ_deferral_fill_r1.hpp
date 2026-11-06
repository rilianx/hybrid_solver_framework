// COMPONENT: {"name": "backward_econ_deferral_fill", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 3.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "margin": {"type": "float", "range": [0.0, 0.3]}}}
static Model::Solution backwardFill(const Model& m) {
    int n = m.n, P = m.P;
    Model::Solution y(n, std::vector<int>(P, 0));
    std::vector<double> r(n, 0.0);
    std::vector<int> idx(n);
    for (int t = P - 1; t >= 0; --t) {
        for (int i = 0; i < n; ++i) r[i] += m.d[i][t];
        std::iota(idx.begin(), idx.end(), 0);
        std::sort(idx.begin(), idx.end(), [&](int a, int b) { if (r[a] != r[b]) return r[a] > r[b]; return a < b; });
        double rem = m.cap[t];
        for (int i : idx) {
            if (r[i] <= 1e-9) break;
            if (rem <= m.st[i] + 1e-9) continue;
            double q = std::min(r[i], rem - m.st[i]);
            y[i][t] = 1; r[i] -= q; rem -= m.st[i] + q;
            if (r[i] < 1e-9) r[i] = 0.0;
        }
    }
    return y;
}

static Model::Solution safeReturn(const Model& m, const Model::Solution& cand) {
    if (m.feasible(cand)) return cand;
    int n = m.n, P = m.P;
    std::vector<Model::Solution> alts;
    alts.push_back(backwardFill(m));
    Model::Solution lfl(n, std::vector<int>(P, 0)), ones(n, std::vector<int>(P, 1));
    for (int i = 0; i < n; ++i) for (int t = 0; t < P; ++t) lfl[i][t] = m.d[i][t] > 1e-9 ? 1 : 0;
    alts.push_back(lfl); alts.push_back(ones); alts.push_back(m.trivial());
    for (auto& a : alts) if (m.feasible(a)) return a;
    alts.push_back(cand);
    double best = std::numeric_limits<double>::infinity(); int bi = 0;
    for (int k = 0; k < (int)alts.size(); ++k) {
        double a, b, sh; m.evaluate(alts[k], a, b, sh);
        if (sh < best) { best = sh; bi = k; }
    }
    return alts[bi];
}

class BackwardEconFill : public hsf::Constructor<Model> {
    const Model& m;
    double alpha, noise, margin;
    std::vector<double> capPre, demPre, stPre;
public:
    BackwardEconFill(const Model& mm, double a, double no, double mg) : m(mm), alpha(a), noise(no), margin(mg) {
        int P = m.P;
        capPre.assign(P + 1, 0.0); demPre.assign(P + 1, 0.0); stPre.assign(P + 1, 0.0);
        for (int t = 0; t < P; ++t) {
            double D = 0, S = 0;
            for (int i = 0; i < m.n; ++i) { D += m.d[i][t]; if (m.d[i][t] > 1e-9) S += m.st[i]; }
            capPre[t + 1] = capPre[t] + m.cap[t];
            demPre[t + 1] = demPre[t] + D;
            stPre[t + 1] = stPre[t] + S;
        }
    }
    Model::Solution run(Rng& rng, double a) {
        int n = m.n, P = m.P;
        Model::Solution y(n, std::vector<int>(P, 0));
        std::vector<double> r(n, 0.0), key(n, 0.0);
        std::vector<char> defer(n, 0);
        std::vector<int> cand; cand.reserve(n);
        for (int t = P - 1; t >= 0; --t) {
            for (int i = 0; i < n; ++i) { r[i] += m.d[i][t]; defer[i] = 0; }
            if (t > 0 && a > 0) {
                double slack = capPre[t] - demPre[t] - stPre[t] - margin * capPre[t];
                cand.clear();
                for (int i = 0; i < n; ++i) if (r[i] > 1e-9) {
                    cand.push_back(i);
                    key[i] = m.h[i] * r[i] / std::max(m.s[i], 1e-9);
                }
                std::sort(cand.begin(), cand.end(), [&](int x, int z) { if (key[x] != key[z]) return key[x] < key[z]; return x < z; });
                double used = 0;
                for (int i : cand) {
                    double f = std::max(0.0, 1.0 + noise * (2.0 * rng.uniform() - 1.0));
                    if (m.h[i] * r[i] < a * m.s[i] * f && used + r[i] <= slack) { defer[i] = 1; used += r[i]; }
                }
            }
            cand.clear();
            for (int i = 0; i < n; ++i) if (r[i] > 1e-9 && !defer[i]) cand.push_back(i);
            std::sort(cand.begin(), cand.end(), [&](int x, int z) { if (m.h[x] != m.h[z]) return m.h[x] > m.h[z]; return x < z; });
            double rem = m.cap[t];
            for (int i : cand) {
                if (rem <= m.st[i] + 1e-9) continue;
                double q = std::min(r[i], rem - m.st[i]);
                y[i][t] = 1; r[i] -= q; rem -= m.st[i] + q;
                if (r[i] < 1e-9) r[i] = 0.0;
            }
        }
        return y;
    }
    Model::Solution build(Rng& rng) override {
        Model::Solution sol;
        double as[3] = {alpha, alpha * 0.5, 0.0};
        for (int k = 0; k < 3; ++k) {
            if (k > 0 && as[k] == as[k - 1]) continue;
            sol = run(rng, as[k]);
            if (m.feasible(sol)) return sol;
        }
        return safeReturn(m, sol);
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<BackwardEconFill>(model, params.get("alpha", 1.0), params.get("noise", 0.2), params.get("margin", 0.05));
}
