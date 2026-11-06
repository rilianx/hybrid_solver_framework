// COMPONENT: {"name": "iterated_greedy_destruct_reconstruct", "slot": "perturbation", "params": {"removed_per_strength": {"type": "float", "range": [1.0, 4.0]}, "max_removed": {"type": "int", "range": [2, 20]}, "removal": {"type": "cat", "values": ["random", "block"]}}}
class IteratedGreedyDestructReconstruct : public hsf::Perturbation<Model> {
    const Model& M;
    double rps;
    int maxr;
    bool block;
    std::vector<char> seen, mark;
    std::vector<int> perm, removed, seq, idx;
    std::vector<long long> C, F, row;

    void to_perm(const Model::Solution& s) {
        perm.clear();
        perm.reserve(M.n);
        seen.assign(M.n, 0);
        if (!s.empty())
            for (int j : s[0])
                if (j >= 0 && j < M.n && !seen[j]) { seen[j] = 1; perm.push_back(j); }
        for (int j = 0; j < M.n; ++j) if (!seen[j]) perm.push_back(j);
    }

    // recalcula filas de prefijo desde la posición 'from' (filas from+1..L)
    void rebuild(int from) {
        int m = M.m, L = (int)seq.size();
        C.resize((size_t)(L + 1) * m);
        F.resize(L + 1);
        if (from == 0) { std::fill(C.begin(), C.begin() + m, 0LL); F[0] = 0; }
        const long long* p = M.pj.data();
        for (int t = from + 1; t <= L; ++t) {
            int j = seq[t - 1];
            const long long* pr = &C[(size_t)(t - 1) * m];
            long long* cr = &C[(size_t)t * m];
            const long long* pp = p + (size_t)j * m;
            long long c = 0;
            for (int i = 0; i < m; ++i) { c = std::max(c, pr[i]) + pp[i]; cr[i] = c; }
            F[t] = F[t - 1] + cr[m - 1];
        }
    }

    void insert_best(int job, Rng& rng) {
        int m = M.m, L = (int)seq.size();
        const long long* p = M.pj.data();
        long long best = std::numeric_limits<long long>::max();
        int bestk = 0, ties = 0;
        row.resize(m);
        for (int k = 0; k <= L; ++k) {
            const long long* base = &C[(size_t)k * m];
            long long c = 0;
            const long long* pp = p + (size_t)job * m;
            for (int i = 0; i < m; ++i) { c = std::max(c, base[i]) + pp[i]; row[i] = c; }
            long long total = F[k] + row[m - 1];
            bool pruned = total > best;
            for (int t = k; t < L && !pruned; ++t) {
                const long long* q = p + (size_t)seq[t] * m;
                c = 0;
                for (int i = 0; i < m; ++i) { c = std::max(c, row[i]) + q[i]; row[i] = c; }
                total += row[m - 1];
                if (total > best) pruned = true;
            }
            if (pruned) continue;
            if (total < best) { best = total; bestk = k; ties = 1; }
            else { ++ties; if (rng.below(ties) == 0) bestk = k; }
        }
        seq.insert(seq.begin() + bestk, job);
        rebuild(bestk);
    }

public:
    IteratedGreedyDestructReconstruct(const Model& m, double r, int mx, bool b)
        : M(m), rps(r), maxr(std::max(1, mx)), block(b) {}

    Model::Solution perturb(const Model::Solution& s, double strength, Rng& rng) override {
        to_perm(s);
        int n = M.n;
        if (n < 2) return Model::Solution{perm};
        int d = (int)std::lround(std::max(1.0, strength) * rps);
        d = std::max(1, std::min({d, maxr, n - 1}));
        removed.clear();
        seq.clear();
        if (block) {
            int st = rng.below(n - d + 1);
            removed.assign(perm.begin() + st, perm.begin() + st + d);
            seq.assign(perm.begin(), perm.begin() + st);
            seq.insert(seq.end(), perm.begin() + st + d, perm.end());
            for (int t = d - 1; t > 0; --t) std::swap(removed[t], removed[rng.below(t + 1)]);
        } else {
            idx.resize(n);
            std::iota(idx.begin(), idx.end(), 0);
            mark.assign(n, 0);
            for (int t = 0; t < d; ++t) {
                int r = t + rng.below(n - t);
                std::swap(idx[t], idx[r]);
                mark[idx[t]] = 1;
                removed.push_back(perm[idx[t]]);
            }
            for (int t = 0; t < n; ++t) if (!mark[t]) seq.push_back(perm[t]);
        }
        rebuild(0);
        for (int job : removed) insert_best(job, rng);
        if (s.size() == 1 && s[0] == seq) {
            int a = rng.below(n), b = rng.below(n - 1);
            if (b >= a) ++b;
            std::swap(seq[a], seq[b]);
        }
        return Model::Solution{seq};
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double r = params.get("removed_per_strength", 2.0);
    int mx = (int)params.get("max_removed", 8);
    bool b = params.text("removal", "random") == "block";
    return std::make_unique<IteratedGreedyDestructReconstruct>(model, r, mx, b);
}
