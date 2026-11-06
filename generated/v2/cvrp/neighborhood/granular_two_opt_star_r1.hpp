// COMPONENT: {"name": "granular_two_opt_star", "slot": "neighborhood", "params": {"neighbors": {"type": "int", "range": [4, 40]}, "cap_filter": {"type": "int", "range": [0, 1]}}}
using Sol = Model::Solution;

struct TOIndex {
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

static std::vector<std::vector<int>> to_nearest(const Model& M, int K) {
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

class GranularTwoOptStar : public hsf::Neighborhood<Model> {
public:
    GranularTwoOptStar(const Model& m, int K, int capf) : M(m), capf_(capf != 0) {
        nb_ = to_nearest(M, K);
        Kmax_ = 0;
        for (auto& v : nb_) Kmax_ = std::max(Kmax_, (int)v.size());
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        idx_.build(s, M.n);
        Move m;
        for (int ri = 0; ri < (int)s.size(); ++ri)
            for (int pi = 0; pi < (int)s[ri].size(); ++pi) {
                const int u = s[ri][pi];
                if (u < 1 || u > M.n || idx_.r[u] != ri || idx_.p[u] != pi) continue;
                for (int v : nb_[u]) {
                    if (idx_.r[v] < 0) continue;
                    for (int var = 0; var < 3; ++var)
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
        const int a = m[1], b = m[2], c = m[3], d = m[4];
        if (m[0] == 0) return Move{0, a, c, b, d, 0, 0};
        if (m[0] == 1) return canon(Move{1, a, d, c, b, 0, 0});
        return canon(Move{2, a, c, b, d, 0, 0});
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        ensure(s, m);
        const int ty = m[0], a = m[1], b = m[2], c = m[3], d = m[4];
        double dd = -M.dist(a, b) - M.dist(c, d);
        if (ty == 1) dd += M.dist(a, d) + M.dist(c, b);
        else dd += M.dist(a, c) + M.dist(b, d);
        if (ty != 0) {
            int r1, k1, r2, k2;
            if (!locate(a, b, r1, k1) || !locate(c, d, r2, k2)) return dd;
            const double P1 = prefix_load(s[r1], k1), L1 = prefix_load(s[r1], (int)s[r1].size());
            const double P2 = prefix_load(s[r2], k2), L2 = prefix_load(s[r2], (int)s[r2].size());
            double nA, nB;
            if (ty == 1) { nA = P1 + L2 - P2; nB = P2 + L1 - P1; }
            else { nA = P1 + P2; nB = (L1 - P1) + (L2 - P2); }
            dd += M.penalty * (ex(nA) + ex(nB) - ex(L1) - ex(L2));
        }
        return dd;
    }

    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        const long long total = (long long)M.n * Kmax_ * 3LL;
        if (k < 0 || (long long)k * 4 >= total) {
            hsf::Neighborhood<Model>::sample(s, k, rng, out);
            return;
        }
        out.clear();
        seen_.clear();
        int tries = 0;
        const int maxt = 20 * k + 50;
        Move m;
        while ((int)out.size() < k && tries++ < maxt) {
            const int u = 1 + rng.below(M.n);
            if (nb_[u].empty()) continue;
            const int v = nb_[u][rng.below((int)nb_[u].size())];
            const int var = rng.below(3);
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
    bool capf_;
    int Kmax_;
    std::vector<std::vector<int>> nb_;
    TOIndex idx_;
    Sol buf_;
    std::vector<int> tA_, tB_;
    std::set<Move> seen_;

    double ex(double l) const { return l > M.capacity ? l - M.capacity : 0.0; }
    double prefix_load(const std::vector<int>& R, int k) const {
        double t = 0.0;
        for (int i = 0; i < k; ++i) t += M.demand[R[i]];
        return t;
    }
    static Move canon(Move m) {
        if (m[0] != 0 && (m[1] > m[3] || (m[1] == m[3] && m[2] > m[4]))) {
            std::swap(m[1], m[3]);
            std::swap(m[2], m[4]);
        }
        return m;
    }
    void ensure(const Sol& s, const Move& m) {
        if (!idx_.ok(s, m[1]) || !idx_.ok(s, m[2]) || !idx_.ok(s, m[3]) || !idx_.ok(s, m[4])) idx_.build(s, M.n);
    }
    bool locate(int x, int y, int& r, int& k) const {
        if (x != 0) { r = idx_.r[x]; k = idx_.p[x] + 1; return r >= 0; }
        if (y != 0) { r = idx_.r[y]; k = 0; return r >= 0; }
        return false;
    }

    bool make_move(const Sol& s, int u, int v, int var, Move& m) {
        const int ru = idx_.r[u], pu = idx_.p[u], rv = idx_.r[v], pv = idx_.p[v];
        const std::vector<int>& U = s[ru];
        const std::vector<int>& V = s[rv];
        const int nu = (int)U.size(), nv = (int)V.size();
        if (ru == rv) {
            if (var > 1) return false;
            int px = pu, py = pv;
            if (px > py) std::swap(px, py);
            if (py - px < 2) return false;
            if (var == 0) m = Move{0, U[px], U[px + 1], U[py], py + 1 < nu ? U[py + 1] : 0, 0, 0};
            else m = Move{0, px > 0 ? U[px - 1] : 0, U[px], U[py - 1], U[py], 0, 0};
            return true;
        }
        const int su = pu + 1 < nu ? U[pu + 1] : 0, pru = pu > 0 ? U[pu - 1] : 0;
        const int sv = pv + 1 < nv ? V[pv + 1] : 0, prv = pv > 0 ? V[pv - 1] : 0;
        int ty, a, b, c, d, k1, k2;
        if (var == 0) { ty = 1; a = u; b = su; c = prv; d = v; k1 = pu + 1; k2 = pv; }
        else if (var == 1) { ty = 2; a = u; b = su; c = v; d = sv; k1 = pu + 1; k2 = pv + 1; }
        else { ty = 2; a = pru; b = u; c = prv; d = v; k1 = pu; k2 = pv; }
        if (capf_) {
            const double P1 = prefix_load(U, k1), L1 = prefix_load(U, nu);
            const double P2 = prefix_load(V, k2), L2 = prefix_load(V, nv);
            double nA, nB;
            if (ty == 1) { nA = P1 + L2 - P2; nB = P2 + L1 - P1; }
            else { nA = P1 + P2; nB = (L1 - P1) + (L2 - P2); }
            if (ex(nA) + ex(nB) > ex(L1) + ex(L2) + 1e-9) return false;
        }
        m = canon(Move{ty, a, b, c, d, 0, 0});
        return true;
    }

    void apply_inplace(Sol& t, const Move& m) {
        const int ty = m[0];
        int r1, k1, r2, k2;
        if (!locate(m[1], m[2], r1, k1) || !locate(m[3], m[4], r2, k2)) return;
        if (ty == 0) {
            if (r1 != r2) return;
            if (k1 > k2) std::swap(k1, k2);
            std::reverse(t[r1].begin() + k1, t[r1].begin() + k2);
            return;
        }
        if (r1 == r2) return;
        const std::vector<int>& A = t[r1];
        const std::vector<int>& B = t[r2];
        if (ty == 1) {
            tA_.assign(A.begin(), A.begin() + k1);
            tA_.insert(tA_.end(), B.begin() + k2, B.end());
            tB_.assign(B.begin(), B.begin() + k2);
            tB_.insert(tB_.end(), A.begin() + k1, A.end());
        } else {
            tA_.assign(A.begin(), A.begin() + k1);
            tA_.insert(tA_.end(), B.rend() - k2, B.rend());
            tB_.assign(A.rbegin(), A.rend() - k1);
            tB_.insert(tB_.end(), B.begin() + k2, B.end());
        }
        t[r1].swap(tA_);
        t[r2].swap(tB_);
        const int hi = std::max(r1, r2), lo = std::min(r1, r2);
        if (t[hi].empty()) t.erase(t.begin() + hi);
        if (t[lo].empty()) t.erase(t.begin() + lo);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int K = (int)params.get("neighbors", 15);
    int capf = (int)params.get("cap_filter", 1);
    return std::make_unique<GranularTwoOptStar>(model, K, capf);
}
