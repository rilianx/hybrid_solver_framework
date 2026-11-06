// COMPONENT: {"name": "surrogate_dual_subgradient_greedy", "slot": "constructor", "params": {"rounds": {"type": "int", "range": [5, 80]}, "step": {"type": "float", "range": [0.05, 1.5]}, "decay": {"type": "float", "range": [0.8, 1.0]}, "noise": {"type": "float", "range": [0.0, 0.5]}}}
class Codec {
public:
    explicit Codec(const Model& md) : M(md), base(md.trivial()) {
        const int n = M.n;
        std::vector<char> T(n, 0);
        for (int j = 0; j < n; ++j) T[j] = M.chosen(base, j) ? 1 : 0;
        if (base.empty()) return;
        const std::vector<int>& r0 = base[0];
        if ((int)r0.size() == n) {
            bool ok = true;
            for (int j = 0; j < n && ok; ++j)
                if (!((r0[j] == 0 && !T[j]) || (r0[j] == 1 && T[j]))) ok = false;
            if (ok) { mode = 1; return; }
        }
        std::vector<char> seen(n, 0);
        bool ok = true;
        for (int v : r0) { if (v < 0 || v >= n || seen[v]) { ok = false; break; } seen[v] = 1; }
        for (int j = 0; j < n && ok; ++j) if (seen[j] != T[j]) ok = false;
        if (!ok) return;
        mode = 2;
        if (base.size() >= 2) {
            std::vector<char> s2(n, 0);
            bool c = true;
            for (int v : base[1]) { if (v < 0 || v >= n || s2[v] || T[v]) { c = false; break; } s2[v] = 1; }
            for (int j = 0; j < n && c; ++j) if (!T[j] && !s2[j]) c = false;
            comp = c;
        }
    }
    Model::Solution finalize(const std::vector<char>& x) const {
        if (mode == 0) return base;
        Model::Solution s = base;
        const int n = M.n;
        if (mode == 1) {
            s[0].assign(n, 0);
            for (int j = 0; j < n; ++j) if (x[j]) s[0][j] = 1;
        } else {
            s[0].clear();
            for (int j = 0; j < n; ++j) if (x[j]) s[0].push_back(j);
            if (comp) { s[1].clear(); for (int j = 0; j < n; ++j) if (!x[j]) s[1].push_back(j); }
        }
        for (int j = 0; j < n; ++j) if (M.chosen(s, j) != (x[j] != 0)) return base;
        if (!M.feasible(s)) return base;
        return s;
    }
private:
    const Model& M;
    Model::Solution base;
    int mode = 0;
    bool comp = false;
};

class SurrogateDualGreedy : public hsf::Constructor<Model> {
public:
    SurrogateDualGreedy(const Model& md, int r, double st, double dc, double nz)
        : M(md), codec(md), n(md.n), m(md.m), rounds(std::max(1, r)), step0(st), decay(dc), noise(nz) {
        lim.resize(m);
        capn.resize(m);
        for (int i = 0; i < m; ++i) {
            lim[i] = M.capacity[i] + 1e-9 * std::max(1.0, std::fabs(M.capacity[i]));
            capn[i] = std::max(M.capacity[i], 1e-12);
        }
    }
    Model::Solution build(Rng& rng) override {
        const double* w = M.wcol.data();
        u.resize(m);
        for (int i = 0; i < m; ++i) u[i] = (1.0 + noise * rng.uniform()) / capn[i];
        std::vector<double> ratio(n), cost(n), load(m), fl(m);
        std::vector<int> order(n);
        std::vector<char> x(n), bestx(n, 0);
        double bestVal = -std::numeric_limits<double>::infinity();
        double step = step0;
        for (int r = 0; r < rounds; ++r) {
            for (int j = 0; j < n; ++j) {
                const double* wj = w + (size_t)j * m;
                double c = 0.0;
                for (int i = 0; i < m; ++i) c += u[i] * wj[i];
                cost[j] = c;
                double jit = (r > 0 && noise > 0.0) ? 1.0 + 0.25 * noise * rng.uniform() : 1.0;
                ratio[j] = c > 0.0 ? M.profit[j] * jit / c : std::numeric_limits<double>::infinity();
            }
            std::iota(order.begin(), order.end(), 0);
            std::sort(order.begin(), order.end(), [&](int a, int b) {
                if (ratio[a] != ratio[b]) return ratio[a] > ratio[b];
                return a < b;
            });
            std::fill(load.begin(), load.end(), 0.0);
            std::fill(x.begin(), x.end(), 0);
            double val = 0.0;
            for (int j : order) {
                const double* wj = w + (size_t)j * m;
                bool ok = true;
                for (int i = 0; i < m; ++i) if (load[i] + wj[i] > lim[i]) { ok = false; break; }
                if (!ok) continue;
                for (int i = 0; i < m; ++i) load[i] += wj[i];
                x[j] = 1;
                val += M.profit[j];
            }
            if (val > bestVal) { bestVal = val; bestx = x; }
            // fractional solution of the surrogate relaxation
            double S = 0.0;
            for (int i = 0; i < m; ++i) S += u[i] * M.capacity[i];
            double used = 0.0;
            std::fill(fl.begin(), fl.end(), 0.0);
            for (int j : order) {
                const double* wj = w + (size_t)j * m;
                double c = cost[j];
                double f = 1.0;
                if (c > 0.0 && used + c > S) f = std::max(0.0, (S - used) / c);
                for (int i = 0; i < m; ++i) fl[i] += f * wj[i];
                used += f * c;
                if (f < 1.0) break;
            }
            double norm = 0.0;
            for (int i = 0; i < m; ++i) {
                double g = fl[i] / capn[i] - 1.0;
                g = std::max(-2.0, std::min(2.0, g));
                u[i] *= std::exp(step * g);
                u[i] = std::max(u[i], 1e-12 / capn[i]);
                norm += u[i] * capn[i];
            }
            if (norm > 0.0) for (int i = 0; i < m; ++i) u[i] *= (double)m / norm;
            step *= decay;
        }
        return codec.finalize(bestx);
    }
private:
    const Model& M;
    Codec codec;
    int n, m, rounds;
    double step0, decay, noise;
    std::vector<double> lim, capn, u;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int rounds = (int)params.get("rounds", 30);
    double step = params.get("step", 0.5);
    double decay = params.get("decay", 0.95);
    double noise = params.get("noise", 0.1);
    return std::make_unique<SurrogateDualGreedy>(model, rounds, step, decay, noise);
}
