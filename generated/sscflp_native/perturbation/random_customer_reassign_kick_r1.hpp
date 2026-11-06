// COMPONENT: {"name": "random_customer_reassign_kick", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "p_open": {"type": "float", "range": [0.0, 1.0]}, "tries": {"type": "int", "range": [2, 30]}}}
class Core {
public:
    const Model& M;
    std::vector<double> load;
    std::vector<int> cnt, pend, perm;
    std::vector<char> forbid;
    explicit Core(const Model& md) : M(md), load(md.n, 0.0), cnt(md.n, 0), perm(md.m), forbid(md.n, 0) {
        std::iota(perm.begin(), perm.end(), 0);
    }
    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    bool fits(int i, int j) const { return load[i] + M.demand[j] <= M.capacity[i] + Model::EPS; }
    void add(std::vector<int>& a, int j, int i) { a[j] = i; load[i] += M.demand[j]; ++cnt[i]; }
    void rem(std::vector<int>& a, int j) { int i = a[j]; if (i >= 0) { load[i] -= M.demand[j]; --cnt[i]; } a[j] = -1; }
    void compute_loads(const std::vector<int>& a) {
        std::fill(load.begin(), load.end(), 0.0); std::fill(cnt.begin(), cnt.end(), 0);
        for (int j = 0; j < M.m; ++j) { int i = a[j]; if (i >= 0) { load[i] += M.demand[j]; ++cnt[i]; } }
    }
    bool insert_pending(std::vector<int>& a, Rng& rng, double noise) {
        std::shuffle(pend.begin(), pend.end(), rng.g);
        std::stable_sort(pend.begin(), pend.end(), [&](int x, int y) { return M.demand[x] > M.demand[y]; });
        bool ok = true;
        for (int j : pend) {
            int best = -1; double bv = std::numeric_limits<double>::infinity();
            for (int pass = 0; pass < 2 && best < 0; ++pass)
                for (int i = 0; i < M.n; ++i) {
                    if (pass == 0 && forbid[i]) continue;
                    if (!fits(i, j)) continue;
                    double v = cst(i, j) + (cnt[i] == 0 ? M.fixed[i] : 0.0);
                    if (noise > 0) v *= 1.0 + noise * rng.uniform();
                    if (v < bv) { bv = v; best = i; }
                }
            if (best < 0) {
                ok = false; double br = -std::numeric_limits<double>::infinity();
                for (int i = 0; i < M.n; ++i) { double r = M.capacity[i] - load[i]; if (r > br) { br = r; best = i; } }
            }
            add(a, j, best);
        }
        pend.clear();
        return ok;
    }
    bool repair(std::vector<int>& a, Rng& rng, double noise) {
        if ((int)a.size() != M.m) a.assign(M.m, -1);
        for (int j = 0; j < M.m; ++j) if (a[j] < 0 || a[j] >= M.n) a[j] = -1;
        compute_loads(a);
        pend.clear();
        for (int j = 0; j < M.m; ++j) if (a[j] < 0) pend.push_back(j);
        bool over = false;
        for (int i = 0; i < M.n; ++i) if (load[i] > M.capacity[i] + Model::EPS) { over = true; break; }
        if (over) {
            std::shuffle(perm.begin(), perm.end(), rng.g);
            for (int j : perm) { int i = a[j]; if (i >= 0 && load[i] > M.capacity[i] + Model::EPS) { rem(a, j); pend.push_back(j); } }
        }
        return insert_pending(a, rng, noise);
    }
    bool force_move(std::vector<int>& a, Rng& rng) {
        int n = M.n, m = M.m; if (m == 0 || n == 0) return false;
        int oj = rng.below(m), oi = rng.below(n);
        for (int x = 0; x < m; ++x) {
            int j = (oj + x) % m, cur = a[j];
            for (int y = 0; y < n; ++y) { int i = (oi + y) % n; if (i != cur && fits(i, j)) { rem(a, j); add(a, j, i); return true; } }
        }
        for (int x = 0; x < m; ++x) {
            int j1 = (oj + x) % m;
            for (int y = x + 1; y < m; ++y) {
                int j2 = (oj + y) % m; int i1 = a[j1], i2 = a[j2];
                if (i1 < 0 || i2 < 0 || i1 == i2) continue;
                double d1 = M.demand[j1], d2 = M.demand[j2];
                if (load[i1] - d1 + d2 <= M.capacity[i1] + Model::EPS && load[i2] - d2 + d1 <= M.capacity[i2] + Model::EPS) {
                    rem(a, j1); rem(a, j2); add(a, j1, i2); add(a, j2, i1); return true;
                }
            }
        }
        return false;
    }
    std::vector<int> finalize(const std::vector<int>& orig, std::vector<int> t, Rng& rng) {
        std::fill(forbid.begin(), forbid.end(), 0);
        bool ok = repair(t, rng, 0.0);
        if (ok && t != orig) return t;
        t = orig; ok = repair(t, rng, 0.0);
        if (ok && t != orig) return t;
        force_move(t, rng);
        return t;
    }
};

class RandomReassignKick : public hsf::Perturbation<Model> {
    const Model& M; Core C; double scale, p_open; int tries;
    std::vector<int> chosen, old, open;
public:
    RandomReassignKick(const Model& m, double sc, double po, int tr) : M(m), C(m), scale(sc), p_open(po), tries(tr) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        std::vector<int> orig = s.empty() ? std::vector<int>() : s[0];
        std::vector<int> t = orig;
        if (M.m == 0 || M.n == 0) return Sol{t};
        C.repair(t, rng, 0.0);
        int k = (int)std::lround(strength * scale); k = std::max(1, std::min(k, M.m));
        chosen.clear(); old.clear();
        for (int x = 0; x < k; ++x) {
            int y = x + rng.below(M.m - x); std::swap(C.perm[x], C.perm[y]);
            int j = C.perm[x]; chosen.push_back(j); old.push_back(t[j]); C.rem(t, j);
        }
        open.clear();
        for (int i = 0; i < M.n; ++i) if (C.cnt[i] > 0) open.push_back(i);
        for (int q = 0; q < k; ++q) {
            int j = chosen[q]; bool done = false;
            for (int r = 0; r < tries && !done; ++r) {
                int i = (!open.empty() && rng.uniform() < p_open) ? open[rng.below((int)open.size())] : rng.below(M.n);
                if (i != old[q] && C.fits(i, j)) { C.add(t, j, i); done = true; }
            }
            if (!done) C.pend.push_back(j);
        }
        C.insert_pending(t, rng, 0.0);
        return Sol{C.finalize(orig, t, rng)};
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("scale", 1.0);
    double po = params.get("p_open", 0.7);
    int tr = (int)params.get("tries", 8);
    return std::make_unique<RandomReassignKick>(model, sc, po, std::max(1, tr));
}
