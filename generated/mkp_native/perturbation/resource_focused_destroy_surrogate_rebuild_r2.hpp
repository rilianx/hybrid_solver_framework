// COMPONENT: {"name": "resource_focused_destroy_surrogate_rebuild", "slot": "perturbation", "params": {"destroy_frac": {"type": "float", "range": [0.15, 0.7]}, "focus_bias": {"type": "float", "range": [0.0, 1.0]}, "multiplier_spread": {"type": "float", "range": [0.0, 2.0]}, "focus_weight": {"type": "float", "range": [1.0, 8.0]}}}
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

class ResourceFocusedSurrogate : public hsf::Perturbation<Model> {
    const Model& M; Codec codec; int n, m; double kps, fbias, spread, fw;
    std::vector<double> wn, ratio, lim, load, key, mult, score;
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
    ResourceFocusedSurrogate(const Model& md, double k, double fb, double sp, double w)
        : M(md), codec(md), n(md.n), m(md.m), kps(k), fbias(fb), spread(sp), fw(w) {
        wn.assign((size_t)n * m, 0.0); ratio.assign(n, 0.0); lim.assign(m, 0.0); load.assign(m, 0.0);
        mult.assign(m, 1.0); key.assign(n, 0.0); score.assign(n, 0.0);
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
        std::fill(load.begin(), load.end(), 0.0);
        for (int j = 0; j < n; ++j) if (x[j]) { const double* w = &M.wcol[(size_t)j * m]; for (int i = 0; i < m; ++i) load[i] += w[i]; }
        banned.assign(n, 0);
        for (int t = n - 1; t >= 0 && violated(); --t) { int j = order[t]; if (x[j]) { remItem(j); banned[j] = 1; } }

        // choose focus resource
        int r = 0;
        if (m > 0) {
            if (rng.uniform() < fbias) {
                double best = -1e300;
                for (int i = 0; i < m; ++i) {
                    double c = M.capacity[i];
                    double t = c > 0 ? load[i] / c : (load[i] > 0 ? 1e9 : 1.0);
                    if (t > best) { best = t; r = i; }
                }
            } else r = rng.below(m);
        }
        clist.clear();
        for (int j = 0; j < n; ++j) if (x[j]) {
            clist.push_back(j);
            double pr = std::max(1e-9, std::fabs(M.profit[j]));
            double c = m > 0 ? wn[(size_t)j * m + r] : 0.0;
            score[j] = (c + 1e-9) / std::sqrt(pr) * (0.85 + 0.3 * rng.uniform());
        }
        int sz = (int)clist.size();
        double st = std::max(0.0, strength);
        double frac = std::min(0.85, kps * (0.75 + 0.25 * st));
        int k = std::min(sz, std::max(std::min(sz, 2), (int)std::ceil(frac * sz)));
        if (k > 0) {
            std::partial_sort(clist.begin(), clist.begin() + k, clist.end(), [&](int a, int b) { return score[a] > score[b]; });
            for (int t = 0; t < k; ++t) { remItem(clist[t]); banned[clist[t]] = 1; }
        }

        // surrogate rebuild with random multipliers
        for (int i = 0; i < m; ++i) mult[i] = std::exp(spread * (2.0 * rng.uniform() - 1.0));
        if (m > 0) mult[r] *= fw;
        cand.clear();
        for (int j : order) if (!x[j] && !banned[j]) {
            const double* w = &wn[(size_t)j * m];
            double d = 0; for (int i = 0; i < m; ++i) d += mult[i] * w[i];
            key[j] = d > 0 ? M.profit[j] / d : 1e300;
            cand.push_back(j);
        }
        std::stable_sort(cand.begin(), cand.end(), [&](int a, int b) { return key[a] > key[b]; });
        for (int j : cand) if (fits(j)) addItem(j);
        for (int t = 0; t < k; ++t) { int j = clist[t]; if (!x[j] && fits(j)) addItem(j); }
        return codec.write(s, x);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double k = std::min(0.7, std::max(0.15, params.get("destroy_frac", 0.35)));
    double fb = std::min(1.0, std::max(0.0, params.get("focus_bias", 0.7)));
    double sp = std::min(2.0, std::max(0.0, params.get("multiplier_spread", 0.5)));
    double w = std::min(8.0, std::max(1.0, params.get("focus_weight", 3.0)));
    return std::make_unique<ResourceFocusedSurrogate>(model, k, fb, sp, w);
}
