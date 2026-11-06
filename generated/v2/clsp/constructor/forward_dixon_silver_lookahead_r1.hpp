// COMPONENT: {"name": "forward_dixon_silver_lookahead", "slot": "constructor", "params": {"lambda": {"type": "float", "range": [0.2, 2.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}, "st_est": {"type": "float", "range": [0.0, 1.0]}}}
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

class ForwardDixonSilver : public hsf::Constructor<Model> {
    const Model& m;
    double lambda, noise, stEst;
    std::vector<double> D, stE, E;
    std::vector<std::vector<double>> suf;
public:
    ForwardDixonSilver(const Model& mm, double l, double no, double se) : m(mm), lambda(l), noise(no), stEst(se) {
        int n = m.n, P = m.P;
        D.assign(P, 0.0); stE.assign(P, 0.0); E.assign(P, 0.0);
        for (int t = 0; t < P; ++t) for (int i = 0; i < n; ++i) {
            D[t] += m.d[i][t];
            if (m.d[i][t] > 1e-9) stE[t] += m.st[i];
        }
        for (int t = 0; t < P; ++t) stE[t] *= stEst;
        for (int t = P - 2; t >= 0; --t) E[t] = std::max(0.0, E[t + 1] + D[t + 1] + stE[t + 1] - m.cap[t + 1]);
        suf.assign(n, std::vector<double>(P + 1, 0.0));
        for (int i = 0; i < n; ++i) for (int t = P - 1; t >= 0; --t) suf[i][t] = suf[i][t + 1] + m.d[i][t];
    }
    Model::Solution build(Rng& rng) override {
        const double eps = 1e-9;
        int n = m.n, P = m.P;
        std::vector<double> sCoef(n);
        for (int i = 0; i < n; ++i) sCoef[i] = m.s[i] * lambda * std::max(0.0, 1.0 + noise * (2.0 * rng.uniform() - 1.0));
        std::vector<double> inv(n, 0.0), q(n, 0.0);
        std::vector<char> on(n, 0);
        std::vector<int> order(n);
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](int a, int b) { if (m.h[a] != m.h[b]) return m.h[a] < m.h[b]; return a < b; });
        Model::Solution y(n, std::vector<int>(P, 0));
        bool ok = true;
        for (int t = 0; t < P && ok; ++t) {
            double rem = m.cap[t];
            for (int i = 0; i < n; ++i) {
                q[i] = 0.0; on[i] = 0;
                double need = m.d[i][t] - inv[i];
                if (need > eps) { on[i] = 1; q[i] = need; rem -= m.st[i] + need; }
            }
            if (rem < -1e-7) { ok = false; break; }
            // economic lot extensions (Silver-Meal / Dixon-Silver style)
            while (true) {
                int bi = -1; double bestScore = 0.0, bamt = 0.0;
                for (int i = 0; i < n; ++i) {
                    if (!on[i]) continue;
                    double a = inv[i] + q[i] - m.d[i][t];
                    double cum = 0.0; int k = t + 1;
                    while (k < P) { cum += m.d[i][k]; if (cum > a + eps) break; ++k; }
                    if (k >= P) continue;
                    double amt = cum - a;
                    if (amt > rem + 1e-12 || amt <= eps) continue;
                    double gain = sCoef[i] - m.h[i] * amt * (k - t);
                    if (gain <= 0) continue;
                    double sc = gain / amt;
                    if (sc > bestScore) { bestScore = sc; bi = i; bamt = amt; }
                }
                if (bi < 0) break;
                q[bi] += bamt; rem -= bamt;
            }
            // feasibility lookahead: aggregate inventory needed for future capacity
            double endTot = 0.0;
            for (int i = 0; i < n; ++i) endTot += inv[i] + q[i] - m.d[i][t];
            double need = E[t] - endTot;
            if (need > eps) {
                for (int pass = 0; pass < 2 && need > eps; ++pass) {
                    for (int i : order) {
                        if (need <= eps || rem <= eps) break;
                        if (pass == 0 && !on[i]) continue;
                        if (pass == 1 && on[i]) continue;
                        double endI = inv[i] + q[i] - m.d[i][t];
                        double fut = suf[i][t + 1] - endI;
                        if (fut <= eps) continue;
                        if (!on[i]) {
                            if (rem <= m.st[i] + eps) continue;
                            on[i] = 1; rem -= m.st[i];
                        }
                        double amt = std::min(need, std::min(fut, rem));
                        if (amt <= 0) continue;
                        q[i] += amt; rem -= amt; need -= amt;
                    }
                }
            }
            for (int i = 0; i < n; ++i) {
                inv[i] = inv[i] + q[i] - m.d[i][t];
                if (inv[i] < 0) inv[i] = 0.0;
                y[i][t] = on[i] ? 1 : 0;
            }
        }
        return safeReturn(m, y);
    }
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<ForwardDixonSilver>(model, params.get("lambda", 1.0), params.get("noise", 0.2), params.get("st_est", 1.0));
}
