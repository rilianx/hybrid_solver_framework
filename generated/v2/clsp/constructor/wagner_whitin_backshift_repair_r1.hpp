// COMPONENT: {"name": "wagner_whitin_backshift_repair", "slot": "constructor", "params": {"bias": {"type": "float", "range": [0.3, 1.5]}, "noise": {"type": "float", "range": [0.0, 0.5]}}}
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

class WWBackshift : public hsf::Constructor<Model> {
    const Model& m;
    double bias, noise;
public:
    WWBackshift(const Model& mm, double b, double no) : m(mm), bias(b), noise(no) {}
    Model::Solution build(Rng& rng) override {
        const double eps = 1e-9;
        int n = m.n, P = m.P;
        std::vector<std::vector<double>> q(n, std::vector<double>(P, 0.0));
        std::vector<double> f(P + 1, 0.0);
        std::vector<int> pred(P + 1, 0);
        for (int i = 0; i < n; ++i) {
            double sc = std::max(0.0, m.s[i] * bias * (1.0 + noise * (2.0 * rng.uniform() - 1.0)));
            f[0] = 0.0;
            for (int k = 1; k <= P; ++k) {
                double best = std::numeric_limits<double>::infinity(); int bj = k - 1;
                double hold = 0.0, sumD = 0.0;
                for (int j = k - 1; j >= 0; --j) {
                    if (j < k - 1) { sumD += m.d[i][j + 1]; hold += m.h[i] * sumD; }
                    double lot = sumD + m.d[i][j];
                    double c = f[j] + hold + (lot > eps ? sc : 0.0);
                    if (c < best) { best = c; bj = j; }
                }
                f[k] = best; pred[k] = bj;
            }
            int k = P;
            while (k > 0) {
                int j = pred[k];
                double lot = 0;
                for (int l = j; l < k; ++l) lot += m.d[i][l];
                q[i][j] = lot;
                k = j;
            }
        }
        bool ok = true;
        for (int t = P - 1; t >= 0 && ok; --t) {
            while (true) {
                double load = 0;
                for (int i = 0; i < n; ++i) if (q[i][t] > eps) load += q[i][t] + m.st[i];
                if (load <= m.cap[t] + 1e-9) break;
                if (t == 0) { ok = false; break; }
                double ex = load - m.cap[t];
                double bestScore = std::numeric_limits<double>::infinity();
                int bi = -1; double bamt = 0;
                for (int i = 0; i < n; ++i) {
                    double a = q[i][t];
                    if (a <= eps) continue;
                    double addC = q[i][t - 1] > eps ? 0.0 : m.s[i];
                    double red = a + m.st[i];
                    double cFull = m.h[i] * a + addC - m.s[i];
                    double sc = cFull / std::min(red, ex);
                    if (sc < bestScore) { bestScore = sc; bi = i; bamt = a; }
                    if (a > ex + 1e-12) {
                        double cPart = m.h[i] * ex + addC;
                        double sp = cPart / ex;
                        if (sp < bestScore) { bestScore = sp; bi = i; bamt = ex; }
                    }
                }
                if (bi < 0) { ok = false; break; }
                q[bi][t - 1] += bamt;
                q[bi][t] -= bamt;
                if (q[bi][t] < eps) q[bi][t] = 0.0;
            }
        }
        Model::Solution y(n, std::vector<int>(P, 0));
        for (int i = 0; i < n; ++i) for (int t = 0; t < P; ++t) y[i][t] = q[i][t] > eps ? 1 : 0;
        (void)ok;
        return safeReturn(m, y);
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<WWBackshift>(model, params.get("bias", 1.0), params.get("noise", 0.15));
}
