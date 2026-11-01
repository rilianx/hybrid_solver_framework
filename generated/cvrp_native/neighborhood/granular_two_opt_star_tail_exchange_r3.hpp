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
        loc.assign((size_t)(n + 1) * 2, -1);
        Dp = M.D.data();
        S = (size_t)(n + 1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const int n = M.n;
        int* lc = loc.data();
        for (size_t z = 0, e = loc.size(); z < e; z += 2) lc[z] = -1;
        const double* dem = M.demand.data();
        int R = (int)s.size(), empty = -1;
        off.resize(R + 1);
        clen.resize(R);
        cl.resize(R);
        okr.resize(R);
        size_t run = 0, total = 0;
        for (int r = 0; r < R; ++r) {
            off[r] = (int)run;
            size_t len = s[r].size();
            run += len + 2;
            total += len;
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
            nd[0] = 0;
            pp[0] = 0.0;
            double pre = 0.0;
            char ok = 1;
            for (int p = 0; p < len; ++p) {
                int c = rt[p];
                nd[p + 1] = c;
                if (c >= 1 && c <= n) {
                    lc[2 * c] = r;
                    lc[2 * c + 1] = p;
                    pre += dem[c];
                } else ok = 0;
                pp[p + 1] = pre;
            }
            nd[len + 1] = 0;
            pp[len + 1] = pre;
            cl[r] = pre;
            okr[r] = ok;
        }
        cR = R;
        cptr = &s;
        out.reserve(out.size() + total * (2 * (size_t)K + 1));
        int target = empty < 0 ? R : empty;
        const double capT = M.capacity + 1e-9;
        const int Kc = K;
        for (int r1 = 0; r1 < R; ++r1) {
            const int* A = nodes.data() + off[r1] + 1;
            int len = clen[r1];
            for (int p = 0; p < len; ++p) {
                int u = A[p];
                if (u < 1 || u > n) continue;
                const int* nb = nbf.data() + (size_t)u * Kc;
                for (int t = 0; t < Kc; ++t) {
                    int v = nb[t];
                    int r2 = lc[2 * v];
                    if (r2 < 0) continue;
                    int q = lc[2 * v + 1];
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
        if (m[0] == 0) {
            Sol t = s;
            auto& r = t[m[1]];
            std::reverse(r.begin() + m[2], r.begin() + m[3] + 1);
            return t;
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        int R = (int)s.size();
        Sol t(r2 >= R ? R + 1 : R);
        for (int r = 0; r < R; ++r)
            if (r != r1 && r != r2) t[r] = s[r];
        const auto& A = s[r1];
        static const std::vector<int> emptyv;
        const std::vector<int>& B = r2 < R ? s[r2] : emptyv;
        std::vector<int> na, nbv;
        na.reserve(i + (B.size() - j));
        nbv.reserve(j + (A.size() - i));
        na.insert(na.end(), A.begin(), A.begin() + i);
        na.insert(na.end(), B.begin() + j, B.end());
        nbv.insert(nbv.end(), B.begin(), B.begin() + j);
        nbv.insert(nbv.end(), A.begin() + i, A.end());
        t[r1] = std::move(na);
        t[r2] = std::move(nbv);
        return t;
    }

    double delta(const Sol& s, const Move& m) override { return eval(s, m, true); }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        if (&s != cptr || (int)s.size() != cR) return eval(s, m, true);
        const int* ND = nodes.data();
        if (m[0] == 0) {
            int r = m[1], i = m[2], j = m[3];
            if (r < 0 || r >= cR || i < 0 || j < i || j >= clen[r]) return eval(s, m, false);
            const int* nd = ND + off[r];
            int a = nd[i], b = nd[j + 2], ci = nd[i + 1], cj = nd[j + 1];
            return d(a, cj) + d(ci, b) - d(a, ci) - d(cj, b);
        }
        int r1 = m[1], i = m[2], r2 = m[3], j = m[4];
        if (r1 < 0 || r1 >= cR || !okr[r1] || i < 0 || i > clen[r1] || r2 < 0) return eval(s, m, false);
        const int o1 = off[r1];
        int a1 = ND[o1 + i], b1 = ND[o1 + i + 1];
        double pre1 = pl[o1 + i], tot1 = pl[o1 + clen[r1]];
        int a2 = 0, b2 = 0;
        double pre2 = 0.0, tot2 = 0.0;
        if (r2 < cR) {
            if (!okr[r2] || j < 0 || j > clen[r2]) return eval(s, m, false);
            const int o2 = off[r2];
            a2 = ND[o2 + j];
            b2 = ND[o2 + j + 1];
            pre2 = pl[o2 + j];
            tot2 = pl[o2 + clen[r2]];
        }
        return finish(a1, b1, a2, b2, pre1, tot1, pre2, tot2);
    }

private:
    const CVRP& M;
    int K;
    const double* Dp = nullptr;
    size_t S = 1;
    std::vector<int> nbf;
    std::vector<int> loc;
    std::vector<int> nodes, off, clen;
    std::vector<double> pl, cl;
    std::vector<char> okr;
    int cR = 0;
    const Sol* cptr = nullptr;

    inline double d(int a, int b) const { return Dp[(size_t)a * S + b]; }

    inline double finish(int a1, int b1, int a2, int b2, double pre1, double tot1, double pre2,
                         double tot2) const {
        double dd = d(a1, b2) + d(a2, b1) - d(a1, b1) - d(a2, b2);
        double suf1 = tot1 - pre1, suf2 = tot2 - pre2;
        double C = M.capacity;
        dd += M.penalty * (std::max(0.0, pre1 + suf2 - C) + std::max(0.0, pre2 + suf1 - C) -
                           std::max(0.0, pre1 + suf1 - C) - std::max(0.0, pre2 + suf2 - C));
        return dd;
    }

    double eval(const Sol& s, const Move& m, bool check) {
        if (m[0] == 0) {
            const auto& r = s[m[1]];
            int i = m[2], j = m[3], len = (int)r.size();
            int a = i > 0 ? r[i - 1] : 0, b = j + 1 < len ? r[j + 1] : 0;
            return d(a, r[j]) + d(r[i], b) - d(a, r[i]) - d(r[j], b);
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
        return finish(a1, b1, a2, b2, pre1, tot1, pre2, tot2);
    }

    void loadsOf(int r, const std::vector<int>& R, int idx, bool check, double& pre, double& tot) const {
        int len = (int)R.size();
        if (r < cR && okr[r] && clen[r] == len && idx >= 0 && idx <= len &&
            (!check || len == 0 ||
             std::memcmp(R.data(), nodes.data() + off[r] + 1, (size_t)len * sizeof(int)) == 0)) {
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
