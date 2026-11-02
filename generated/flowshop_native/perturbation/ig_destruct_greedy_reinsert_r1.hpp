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

    inline bool valid(int j) const { return j >= 0 && j < md.n; }

    void insertBest(std::vector<int>& v, int job, Rng& rng) {
        int L = (int)v.size();
        int m = md.m;
        if (m == 0) { v.insert(v.begin() + rng.below(L + 1), job); return; }
        E.assign((size_t)(L + 1) * m, 0);
        F.assign(L + 1, 0);
        for (int k = 0; k < L; ++k) {
            const long long* prev = &E[(size_t)k * m];
            long long* cur = &E[(size_t)(k + 1) * m];
            int j = v[k];
            if (!valid(j)) { std::copy(prev, prev + m, cur); F[k + 1] = F[k]; continue; }
            const long long* p = &md.pj[(size_t)j * m];
            cur[0] = prev[0] + p[0];
            for (int i = 1; i < m; ++i) cur[i] = std::max(prev[i], cur[i - 1]) + p[i];
            F[k + 1] = F[k] + cur[m - 1];
        }
        C.resize(m);
        long long best = std::numeric_limits<long long>::max();
        int bestPos = L;
        int ties = 0;
        for (int pos = 0; pos <= L; ++pos) {
            std::copy(&E[(size_t)pos * m], &E[(size_t)pos * m] + m, C.begin());
            long long sum = F[pos];
            bool cut = false;
            auto process = [&](int j) {
                if (!valid(j)) return;
                const long long* p = &md.pj[(size_t)j * m];
                C[0] += p[0];
                for (int i = 1; i < m; ++i) C[i] = std::max(C[i], C[i - 1]) + p[i];
                sum += C[m - 1];
            };
            process(job);
            if (sum > best) continue;
            for (int k = pos; k < L; ++k) {
                process(v[k]);
                if (sum > best) { cut = true; break; }
            }
            if (cut) continue;
            if (sum < best) { best = sum; bestPos = pos; ties = 1; }
            else if (sum == best) { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
        }
        v.insert(v.begin() + bestPos, job);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int db = (int)params.get("d_base", 2);
    double ds = params.get("d_scale", 1.0);
    return std::make_unique<IGDestructReinsert>(model, db, ds);
}
