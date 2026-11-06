// COMPONENT: {"name": "random_flip_kick_excess_repair", "slot": "perturbation", "params": {"k_per_strength": {"type": "float", "range": [1.0, 6.0]}, "add_prob": {"type": "float", "range": [0.2, 0.8]}}}
using Sol = Model::Solution;

struct Codec {
    const Model& M; int fmt = -1;
    explicit Codec(const Model& md) : M(md) {}
    void read(const Sol& s, std::vector<char>& x) const {
        x.assign(M.n, 0);
        for (int j = 0; j < M.n; ++j) x[j] = M.chosen(s, j) ? 1 : 0;
    }
    Sol encode(int f, const Sol& tpl, const std::vector<char>& x) const {
        int n = M.n;
        if (f == 0) { Sol r = tpl; if (r.empty()) r.emplace_back(); r[0].assign(n, 0); for (int j = 0; j < n; ++j) r[0][j] = x[j]; return r; }
        if (f == 1) { Sol r = tpl; if (r.empty()) r.emplace_back(); r[0].clear(); for (int j = 0; j < n; ++j) if (x[j]) r[0].push_back(j); return r; }
        Sol r(n, std::vector<int>(1, 0)); for (int j = 0; j < n; ++j) r[j][0] = x[j]; return r;
    }
    bool check(const Sol& r, const std::vector<char>& x) const {
        for (int j = 0; j < M.n; ++j) if ((M.chosen(r, j) ? 1 : 0) != x[j]) return false;
        return true;
    }
    Sol write(const Sol& tpl, const std::vector<char>& x) {
        if (fmt >= 0) return encode(fmt, tpl, x);
        int first = 1;
        if (!tpl.empty() && (int)tpl[0].size() == M.n) {
            bool bin = true; for (int v : tpl[0]) if (v != 0 && v != 1) { bin = false; break; }
            if (bin) first = 0;
        } else if ((int)tpl.size() == M.n && M.n > 1) {
            bool one = true; for (auto& v : tpl) if (v.size() != 1) { one = false; break; }
            if (one) first = 2;
        }
        int order[3] = {first, first == 0 ? 1 : 0, first == 2 ? 1 : 2};
        for (int f : order) { Sol r = encode(f, tpl, x); if (check(r, x)) { fmt = f; return r; } }
        fmt = first; return encode(first, tpl, x);
    }
};

class FlipKickExcessRepair : public hsf::Perturbation<Model> {
    const Model& M; Codec codec; int n, m; double kps, addp;
    std::vector<double> wn, ratio, lim, load, excess;
    std::vector<int> order, C, U;
    std::vector<char> x, x0, banned, prot;

    bool fits(int j) const {
        const double* w = &M.wcol[(size_t)j * m];
        for (int i = 0; i < m; ++i) if (load[i] + w[i] > lim[i]) return false;
        return true;
    }
    void addItem(int j) { x[j] = 1; const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] += w[i]; }
    void remItem(int j) { x[j] = 0; const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] -= w[i]; }
    bool computeExcess() {
        bool any = false;
        for (int i = 0; i < m; ++i) {
            double e = load[i] - lim[i];
            if (e > 0) { double c = M.capacity[i]; excess[i] = c > 0 ? e / c : e; any = true; }
            else excess[i] = 0;
        }
        return any;
    }
    void repair() {
        while (computeExcess()) {
            int best = -1; double bs = -1; bool bestProt = true;
            for (int j = 0; j < n; ++j) if (x[j]) {
                const double* w = &wn[(size_t)j * m];
                double c = 0; for (int i = 0; i < m; ++i) if (excess[i] > 0) c += w[i] * excess[i];
                if (c <= 0) continue;
                double sc = c / std::max(1e-9, std::fabs(M.profit[j]));
                bool p = prot[j] != 0;
                if (best < 0 || (bestProt && !p) || (p == bestProt && sc > bs)) { best = j; bs = sc; bestProt = p; }
            }
            if (best < 0) break;
            remItem(best); banned[best] = 1;
        }
    }
    void fill() { for (int j : order) if (!x[j] && !banned[j] && fits(j)) addItem(j); }

public:
    FlipKickExcessRepair(const Model& md, double k, double ap) : M(md), codec(md), n(md.n), m(md.m), kps(k), addp(ap) {
        wn.assign((size_t)n * m, 0.0); ratio.assign(n, 0.0); lim.assign(m, 0.0); load.assign(m, 0.0); excess.assign(m, 0.0);
        for (int i = 0; i < m; ++i) lim[i] = M.capacity[i] + ((int)M.tol.size() == m ? 0.5 * std::max(0.0, M.tol[i]) : 0.0);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int i = 0; i < m; ++i) {
                double w = M.wcol[(size_t)j * m + i], c = M.capacity[i];
                double v = c > 0 ? w / c : (w > 0 ? 1e9 : 0.0);
                wn[(size_t)j * m + i] = v; s += v;
            }
            ratio[j] = s > 0 ? M.profit[j] / s : 1e300;
        }
        order.resize(n); std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        codec.read(s, x);
        x0 = x;
        std::fill(load.begin(), load.end(), 0.0);
        for (int j = 0; j < n; ++j) if (x[j]) { const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] += w[i]; }
        banned.assign(n, 0); prot.assign(n, 0);
        C.clear(); U.clear();
        for (int j = 0; j < n; ++j) (x[j] ? C : U).push_back(j);

        int k = std::max(1, (int)std::lround(strength * kps));
        for (int t = 0; t < k; ++t) {
            bool doAdd = rng.uniform() < addp;
            if (doAdd && U.empty()) doAdd = false;
            if (!doAdd && C.empty()) doAdd = !U.empty();
            if (doAdd) {
                if (U.empty()) break;
                int idx = rng.below((int)U.size()); int j = U[idx]; U[idx] = U.back(); U.pop_back();
                addItem(j); prot[j] = 1;
            } else {
                if (C.empty()) break;
                int idx = rng.below((int)C.size()); int j = C[idx]; C[idx] = C.back(); C.pop_back();
                remItem(j); banned[j] = 1;
            }
        }
        repair();
        fill();
        if (x == x0) {
            C.clear();
            for (int j = 0; j < n; ++j) if (x[j]) C.push_back(j);
            if (!C.empty()) {
                int j = C[rng.below((int)C.size())];
                remItem(j); banned[j] = 1;
                fill();
            }
        }
        return codec.write(s, x);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double k = std::min(6.0, std::max(1.0, params.get("k_per_strength", 2.0)));
    double ap = std::min(0.8, std::max(0.2, params.get("add_prob", 0.5)));
    return std::make_unique<FlipKickExcessRepair>(model, k, ap);
}
