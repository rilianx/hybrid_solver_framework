// COMPONENT: {"name": "granular_two_opt_star_tail_exchange", "slot": "neighborhood", "params": {"k_neighbors": {"type": "int", "range": [3, 30]}}}
class TwoOptStar : public hsf::Neighborhood<CVRP> {
public:
    using Sol = CVRP::Solution;
    TwoOptStar(const CVRP& m, int k) : M(m) {
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
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        std::fill(rof.begin(), rof.end(), -1);
        const int n = M.n;
        const double* dem = M.demand.data();
        int R = (int)s.size(), empty = -1;
        off.resize(R + 1);
        clen.resize(R);
        cl.resize(R);
        okr.resize(R);
        size_t run = 0;
        for (int r = 0; r < R; ++r) {
            off[r] = (int)run;
            run += s[r].size() + 1;
        }
        off[R] = (int)run;
        nodes.resize(run);
        pl.resize(run);
        for (int r = 0; r < R; ++r) {
            const auto& rt = s[r];
            int len = (int)rt.size();
            clen[r] = len;
            if (len == 0 && empty < 0) empty = r;
            int o = off[r];
            int* nd = nodes.data() + o;
            double* pp = pl.data() + o;
            pp[0] = 0.0;
            double l = 0.0, pre = 0.0;
            char ok = 1;
            for (int p = 0; p < len; ++p) {
                int c = rt[p];
                nd[p] = c;
                if (c >= 1 && c <= n) {
                    rof[c] = r, pof[c] = p;
                    l += dem[c];
                    pre += dem[c];
                } else ok = 0;
                pp[p + 1] = pre;
            }
            cl[r] = l;
            okr[r] = ok;
        }
        cR = R;
        cptr = &s;
        int target = empty < 0 ? R : empty;
        const double capT = M.capacity + 1e-9;
        for (int r1 = 0; r1 < R; ++r1) {
            const auto& A = s[r1];
            int len = clen[r1];
            for (int p = 0; p < len; ++p) {
                int u = A[p];
                if (u < 1 || u > n) continue;
                const int* nb = nbf.data() + (size_t)u * K;
                for (int t = 0; t < K; ++t) {
                    int v = nb[t];
                    int r2 = rof[v], q = pof[v];
                    if (r2 < 0) continue;
                    if (r2 == r1) {
                        if (q > p + 1) out.push_back({0, r1, p + 1, q, 0, 0});
                        else if (q + 1 < p) out.push_back({0, r1, q + 1, p, 0, 0});
                    } else {
                        int l2 = clen[r2];
                        add(out, r1, p + 1, len, r2, q, l2);
                        add(out, r1, p, len, r2, q + 1, l2);
                    }
                }
            }
            if (len >= 2 && cl[r1] > capT)
                for (int i = 1; i < len; ++i) out.push_back({1, r1, i, target, 0, 0});
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol t = s;
        if (m[0] == 0) {
            auto& r = t[m[1]];
            std::reverse(r.begin() + m[2], r.begin() + m[3] + 1);
            return t;
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        if (r2 >= (int)t.size()) t.emplace_back();
        const auto& A = s[r1];
        std::vector<int> B = r2 < (int)s.size() ? s[r2] : std::vector<int>();
        std::vector<int> na(A.begin(), A.begin() + i), nbv(B.begin(), B.begin() + j);
        na.insert(na.end(), B.begin() + j, B.end());
        nbv.insert(nbv.end(), A.begin() + i, A.end());
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

private:
    const CVRP& M;
    int K;
    std::vector<int> nbf;
    std::vector<int> rof, pof;
    std::vector<int> nodes, off, clen;
    std::vector<double> pl, cl;
    std::vector<char> okr;
    int cR = 0;
    const Sol* cptr = nullptr;

    double eval(const Sol& s, const Move& m, bool check) {
        if (m[0] == 0) {
            const auto& r = s[m[1]];
            int i = m[2], j = m[3], len = (int)r.size();
            int a = i > 0 ? r[i - 1] : 0, b = j + 1 < len ? r[j + 1] : 0;
            return M.dist(a, r[j]) + M.dist(r[i], b) - M.dist(a, r[i]) - M.dist(r[j], b);
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        const auto& A = s[r1];
        int l1 = (int)A.size();
        int a1 = i > 0 ? A[i - 1] : 0, b1 = i < l1 ? A[i] : 0;
        int a2 = 0, b2 = 0;
        double pre1, tot1, pre2 = 0.0, tot2 = 0.0;
        loadsOf(r1, A, i, check, pre1, tot1);
        if (r2 < (int)s.size()) {
            const auto& B = s[r2];
            int l2 = (int)B.size();
            a2 = j > 0 ? B[j - 1] : 0;
            b2 = j < l2 ? B[j] : 0;
            loadsOf(r2, B, j, check, pre2, tot2);
        }
        double dd = M.dist(a1, b2) + M.dist(a2, b1) - M.dist(a1, b1) - M.dist(a2, b2);
        double suf1 = tot1 - pre1, suf2 = tot2 - pre2;
        double C = M.capacity;
        dd += M.penalty * (std::max(0.0, pre1 + suf2 - C) + std::max(0.0, pre2 + suf1 - C) -
                           std::max(0.0, pre1 + suf1 - C) - std::max(0.0, pre2 + suf2 - C));
        return dd;
    }

    void loadsOf(int r, const std::vector<int>& R, int idx, bool check, double& pre, double& tot) const {
        int len = (int)R.size();
        if (r < cR && okr[r] && clen[r] == len && idx >= 0 && idx <= len &&
            (!check || len == 0 ||
             std::memcmp(R.data(), nodes.data() + off[r], (size_t)len * sizeof(int)) == 0)) {
            const double* pp = pl.data() + off[r];
            pre = pp[idx];
            tot = pp[len];
            return;
        }
        double p = 0, sf = 0;
        for (int k = 0; k < len; ++k) (k < idx ? p : sf) += M.demand[R[k]];
        pre = p;
        tot = p + sf;
    }

    static void add(std::vector<Move>& out, int r1, int i, int l1, int r2, int j, int l2) {
        if (i < 0 || j < 0 || i > l1 || j > l2) return;
        if ((i == 0 && j == 0) || (i == l1 && j == l2)) return;
        if (r1 > r2) std::swap(r1, r2), std::swap(i, j);
        out.push_back({1, r1, i, r2, j, 0});
    }
};

std::unique_ptr<hsf::Neighborhood<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int k = (int)params.get("k_neighbors", 10);
    return std::make_unique<TwoOptStar>(model, k);
}
