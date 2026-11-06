// COMPONENT: {"name": "open_facility_attract_customers", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.2, 1.5]}, "sample": {"type": "int", "range": [1, 20]}, "accept_neg": {"type": "float", "range": [0.0, 0.5]}}}
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
    bool try_swap(std::vector<int>& a, int j1, int j2) {
        int i1 = a[j1], i2 = a[j2];
        if (i1 < 0 || i2 < 0 || i1 == i2) return false;
        double d1 = M.demand[j1], d2 = M.demand[j2];
        if (load[i1] - d1 + d2 <= M.capacity[i1] + Model::EPS && load[i2] - d2 + d1 <= M.capacity[i2] + Model::EPS) {
            rem(a, j1); rem(a, j2); add(a, j1, i2); add(a, j2, i1); return true;
        }
        return false;
    }
    bool force_move(std::vector<int>& a, Rng& rng) {
        int n = M.n, m = M.m; if (m == 0 || n == 0) return false;
        int oj = rng.below(m), oi = rng.below(n);
        for (int x = 0; x < m; ++x) {
            int j = (oj + x) % m, cur = a[j];
            for (int y = 0; y < n; ++y) { int i = (oi + y) % n; if (i != cur && fits(i, j)) { rem(a, j); add(a, j, i); return true; } }
        }
        for (int x = 0; x < m; ++x)
            for (int y = x + 1; y < m; ++y) if (try_swap(a, (oj + x) % m, (oj + y) % m)) return true;
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

class OpenFacilityAttract : public hsf::Perturbation<Model> {
    const Model& M; Core C; double scale; int sample; double accept_neg;
    std::vector<int> closed; std::vector<std::pair<double, int>> cand;
public:
    OpenFacilityAttract(const Model& m, double sc, int sa, double an) : M(m), C(m), scale(sc), sample(sa), accept_neg(an) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        std::vector<int> orig = s.empty() ? std::vector<int>() : s[0];
        std::vector<int> t = orig;
        if (M.m == 0 || M.n == 0) return Sol{t};
        C.repair(t, rng, 0.0);
        int k = std::max(1, (int)std::lround(strength * scale));
        closed.clear();
        for (int i = 0; i < M.n; ++i) if (C.cnt[i] == 0) closed.push_back(i);
        if (closed.empty()) {
            int done = 0, kk = std::max(1, (int)std::lround(strength));
            for (int tr = 0; tr < 50 * kk && done < kk; ++tr)
                if (C.try_swap(t, rng.below(M.m), rng.below(M.m))) ++done;
            return Sol{C.finalize(orig, t, rng)};
        }
        k = std::min(k, (int)closed.size());
        for (int r = 0; r < k && !closed.empty(); ++r) {
            int bestq = -1; double bs = -std::numeric_limits<double>::infinity();
            for (int z = 0; z < sample; ++z) {
                int q = rng.below((int)closed.size()); int i = closed[q];
                double sc = -M.fixed[i];
                for (int j = 0; j < M.m; ++j) { double g = C.cst(t[j], j) - C.cst(i, j); if (g > 0) sc += g; }
                if (sc > bs) { bs = sc; bestq = q; }
            }
            int i = closed[bestq];
            closed[bestq] = closed.back(); closed.pop_back();
            cand.clear();
            int bestNeg = -1; double bng = -std::numeric_limits<double>::infinity();
            for (int j = 0; j < M.m; ++j) {
                if (t[j] == i) continue;
                double g = C.cst(t[j], j) - C.cst(i, j);
                if (g >= -accept_neg * C.cst(i, j)) cand.push_back({g, j});
                if (g > bng && C.fits(i, j)) { bng = g; bestNeg = j; }
            }
            std::sort(cand.begin(), cand.end(), [](const std::pair<double, int>& x, const std::pair<double, int>& y) { return x.first > y.first; });
            int moved = 0;
            for (auto& p : cand) {
                int j = p.second;
                if (C.fits(i, j)) { C.rem(t, j); C.add(t, j, i); ++moved; }
            }
            if (moved == 0 && bestNeg >= 0 && C.fits(i, bestNeg)) { C.rem(t, bestNeg); C.add(t, bestNeg, i); }
        }
        return Sol{C.finalize(orig, t, rng)};
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double sc = params.get("scale", 0.5);
    int sa = (int)params.get("sample", 4);
    double an = params.get("accept_neg", 0.0);
    return std::make_unique<OpenFacilityAttract>(model, sc, std::max(1, sa), an);
}
