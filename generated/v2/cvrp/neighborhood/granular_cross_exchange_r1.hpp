// COMPONENT: {"name": "granular_cross_exchange", "slot": "neighborhood", "params": {"neighbors": {"type": "int", "range": [3, 25]}, "max_seg": {"type": "int", "range": [2, 4]}, "allow_reverse": {"type": "int", "range": [0, 1]}, "cap_filter": {"type": "int", "range": [0, 1]}}}
using Sol = Model::Solution;

struct CXIndex {
    std::vector<int> r, p;
    void build(const Sol& s, int n) {
        r.assign(n + 1, -1);
        p.assign(n + 1, -1);
        for (int i = 0; i < (int)s.size(); ++i)
            for (int j = 0; j < (int)s[i].size(); ++j) {
                int c = s[i][j];
                if (c >= 1 && c <= n) { r[c] = i; p[c] = j; }
            }
    }
    bool ok(const Sol& s, int c) const {
        if (c == 0) return true;
        if (c < 0 || c >= (int)r.size()) return false;
        int i = r[c];
        if (i < 0 || i >= (int)s.size()) return false;
        int j = p[c];
        if (j < 0 || j >= (int)s[i].size()) return false;
        return s[i][j] == c;
    }
};

static std::vector<std::vector<int>> cx_nearest(const Model& M, int K) {
    const int n = M.n;
    if (K > n - 1) K = n - 1;
    if (K < 0) K = 0;
    std::vector<std::vector<int>> nb(n + 1);
    std::vector<std::pair<double, int>> tmp;
    tmp.reserve(n);
    for (int c = 1; c <= n; ++c) {
        tmp.clear();
        for (int v = 1; v <= n; ++v) if (v != c) tmp.emplace_back(M.dist(c, v), v);
        if (K < (int)tmp.size()) std::nth_element(tmp.begin(), tmp.begin() + K, tmp.end());
        std::sort(tmp.begin(), tmp.begin() + K);
        for (int i = 0; i < K; ++i) nb[c].push_back(tmp[i].second);
    }
    return nb;
}

class GranularCrossExchange : public hsf::Neighborhood<Model> {
public:
    GranularCrossExchange(const Model& m, int K, int L, int rev, int capf)
        : M(m), L_(std::max(1, L)), rev_(rev != 0), capf_(capf != 0) {
        nb_ = cx_nearest(M, K);
        Kmax_ = 0;
        for (auto& v : nb_) Kmax_ = std::max(Kmax_, (int)v.size());
        nsw_ = 2 * L_ * L_;
        nin_ = 4 * L_;
        N1_ = M.n + 1;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        idx_.build(s, M.n);
        Move m;
        for (int ri = 0; ri < (int)s.size(); ++ri)
            for (int pi = 0; pi < (int)s[ri].size(); ++pi) {
                const int u = s[ri][pi];
                if (u < 1 || u > M.n || idx_.r[u] != ri || idx_.p[u] != pi) continue;
                for (int var = nsw_ + nin_; var < nsw_ + nin_ + L_; ++var)
                    if (make_move(s, u, u, var, m)) out.push_back(m);
                for (int v : nb_[u]) {
                    if (idx_.r[v] < 0 || idx_.r[v] == ri) continue;
                    for (int var = 0; var < nsw_ + nin_; ++var)
                        if (make_move(s, u, v, var, m)) out.push_back(m);
                }
            }
        std::sort(out.begin(), out.end());
        out.erase(std::unique(out.begin(), out.end()), out.end());
    }

    Sol apply(const Sol& s, const Move& m) override {
        ensure(s, m);
        Sol t = s;
        apply_inplace(t, m);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        ensure(s, m);
        buf_ = s;
        apply_inplace(buf_, m);
        return M.objective(buf_) - M.objective(s);
    }

    Move tabu_key(const Move& m) override {
        const int code = m[0];
        if (code < 4) {
            const int r1 = code & 1, r2 = (code >> 1) & 1;
            const int s1 = r1 ? m[2] : m[1], e1 = r1 ? m[1] : m[2];
            const int s2 = r2 ? m[4] : m[3], e2 = r2 ? m[3] : m[4];
            return canon(Move{r2 | (r1 << 1), s2, e2, s1, e1, 0, 0});
        }
        const int rev = code - 4;
        const int s0 = rev ? m[2] : m[1], e0 = rev ? m[1] : m[2];
        const int p = m[5] / N1_, q = m[5] % N1_;
        return Move{code, s0, e0, p, q, m[3] * N1_ + m[4], 0};
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        ensure(s, m);
        const int code = m[0];
        if (code < 4) {
            const int s1 = m[1], e1 = m[2], s2 = m[3], e2 = m[4];
            const int r1 = idx_.r[s1], i1 = idx_.p[s1], j1 = idx_.p[e1];
            const int r2 = idx_.r[s2], i2 = idx_.p[s2], j2 = idx_.p[e2];
            const std::vector<int>& A = s[r1];
            const std::vector<int>& B = s[r2];
            const int a = i1 > 0 ? A[i1 - 1] : 0, b = j1 + 1 < (int)A.size() ? A[j1 + 1] : 0;
            const int c = i2 > 0 ? B[i2 - 1] : 0, d = j2 + 1 < (int)B.size() ? B[j2 + 1] : 0;
            double dd = -M.dist(a, s1) - M.dist(e1, b) - M.dist(c, s2) - M.dist(e2, d);
            dd += (code & 2) ? M.dist(a, e2) + M.dist(s2, b) : M.dist(a, s2) + M.dist(e2, b);
            dd += (code & 1) ? M.dist(c, e1) + M.dist(s1, d) : M.dist(c, s1) + M.dist(e1, d);
            const double LA = seg_load(A, 0, (int)A.size() - 1), LB = seg_load(B, 0, (int)B.size() - 1);
            const double g1 = seg_load(A, i1, j1), g2 = seg_load(B, i2, j2);
            dd += M.penalty * (ex(LA - g1 + g2) + ex(LB - g2 + g1) - ex(LA) - ex(LB));
            return dd;
        }
        const int rev = code - 4, s0 = m[1], e0 = m[2], x = m[3], y = m[4];
        const int r1 = idx_.r[s0], i = idx_.p[s0], j = idx_.p[e0];
        const std::vector<int>& A = s[r1];
        const int p = i > 0 ? A[i - 1] : 0, q = j + 1 < (int)A.size() ? A[j + 1] : 0;
        double dd = M.dist(p, q) - M.dist(p, s0) - M.dist(e0, q) - M.dist(x, y);
        dd += rev ? M.dist(x, e0) + M.dist(s0, y) : M.dist(x, s0) + M.dist(e0, y);
        const int rt = x ? idx_.r[x] : (y ? idx_.r[y] : -1);
        const double LA = seg_load(A, 0, (int)A.size() - 1);
        const double Lt = rt >= 0 ? seg_load(s[rt], 0, (int)s[rt].size() - 1) : 0.0;
        const double g = seg_load(A, i, j);
        dd += M.penalty * (ex(LA - g) + ex(Lt + g) - ex(LA) - ex(Lt));
        return dd;
    }

    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        const long long total = (long long)M.n * ((long long)Kmax_ * (nsw_ + nin_) + L_);
        if (k < 0 || (long long)k * 4 >= total) {
            hsf::Neighborhood<Model>::sample(s, k, rng, out);
            return;
        }
        out.clear();
        seen_.clear();
        int tries = 0;
        const int maxt = 30 * k + 50;
        Move m;
        while ((int)out.size() < k && tries++ < maxt) {
            const int u = 1 + rng.below(M.n);
            const int var = rng.below(nsw_ + nin_ + L_);
            int v = u;
            if (var < nsw_ + nin_) {
                if (nb_[u].empty()) continue;
                v = nb_[u][rng.below((int)nb_[u].size())];
            }
            if (!idx_.ok(s, u) || !idx_.ok(s, v)) {
                idx_.build(s, M.n);
                if (!idx_.ok(s, u) || !idx_.ok(s, v)) continue;
            }
            if (make_move(s, u, v, var, m) && seen_.insert(m).second) out.push_back(m);
        }
        if (out.empty()) hsf::Neighborhood<Model>::sample(s, k, rng, out);
    }

private:
    const Model& M;
    int L_;
    bool rev_, capf_;
    int Kmax_, nsw_, nin_, N1_;
    std::vector<std::vector<int>> nb_;
    CXIndex idx_;
    Sol buf_;
    std::vector<int> tA_, tB_, seg_;
    std::set<Move> seen_;

    double ex(double l) const { return l > M.capacity ? l - M.capacity : 0.0; }
    double seg_load(const std::vector<int>& R, int i, int j) const {
        double t = 0.0;
        for (int k = i; k <= j; ++k) t += M.demand[R[k]];
        return t;
    }
    bool cap_ok(double oA, double oB, double nA, double nB) const {
        return !capf_ || ex(nA) + ex(nB) <= ex(oA) + ex(oB) + 1e-9;
    }
    static Move canon(Move m) {
        if (m[0] < 4 && m[1] > m[3]) {
            std::swap(m[1], m[3]);
            std::swap(m[2], m[4]);
            const int f = m[0];
            m[0] = ((f & 1) << 1) | ((f >> 1) & 1);
        }
        return m;
    }
    void ensure(const Sol& s, const Move& m) {
        if (!idx_.ok(s, m[1]) || !idx_.ok(s, m[2]) || !idx_.ok(s, m[3]) || !idx_.ok(s, m[4])) idx_.build(s, M.n);
    }

    bool make_move(const Sol& s, int u, int v, int var, Move& m) {
        const int ru = idx_.r[u], pu = idx_.p[u];
        const std::vector<int>& U = s[ru];
        const int nu = (int)U.size();
        if (var >= nsw_ + nin_) {
            const int l = var - nsw_ - nin_ + 1;
            if (l >= nu || pu + l > nu) return false;
            const int p = pu > 0 ? U[pu - 1] : 0, q = pu + l < nu ? U[pu + l] : 0;
            m = Move{4, u, U[pu + l - 1], 0, 0, p * N1_ + q, 0};
            return true;
        }
        if (v == u) return false;
        const int rv = idx_.r[v], pv = idx_.p[v];
        if (rv == ru) return false;
        const std::vector<int>& V = s[rv];
        const int nv = (int)V.size();
        if (var < nsw_) {
            const int l1 = var / (2 * L_) + 1, rem = var % (2 * L_), l2 = rem / 2 + 1, r2 = rem % 2;
            if (pu + l1 >= nu) return false;
            int a2, b2;
            if (!r2) { a2 = pv; b2 = pv + l2 - 1; if (b2 >= nv) return false; }
            else {
                if (!rev_ || l2 == 1) return false;
                a2 = pv - l2 + 1; b2 = pv;
                if (a2 < 0) return false;
            }
            if (capf_) {
                const double LU = seg_load(U, 0, nu - 1), LV = seg_load(V, 0, nv - 1);
                const double g1 = seg_load(U, pu + 1, pu + l1), g2 = seg_load(V, a2, b2);
                if (!cap_ok(LU, LV, LU - g1 + g2, LV - g2 + g1)) return false;
            }
            m = canon(Move{r2 ? 2 : 0, U[pu + 1], U[pu + l1], V[a2], V[b2], 0, 0});
            return true;
        }
        const int w = var - nsw_, l = w / 4 + 1, kind = w % 4;
        const int rev = kind >= 2 ? 1 : 0;
        if (rev && (!rev_ || l == 1)) return false;
        int a2, b2;
        if (kind == 0 || kind == 3) { a2 = pv; b2 = pv + l - 1; if (b2 >= nv) return false; }
        else { a2 = pv - l + 1; b2 = pv; if (a2 < 0) return false; }
        int x, y;
        if (kind == 0 || kind == 2) { x = u; y = pu + 1 < nu ? U[pu + 1] : 0; }
        else { x = pu > 0 ? U[pu - 1] : 0; y = u; }
        if (capf_) {
            const double LU = seg_load(U, 0, nu - 1), LV = seg_load(V, 0, nv - 1);
            const double g = seg_load(V, a2, b2);
            if (!cap_ok(LU, LV, LU + g, LV - g)) return false;
        }
        const int p = a2 > 0 ? V[a2 - 1] : 0, q = b2 + 1 < nv ? V[b2 + 1] : 0;
        m = Move{4 + rev, V[a2], V[b2], x, y, p * N1_ + q, 0};
        return true;
    }

    void apply_inplace(Sol& t, const Move& m) {
        const int code = m[0];
        if (code < 4) {
            const int r1 = idx_.r[m[1]], i1 = idx_.p[m[1]], j1 = idx_.p[m[2]];
            const int r2 = idx_.r[m[3]], i2 = idx_.p[m[3]], j2 = idx_.p[m[4]];
            if (r1 == r2 || j1 < i1 || j2 < i2) return;
            const std::vector<int>& A = t[r1];
            const std::vector<int>& B = t[r2];
            tA_.assign(A.begin(), A.begin() + i1);
            tA_.insert(tA_.end(), B.begin() + i2, B.begin() + j2 + 1);
            if (code & 2) std::reverse(tA_.begin() + i1, tA_.end());
            tA_.insert(tA_.end(), A.begin() + j1 + 1, A.end());
            tB_.assign(B.begin(), B.begin() + i2);
            tB_.insert(tB_.end(), A.begin() + i1, A.begin() + j1 + 1);
            if (code & 1) std::reverse(tB_.begin() + i2, tB_.end());
            tB_.insert(tB_.end(), B.begin() + j2 + 1, B.end());
            t[r1].swap(tA_);
            t[r2].swap(tB_);
            return;
        }
        const int rev = code - 4;
        const int r1 = idx_.r[m[1]], i = idx_.p[m[1]], j = idx_.p[m[2]];
        if (j < i) return;
        const int x = m[3], y = m[4];
        int rt = -1, ins = 0;
        if (x != 0) { rt = idx_.r[x]; ins = idx_.p[x] + 1; }
        else if (y != 0) { rt = idx_.r[y]; ins = idx_.p[y]; }
        if (rt == r1) return;
        seg_.assign(t[r1].begin() + i, t[r1].begin() + j + 1);
        if (rev) std::reverse(seg_.begin(), seg_.end());
        if (rt < 0) t.push_back(seg_);
        else t[rt].insert(t[rt].begin() + ins, seg_.begin(), seg_.end());
        t[r1].erase(t[r1].begin() + i, t[r1].begin() + j + 1);
        if (t[r1].empty()) t.erase(t.begin() + r1);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int K = (int)params.get("neighbors", 10);
    int L = (int)params.get("max_seg", 3);
    int rev = (int)params.get("allow_reverse", 1);
    int capf = (int)params.get("cap_filter", 1);
    return std::make_unique<GranularCrossExchange>(model, K, L, rev, capf);
}
