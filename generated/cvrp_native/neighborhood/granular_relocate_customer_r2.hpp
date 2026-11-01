// COMPONENT: {"name": "granular_relocate_customer", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class GranularRelocate : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    GranularRelocate(const CVRP& m, int k) : M(m) {
        int n = M.n;
        K = std::max(0, std::min(k, n - 1));
        nbf.assign((size_t)(n + 1) * (K > 0 ? K : 1), 0);
        std::vector<int> idx;
        for (int c = 1; c <= n; ++c) {
            idx.clear();
            for (int o = 1; o <= n; ++o) if (o != c) idx.push_back(o);
            std::partial_sort(idx.begin(), idx.begin() + K, idx.end(),
                              [&](int a, int b) { return M.dist(c, a) < M.dist(c, b); });
            for (int t = 0; t < K; ++t) nbf[(size_t)c * K + t] = idx[t];
        }
        rof.assign(n + 1, -1);
        pof.assign(n + 1, -1);
        d0c.assign(n + 1, 0.0);
        for (int c = 0; c <= n; ++c) d0c[c] = M.dist(0, c) + M.dist(c, 0);
        d00 = M.dist(0, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        std::fill(rof.begin(), rof.end(), -1);
        int R = (int)s.size(), empty = -1;
        cl.assign(R, 0.0);
        clen.resize(R);
        off.resize(R + 1);
        const int n = M.n;
        const double* dem = M.demand.data();
        size_t total = 0, run = 0;
        for (int r = 0; r < R; ++r) {
            int len = (int)s[r].size();
            off[r] = (int)run;
            run += len + 2;
            total += len;
        }
        off[R] = (int)run;
        nodes.resize(run);
        ec.resize(run);
        remp.resize(run);
        for (int r = 0; r < R; ++r) {
            const auto& rt = s[r];
            int len = (int)rt.size();
            clen[r] = len;
            if (len == 0 && empty < 0) empty = r;
            int o = off[r];
            int* nd = nodes.data() + o;
            nd[0] = 0;
            double l = 0.0;
            for (int p = 0; p < len; ++p) {
                int c = rt[p];
                nd[p + 1] = c;
                if (c >= 1 && c <= n) { rof[c] = r, pof[c] = p; l += dem[c]; }
            }
            nd[len + 1] = 0;
            cl[r] = l;
            double* e = ec.data() + o;
            for (int q = 0; q <= len; ++q) e[q] = M.dist(nd[q], nd[q + 1]);
            double* rm = remp.data() + o;
            for (int p = 0; p < len; ++p)
                rm[p + 1] = M.dist(nd[p], nd[p + 2]) - e[p] - e[p + 1];
        }
        cR = R;
        cptr = &s;
        out.reserve(out.size() + total * (2 * (size_t)K + 1));
        int target = empty < 0 ? R : empty;
        for (int r1 = 0; r1 < R; ++r1) {
            const auto& rt = s[r1];
            int len = (int)rt.size();
            for (int i = 0; i < len; ++i) {
                int c = rt[i];
                if (c < 1 || c > n) continue;
                const int* nb = nbf.data() + (size_t)c * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = rof[v], q = pof[v];
                    if (r2 < 0) continue;
                    if (r2 != r1) {
                        out.push_back({r1, i, r2, q, 0, 0});
                        out.push_back({r1, i, r2, q + 1, 0, 0});
                    } else {
                        int qq = q < i ? q : q - 1;
                        if (qq != i) out.push_back({r1, i, r1, qq, 0, 0});
                        if (qq + 1 != i) out.push_back({r1, i, r1, qq + 1, 0, 0});
                    }
                }
                if (len > 1) out.push_back({r1, i, target, 0, 0, 0});
            }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        if (r2 >= (int)t.size()) t.emplace_back();
        int c = t[r1][i];
        t[r1].erase(t[r1].begin() + i);
        t[r2].insert(t[r2].begin() + j, c);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        const auto& A = s[r1];
        int len = (int)A.size();
        int c = A[i];
        int p = i > 0 ? A[i - 1] : 0, nx = i + 1 < len ? A[i + 1] : 0;
        double dd = M.dist(p, nx) - M.dist(p, c) - M.dist(c, nx);
        if (r1 == r2) {
            int mlen = len - 1;
            auto at = [&](int k) { return k < i ? A[k] : A[k + 1]; };
            int a = j > 0 ? at(j - 1) : 0, b = j < mlen ? at(j) : 0;
            return dd + M.dist(a, c) + M.dist(c, b) - M.dist(a, b);
        }
        int a = 0, b = 0;
        double L2 = 0.0;
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            a = j > 0 ? B[j - 1] : 0;
            b = j < (int)B.size() ? B[j] : 0;
            L2 = loadOf(r2, B);
        }
        dd += M.dist(a, c) + M.dist(c, b) - M.dist(a, b);
        double L1 = loadOf(r1, A), dc = M.demand[c], C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - dc - C) - std::max(0.0, L1 - C) +
                           std::max(0.0, L2 + dc - C) - std::max(0.0, L2 - C));
        return dd;
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        if (&s != cptr || (int)s.size() != cR) return delta(s, m);
        int r1 = m[0], i = m[1], r2 = m[2], j = m[3];
        int len1 = clen[r1];
        if (i < 0 || i >= len1) return delta(s, m);
        const int o1 = off[r1];
        const int* nd = nodes.data();
        int c = nd[o1 + i + 1];
        double dd = remp[o1 + i + 1];
        if (r1 == r2) {
            int e = j < i ? j : j + 1;
            if (j < 0 || e > len1) return delta(s, m);
            int a = nd[o1 + e], b = nd[o1 + e + 1];
            return dd + M.dist(a, c) + M.dist(c, b) - ec[o1 + e];
        }
        double L2 = 0.0;
        if (r2 < cR) {
            if (j < 0 || j > clen[r2]) return delta(s, m);
            int o2 = off[r2];
            int a = nd[o2 + j], b = nd[o2 + j + 1];
            dd += M.dist(a, c) + M.dist(c, b) - ec[o2 + j];
            L2 = cl[r2];
        } else {
            dd += d0c[c] - d00;
        }
        double L1 = cl[r1], dc = M.demand[c], C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - dc - C) - std::max(0.0, L1 - C) +
                           std::max(0.0, L2 + dc - C) - std::max(0.0, L2 - C));
        return dd;
    }

    Move tabu_key(const Move& m) override { return {m[2], m[3], m[0], m[1], 0, 0}; }

private:
    const CVRP& M;
    int K;
    std::vector<int> nbf;
    std::vector<int> rof, pof;
    std::vector<int> nodes;     // rutas con depósito en ambos extremos, contiguas
    std::vector<double> ec;     // costo de la arista (q, q+1) de cada ruta
    std::vector<double> remp;   // ganancia de remover el nodo en cada posición
    std::vector<int> off, clen;
    std::vector<double> cl;
    std::vector<double> d0c;
    double d00 = 0.0;
    int cR = 0;
    const Sol* cptr = nullptr;

    double load(const std::vector<int>& r) const {
        double l = 0.0;
        for (int c : r) if (c >= 1 && c <= M.n) l += M.demand[c];
        return l;
    }
    // carga exacta: la cacheada solo si el contenido de la ruta coincide
    double loadOf(int r, const std::vector<int>& R) const {
        if (r < cR) {
            int len = (int)R.size();
            if (clen[r] == len) {
                if (len == 0) return cl[r];
                if (std::memcmp(R.data(), nodes.data() + off[r] + 1, (size_t)len * sizeof(int)) == 0)
                    return cl[r];
            }
        }
        return load(R);
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<GranularRelocate>(model, k);
}
