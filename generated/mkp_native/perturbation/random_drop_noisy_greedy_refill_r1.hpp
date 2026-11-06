// COMPONENT: {"name": "random_drop_noisy_greedy_refill", "slot": "perturbation", "params": {"k_per_strength": {"type": "float", "range": [0.5, 4.0]}, "noise": {"type": "float", "range": [0.0, 0.6]}}}
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

class RandomDropNoisyRefill : public hsf::Perturbation<Model> {
    const Model& M; Codec codec; int n, m; double kps, noise;
    std::vector<double> ratio, lim, load, key;
    std::vector<int> order, clist, cand;
    std::vector<char> x, banned;

    bool fits(int j) const {
        const double* w = &M.wcol[(size_t)j * m];
        for (int i = 0; i < m; ++i) if (load[i] + w[i] > lim[i]) return false;
        return true;
    }
    void addItem(int j) { x[j] = 1; const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] += w[i]; }
    void remItem(int j) { x[j] = 0; const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] -= w[i]; }
    bool violated() const { for (int i = 0; i < m; ++i) if (load[i] > lim[i]) return true; return false; }

public:
    RandomDropNoisyRefill(const Model& md, double k, double nz) : M(md), codec(md), n(md.n), m(md.m), kps(k), noise(nz) {
        ratio.assign(n, 0.0); lim.assign(m, 0.0); load.assign(m, 0.0);
        for (int i = 0; i < m; ++i) lim[i] = M.capacity[i] + ((int)M.tol.size() == m ? 0.5 * std::max(0.0, M.tol[i]) : 0.0);
        for (int j = 0; j < n; ++j) {
            double s = 0;
            for (int i = 0; i < m; ++i) {
                double w = M.wcol[(size_t)j * m + i], c = M.capacity[i];
                s += c > 0 ? w / c : (w > 0 ? 1e9 : 0.0);
            }
            ratio[j] = s > 0 ? M.profit[j] / s : 1e300;
        }
        order.resize(n); std::iota(order.begin(), order.end(), 0);
        std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return ratio[a] > ratio[b]; });
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        codec.read(s, x);
        std::fill(load.begin(), load.end(), 0.0);
        for (int j = 0; j < n; ++j) if (x[j]) { const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] += w[i]; }
        banned.assign(n, 0);
        // repair an infeasible input: drop lowest-ratio items
        for (int t = n - 1; t >= 0 && violated(); --t) { int j = order[t]; if (x[j]) { remItem(j); banned[j] = 1; } }
        clist.clear();
        for (int j = 0; j < n; ++j) if (x[j]) clist.push_back(j);
        int sz = (int)clist.size();
        int k = std::max(1, (int)std::lround(strength * kps));
        k = std::min(k, sz);
        for (int t = 0; t < k; ++t) {
            int idx = t + rng.below(sz - t);
            std::swap(clist[t], clist[idx]);
            int j = clist[t]; remItem(j); banned[j] = 1;
        }
        if (noise <= 0) {
            for (int j : order) if (!x[j] && !banned[j] && fits(j)) addItem(j);
        } else {
            cand.clear(); key.assign(n, 0.0);
            for (int j : order) if (!x[j] && !banned[j]) { cand.push_back(j); key[j] = ratio[j] * (1.0 + noise * (2.0 * rng.uniform() - 1.0)); }
            std::stable_sort(cand.begin(), cand.end(), [&](int a, int b) { return key[a] > key[b]; });
            for (int j : cand) if (fits(j)) addItem(j);
        }
        return codec.write(s, x);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double k = std::min(4.0, std::max(0.5, params.get("k_per_strength", 1.5)));
    double nz = std::min(0.6, std::max(0.0, params.get("noise", 0.2)));
    return std::make_unique<RandomDropNoisyRefill>(model, k, nz);
}
