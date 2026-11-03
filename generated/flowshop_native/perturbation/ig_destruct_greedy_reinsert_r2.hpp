// COMPONENT: {"name": "ig_destruct_greedy_reinsert", "slot": "perturbation", "params": {"d_base": {"type": "int", "range": [1, 6]}, "d_scale": {"type": "float", "range": [0.0, 2.0]}}}
class IGDestructReinsert : public hsf::Perturbation<Model> {
public:
    IGDestructReinsert(const Model& m, int db, double ds) : md(m), dbase(db), dscale(ds) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out = s;
        if (out.empty()) return out;
        auto& v = out[0];
        int N = (int)v.size();
        if (N < 2) return out;
        int d = dbase + (int)std::lround(dscale * std::max(1.0, strength));
        d = std::max(1, std::min(N - 1, d));
        removed.clear();
        for (int t = 0; t < d; ++t) {
            int idx = rng.below((int)v.size());
            removed.push_back(v[idx]);
            v.erase(v.begin() + idx);
        }
        eValid = 0;
        for (int job : removed) insertBest(v, job, rng);
        if (v == s[0]) {
            int i = rng.below(N), j = rng.below(N - 1);
            if (j >= i) ++j;
            std::swap(v[i], v[j]);
        }
        return out;
    }
private:
    const Model& md;
    int dbase;
    double dscale;
    std::vector<int> removed;
    std::vector<long long> E, F, C;
    std::vector<int> V;
    int eValid = 0;  // filas de E/F/V válidas: 0..eValid

    inline bool valid(int j) const { return j >= 0 && j < md.n; }

    void insertBest(std::vector<int>& v, int job, Rng& rng) {
        int L = (int)v.size();
        int m = md.m;
        if (m == 0) { v.insert(v.begin() + rng.below(L + 1), job); return; }
        if (E.size() < (size_t)(L + 1) * m) E.resize((size_t)(L + 1) * m);
        if (F.size() < (size_t)(L + 1)) { F.resize(L + 1); V.resize(L + 1); }
        if (eValid <= 0) {
            std::fill(E.begin(), E.begin() + m, 0LL);
            F[0] = 0; V[0] = 0; eValid = 0;
        }
        const long long* pjb = md.pj.data();
        for (int k = eValid; k < L; ++k) {
            const long long* prev = &E[(size_t)k * m];
            long long* cur = &E[(size_t)(k + 1) * m];
            int j = v[k];
            if (!valid(j)) { std::copy(prev, prev + m, cur); F[k + 1] = F[k]; V[k + 1] = V[k]; continue; }
            const long long* p = pjb + (size_t)j * m;
            long long c = prev[0] + p[0];
            cur[0] = c;
            for (int i = 1; i < m; ++i) { long long a = prev[i]; c = (a > c ? a : c) + p[i]; cur[i] = c; }
            F[k + 1] = F[k] + c;
            V[k + 1] = V[k] + 1;
        }
        C.resize(m);
        long long* Cp = C.data();
        const long long FL = F[L];
        const int VL = V[L];
        const bool jobValid = valid(job);
        const long long* pjob = jobValid ? pjb + (size_t)job * m : nullptr;
        long long best = std::numeric_limits<long long>::max();
        int bestPos = L;
        int ties = 0;
        for (int pos = 0; pos <= L; ++pos) {
            const long long* Ep = &E[(size_t)pos * m];
            long long sum, dmin, dmax;
            if (jobValid) {
                long long c = Ep[0] + pjob[0];
                Cp[0] = c;
                dmin = dmax = c - Ep[0];
                for (int i = 1; i < m; ++i) {
                    long long a = Ep[i];
                    c = (a > c ? a : c) + pjob[i];
                    Cp[i] = c;
                    long long dd = c - a;
                    if (dd < dmin) dmin = dd;
                    if (dd > dmax) dmax = dd;
                }
                sum = F[pos] + c;
            } else {
                std::copy(Ep, Ep + m, Cp);
                sum = F[pos];
                dmin = dmax = 0;
            }
            if (sum > best) continue;
            bool cut = false;
            int k = pos;
            for (;; ++k) {
                long long lb = sum + (FL - F[k]) + (long long)(VL - V[k]) * dmin;
                if (dmin == dmax || k >= L) { sum = lb; break; }
                if (lb > best) { cut = true; break; }
                int j = v[k];
                if (!valid(j)) continue;
                const long long* p = pjb + (size_t)j * m;
                const long long* En = &E[(size_t)(k + 1) * m];
                long long c = Cp[0] + p[0];
                Cp[0] = c;
                dmin = dmax = c - En[0];
                for (int i = 1; i < m; ++i) {
                    long long a = Cp[i];
                    c = (a > c ? a : c) + p[i];
                    Cp[i] = c;
                    long long dd = c - En[i];
                    if (dd < dmin) dmin = dd;
                    if (dd > dmax) dmax = dd;
                }
                sum += c;
            }
            if (cut) continue;
            if (sum > best) continue;
            if (sum < best) { best = sum; bestPos = pos; ties = 1; }
            else { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
        }
        v.insert(v.begin() + bestPos, job);
        eValid = bestPos;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int db = (int)params.get("d_base", 2);
    double ds = params.get("d_scale", 1.0);
    return std::make_unique<IGDestructReinsert>(model, db, ds);
}
