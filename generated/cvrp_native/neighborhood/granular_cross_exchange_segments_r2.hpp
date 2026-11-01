// COMPONENT: {"name": "granular_cross_exchange_segments", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 20]}, "max_seg": {"type": "int", "range": [1, 4]}}}
class CrossExchange : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    CrossExchange(const CVRP& m, int k, int L) : M(m), L(std::max(1, L)) {
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
        stride = n + 1;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        build(s);
        const int n = M.n;
        const int R = cR;
        const int Lc = L;
        size_t cnt = 0;
        for (int r1 = 0; r1 < R; ++r1) {
            int len1 = clen[r1];
            const int* A = nodes.data() + off[r1];
            for (int p = 0; p < len1; ++p) {
                int u = A[p];
                if (u < 1 || u > n) continue;
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = rof[v];
                    if (r2 < 0 || r2 == r1) continue;
                    int q = pof[v], len2 = clen[r2];
                    int i = p + 1;
                    int ma = std::min(Lc, len1 - i), mb = std::min(Lc, len2 - q);
                    if (ma >= 0 && mb >= 1) cnt += (size_t)(ma + 1) * mb;
                    int ma2 = std::min(Lc, p), mb2 = std::min(Lc, q + 1);
                    if (ma2 >= 0 && mb2 >= 1) cnt += (size_t)(ma2 + 1) * mb2;
                }
            }
        }
        size_t base = out.size();
        out.resize(base + cnt);
        Move* w = out.data() + base;
        for (int r1 = 0; r1 < R; ++r1) {
            int len1 = clen[r1];
            const int* A = nodes.data() + off[r1];
            for (int p = 0; p < len1; ++p) {
                int u = A[p];
                if (u < 1 || u > n) continue;
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = rof[v];
                    if (r2 < 0 || r2 == r1) continue;
                    int q = pof[v], len2 = clen[r2];
                    int i = p + 1, j = q;
                    int ma = std::min(Lc, len1 - i), mb = std::min(Lc, len2 - j);
                    for (int a = 0; a <= ma; ++a)
                        for (int b = 1; b <= mb; ++b) *w++ = Move{r1, i, a, r2, j, b};
                    int ma2 = std::min(Lc, p), mb2 = std::min(Lc, q + 1);
                    for (int a = 0; a <= ma2; ++a)
                        for (int b = 1; b <= mb2; ++b) *w++ = Move{r1, p - a, a, r2, q - b + 1, b};
                }
            }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        int r1 = m[0], i = m[1], a = m[2], r2 = m[3], j = m[4], b = m[5];
        int R = (int)s.size();
        Sol t(R);
        for (int r = 0; r < R; ++r)
            if (r != r1 && r != r2) t[r] = s[r];
        const auto& A = s[r1];
        const auto& B = s[r2];
        std::vector<int> na;
        na.reserve(A.size() - a + b);
        na.insert(na.end(), A.begin(), A.begin() + i);
        na.insert(na.end(), B.begin() + j, B.begin() + j + b);
        na.insert(na.end(), A.begin() + i + a, A.end());
        std::vector<int> nbv;
        nbv.reserve(B.size() - b + a);
        nbv.insert(nbv.end(), B.begin(), B.begin() + j);
        nbv.insert(nbv.end(), A.begin() + i, A.begin() + i + a);
        nbv.insert(nbv.end(), B.begin() + j + b, B.end());
        t[r1] = std::move(na);
        t[r2] = std::move(nbv);
        return t;
    }

    double delta(const Sol& s, const Move& m) override { return eval(s, m, true); }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        if (&s != cptr || (int)s.size() != cR) return eval(s, m, true);
        return eval(s, m, false);
    }

    Move tabu_key(const Move& m) override { return {m[0], m[1], m[5], m[3], m[4], m[2]}; }

private:
    const CVRP& M;
    int K, L;
    int stride = 1;
    std::vector<int> nbf;
    std::vector<int> rof, pof;
    std::vector<int> nodes, off, clen;
    std::vector<double> pl;
    int cR = 0;
    const Sol* cptr = nullptr;

    void build(const Sol& s) {
        std::fill(rof.begin(), rof.end(), -1);
        const int n = M.n;
        const double* dem = M.demand.data();
        int R = (int)s.size();
        off.resize(R + 1);
        clen.resize(R);
        size_t run = 0, prun = 0;
        for (int r = 0; r < R; ++r) {
            off[r] = (int)run;
            run += s[r].size() + 1;
        }
        off[R] = (int)run;
        (void)prun;
        nodes.resize(run);
        pl.resize(run);
        for (int r = 0; r < R; ++r) {
            const auto& rt = s[r];
            int len = (int)rt.size();
            clen[r] = len;
            int o = off[r];
            int* nd = nodes.data() + o;
            double* pp = pl.data() + o;
            pp[0] = 0.0;
            double pre = 0.0;
            for (int p = 0; p < len; ++p) {
                int c = rt[p];
                nd[p] = c;
                if (c >= 1 && c <= n) rof[c] = r, pof[c] = p;
                pre += dem[c];
                pp[p + 1] = pre;
            }
        }
        cR = R;
        cptr = &s;
    }

    void loadsOf(int r, const std::vector<int>& R, int i, int a, bool check, double& seg, double& tot) const {
        int len = (int)R.size();
        if (r < cR && clen[r] == len && i >= 0 && a >= 0 && i + a <= len &&
            (!check || len == 0 ||
             std::memcmp(R.data(), nodes.data() + off[r], (size_t)len * sizeof(int)) == 0)) {
            const double* pp = pl.data() + off[r];
            seg = pp[i + a] - pp[i];
            tot = pp[len];
            return;
        }
        double sg = 0, tt = 0;
        for (int k = 0; k < len; ++k) {
            double d = M.demand[R[k]];
            tt += d;
            if (k >= i && k < i + a) sg += d;
        }
        seg = sg;
        tot = tt;
    }

    double eval(const Sol& s, const Move& m, bool check) {
        int r1 = m[0], i = m[1], a = m[2], r2 = m[3], j = m[4], b = m[5];
        const auto& A = s[r1];
        const auto& B = s[r2];
        int la = (int)A.size(), lb = (int)B.size();
        int p1 = i > 0 ? A[i - 1] : 0, n1 = i + a < la ? A[i + a] : 0;
        int f1 = a ? A[i] : 0, l1 = a ? A[i + a - 1] : 0;
        int p2 = j > 0 ? B[j - 1] : 0, n2 = j + b < lb ? B[j + b] : 0;
        int f2 = b ? B[j] : 0, l2 = b ? B[j + b - 1] : 0;
        const double* D = M.D.data();
        const size_t S = (size_t)stride;
        auto d = [&](int x, int y) { return D[(size_t)x * S + y]; };
        double old1 = a ? d(p1, f1) + d(l1, n1) : d(p1, n1);
        double new1 = b ? d(p1, f2) + d(l2, n1) : d(p1, n1);
        double old2 = b ? d(p2, f2) + d(l2, n2) : d(p2, n2);
        double new2 = a ? d(p2, f1) + d(l1, n2) : d(p2, n2);
        double dd = new1 + new2 - old1 - old2;
        double s1, s2, L1, L2;
        loadsOf(r1, A, i, a, check, s1, L1);
        loadsOf(r2, B, j, b, check, s2, L2);
        double C = M.capacity;
        dd += M.penalty * (std::max(0.0, L1 - s1 + s2 - C) + std::max(0.0, L2 - s2 + s1 - C) -
                           std::max(0.0, L1 - C) - std::max(0.0, L2 - C));
        return dd;
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 8);
    int L = (int)params.get("max_seg", 2);
    return std::make_unique<CrossExchange>(model, k, L);
}
