// COMPONENT: {"name": "ig_destruct_greedy_reinsert", "slot": "perturbation", "params": {"d_base": {"type": "int", "range": [1, 6]}, "d_scale": {"type": "float", "range": [0.0, 2.0]}}}
class IGDestructReinsert : public hsf::Perturbation<Model> {
public:
    IGDestructReinsert(const Model& m, int db, double ds) : md(m), dbase(db), dscale(ds) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out = s;
        int K = (int)out.size();
        if (K == 0) return out;
        int N = 0;
        for (int l = 0; l < K; ++l) N += (int)out[l].size();
        if (N == 0) return out;
        if (N == 1) {
            if (K < 2) return out;
            int src = 0;
            for (int l = 0; l < K; ++l) if (!out[l].empty()) src = l;
            int job = out[src][0];
            out[src].clear();
            int dst = rng.below(K - 1);
            if (dst >= src) ++dst;
            out[dst].push_back(job);
            return out;
        }
        int d = dbase + (int)std::lround(dscale * std::max(1.0, strength));
        d = std::max(1, std::min(N - 1, d));
        removed.clear();
        int cur = N;
        for (int t = 0; t < d; ++t) {
            int g = rng.below(cur);
            for (int l = 0; l < K; ++l) {
                int sz = (int)out[l].size();
                if (g < sz) {
                    removed.push_back(out[l][g]);
                    out[l].erase(out[l].begin() + g);
                    break;
                }
                g -= sz;
            }
            --cur;
        }
        for (int job : removed) insertBest(out, job, rng);

        bool same = true;
        for (int l = 0; l < K && same; ++l) if (out[l] != s[l]) same = false;
        if (same) forceSwap(out, rng);

        if (!sameMultiset(out, s)) {
            Sol safe = s;
            forceSwap(safe, rng);
            return safe;
        }
        return out;
    }
private:
    const Model& md;
    int dbase;
    double dscale;
    std::vector<int> removed;
    std::vector<int> chk, ref;
    std::vector<long long> E, F, C;

    inline bool valid(int j) const { return j >= 0 && j < md.n; }

    bool sameMultiset(const Sol& a, const Sol& b) {
        chk.clear(); ref.clear();
        for (size_t l = 0; l < a.size(); ++l) chk.insert(chk.end(), a[l].begin(), a[l].end());
        for (size_t l = 0; l < b.size(); ++l) ref.insert(ref.end(), b[l].begin(), b[l].end());
        if (chk.size() != ref.size()) return false;
        std::sort(chk.begin(), chk.end());
        std::sort(ref.begin(), ref.end());
        return chk == ref;
    }

    // intercambia dos posiciones globales con valores distintos (si existen)
    void forceSwap(Sol& w, Rng& rng) {
        int K = (int)w.size();
        int N = 0;
        for (int l = 0; l < K; ++l) N += (int)w[l].size();
        if (N < 2) return;
        for (int tries = 0; tries < 32; ++tries) {
            int a = rng.below(N), b = rng.below(N - 1);
            if (b >= a) ++b;
            int la = 0, lb = 0;
            while (a >= (int)w[la].size()) { a -= (int)w[la].size(); ++la; }
            while (b >= (int)w[lb].size()) { b -= (int)w[lb].size(); ++lb; }
            if (w[la][a] != w[lb][b] || la != lb) {
                std::swap(w[la][a], w[lb][b]);
                if (la != lb || tries == 31) return;
                return;
            }
        }
    }

    long long seqCost(const std::vector<int>& v) {
        int m = md.m;
        if (m <= 0) return 0;
        C.assign(m, 0);
        long long sum = 0;
        for (int j : v) {
            if (!valid(j)) continue;
            const long long* p = &md.pj[(size_t)j * m];
            C[0] += p[0];
            for (int i = 1; i < m; ++i) C[i] = std::max(C[i], C[i - 1]) + p[i];
            sum += C[m - 1];
        }
        return sum;
    }

    // mejor posición de inserción de job en v; devuelve costo resultante, pos en bestPos
    long long bestInList(const std::vector<int>& v, int job, long long bound, int& bestPos, Rng& rng) {
        int L = (int)v.size();
        int m = md.m;
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
        long long best = bound;
        bestPos = -1;
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
            if (sum < best || bestPos < 0) { best = sum; bestPos = pos; ties = 1; }
            else if (sum == best) { ++ties; if (rng.below(ties) == 0) bestPos = pos; }
        }
        return best;
    }

    void insertBest(Sol& out, int job, Rng& rng) {
        int K = (int)out.size();
        if (md.m <= 0) {
            int l = rng.below(K);
            out[l].insert(out[l].begin() + rng.below((int)out[l].size() + 1), job);
            return;
        }
        long long bestDelta = std::numeric_limits<long long>::max();
        int bestL = 0, bestP = (int)out[0].size(), ties = 0;
        const long long INF = std::numeric_limits<long long>::max() / 4;
        for (int l = 0; l < K; ++l) {
            long long base = (K > 1) ? seqCost(out[l]) : 0;
            int pos;
            long long c = bestInList(out[l], job, INF, pos, rng);
            if (pos < 0) continue;
            long long delta = c - base;
            if (delta < bestDelta) { bestDelta = delta; bestL = l; bestP = pos; ties = 1; }
            else if (delta == bestDelta) { ++ties; if (rng.below(ties) == 0) { bestL = l; bestP = pos; } }
        }
        if (bestP < 0 || bestP > (int)out[bestL].size()) bestP = (int)out[bestL].size();
        out[bestL].insert(out[bestL].begin() + bestP, job);
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    int db = (int)params.get("d_base", 2);
    double ds = params.get("d_scale", 1.0);
    return std::make_unique<IGDestructReinsert>(model, db, ds);
}
