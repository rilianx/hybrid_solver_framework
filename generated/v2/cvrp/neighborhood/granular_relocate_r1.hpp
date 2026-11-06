// COMPONENT: {"name": "granular_relocate", "slot": "neighborhood", "params": {"neighbors": {"type": "int", "range": [4, 40]}, "cap_filter": {"type": "int", "range": [0, 1]}}}
using Sol = Model::Solution;

struct RelocIndex {
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

static std::vector<std::vector<int>> reloc_nearest(const Model& M, int K) {
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

class GranularRelocate : public hsf::Neighborhood<Model> {
public:
    GranularRelocate(const Model& m, int K, int capf) : M(m), capf_(capf != 0) {
        nb_ = reloc_nearest(M, K);
        mark_.assign(M.n + 1, 0);
        Kmax_ = 0;
        for (auto& v : nb_) Kmax_ = std::max(Kmax_, (int)v.size());
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        idx_.build(s, M.n);
        rl_.assign(s.size(), 0.0);
        for (int i = 0; i < (int)s.size(); ++i) rl_[i] = load(s[i]);
        for (int ri = 0; ri < (int)s.size(); ++ri)
            for (int pi = 0; pi < (int)s[ri].size(); ++pi) {
                int c = s[ri][pi];
                if (c < 1 || c > M.n || idx_.r[c] != ri || idx_.p[c] != pi) continue;
                gen(s, c, out);
            }
    }

    Sol apply(const Sol& s, const Move& m) override {
        ensure(s, m[0], m[1], m[2]);
        Sol t = s;
        apply_inplace(t, m);
        return t;
    }

    double delta(const Sol& s, const Move& m) override {
        ensure(s, m[0], m[1], m[2]);
        buf_ = s;
        apply_inplace(buf_, m);
        return M.objective(buf_) - M.objective(s);
    }

    Move tabu_key(const Move& m) override { return Move{m[0], m[3], m[4], m[1], m[2], 0, 0}; }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& m) override {
        ensure(s, m[0], m[1], m[2]);
        const int c = m[0], x = m[1], y = m[2];
        const int rc = idx_.r[c], pc = idx_.p[c];
        const std::vector<int>& R = s[rc];
        const int p = pc > 0 ? R[pc - 1] : 0;
        const int q = pc + 1 < (int)R.size() ? R[pc + 1] : 0;
        double dd = M.dist(p, q) - M.dist(p, c) - M.dist(c, q);
        dd += M.dist(x, c) + M.dist(c, y) - M.dist(x, y);
        const int rt = x ? idx_.r[x] : (y ? idx_.r[y] : -1);
        if (rt != rc) {
            const double dc = M.demand[c];
            const double Lc = load(R), Lt = rt >= 0 ? load(s[rt]) : 0.0;
            dd += M.penalty * (ex(Lc - dc) + ex(Lt + dc) - ex(Lc) - ex(Lt));
        }
        return dd;
    }

    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        const long long total = (long long)M.n * (2LL * Kmax_ + 1);
        if (k < 0 || (long long)k * 4 >= total) {
            hsf::Neighborhood<Model>::sample(s, k, rng, out);
            return;
        }
        out.clear();
        seen_.clear();
        int tries = 0;
        const int maxt = 20 * k + 50;
        Move m;
        while ((int)out.size() < k && tries++ < maxt)
            if (random_move(s, rng, m) && seen_.insert(m).second) out.push_back(m);
        if (out.empty()) hsf::Neighborhood<Model>::sample(s, k, rng, out);
    }

private:
    const Model& M;
    bool capf_;
    int Kmax_;
    std::vector<std::vector<int>> nb_;
    std::vector<int> mark_;
    int stamp_ = 0;
    RelocIndex idx_;
    std::vector<double> rl_;
    Sol buf_;
    std::set<Move> seen_;

    double ex(double l) const { return l > M.capacity ? l - M.capacity : 0.0; }
    double load(const std::vector<int>& R) const {
        double t = 0.0;
        for (int c : R) t += M.demand[c];
        return t;
    }
    bool cap_ok(double Lc, double Lt, double dc) const {
        return ex(Lc - dc) + ex(Lt + dc) <= ex(Lc) + ex(Lt) + 1e-9;
    }
    void ensure(const Sol& s, int a, int b, int c) {
        if (!idx_.ok(s, a) || !idx_.ok(s, b) || !idx_.ok(s, c)) idx_.build(s, M.n);
    }

    void gen(const Sol& s, int c, std::vector<Move>& out) {
        const int rc = idx_.r[c], pc = idx_.p[c];
        const std::vector<int>& R = s[rc];
        const int p = pc > 0 ? R[pc - 1] : 0;
        const int q = pc + 1 < (int)R.size() ? R[pc + 1] : 0;
        ++stamp_;
        for (int v : nb_[c]) mark_[v] = stamp_;
        const double dc = M.demand[c];
        for (int v : nb_[c]) {
            if (idx_.r[v] < 0) continue;
            const int rv = idx_.r[v], pv = idx_.p[v];
            const std::vector<int>& V = s[rv];
            if (rv != rc && capf_ && !cap_ok(rl_[rc], rl_[rv], dc)) continue;
            const int sv = pv + 1 < (int)V.size() ? V[pv + 1] : 0;
            const int pr = pv > 0 ? V[pv - 1] : 0;
            if (sv != c) out.push_back(Move{c, v, sv, p, q, 0, 0});
            if (pr != c && (pr == 0 || mark_[pr] != stamp_)) out.push_back(Move{c, pr, v, p, q, 0, 0});
        }
        if (R.size() > 1) out.push_back(Move{c, 0, 0, p, q, 0, 0});
    }

    bool random_move(const Sol& s, Rng& rng, Move& m) {
        const int c = 1 + rng.below(M.n);
        const int K = (int)nb_[c].size();
        const int j = rng.below(2 * K + 1);
        const int v = j < 2 * K ? nb_[c][j / 2] : 0;
        if (!idx_.ok(s, c) || !idx_.ok(s, v)) {
            idx_.build(s, M.n);
            if (!idx_.ok(s, c) || !idx_.ok(s, v)) return false;
        }
        const int rc = idx_.r[c], pc = idx_.p[c];
        const std::vector<int>& R = s[rc];
        const int p = pc > 0 ? R[pc - 1] : 0;
        const int q = pc + 1 < (int)R.size() ? R[pc + 1] : 0;
        int x, y, rt;
        if (v == 0) {
            if (R.size() < 2) return false;
            x = y = 0;
            rt = -1;
        } else {
            const int rv = idx_.r[v], pv = idx_.p[v];
            const std::vector<int>& V = s[rv];
            if (j % 2 == 0) { x = v; y = pv + 1 < (int)V.size() ? V[pv + 1] : 0; }
            else { x = pv > 0 ? V[pv - 1] : 0; y = v; }
            if (x == c || y == c) return false;
            rt = rv;
        }
        if (capf_ && rt >= 0 && rt != rc && !cap_ok(load(R), load(s[rt]), M.demand[c])) return false;
        m = Move{c, x, y, p, q, 0, 0};
        return true;
    }

    void apply_inplace(Sol& t, const Move& m) {
        const int c = m[0], x = m[1], y = m[2];
        const int rc = idx_.r[c], pc = idx_.p[c];
        int rt = -1, ins = 0;
        if (x != 0) { rt = idx_.r[x]; ins = idx_.p[x] + 1; }
        else if (y != 0) { rt = idx_.r[y]; ins = idx_.p[y]; }
        t[rc].erase(t[rc].begin() + pc);
        if (rt < 0) {
            t.push_back(std::vector<int>{c});
        } else {
            if (rt == rc && ins > pc) --ins;
            t[rt].insert(t[rt].begin() + ins, c);
        }
        if (t[rc].empty()) t.erase(t.begin() + rc);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int K = (int)params.get("neighbors", 15);
    int capf = (int)params.get("cap_filter", 1);
    return std::make_unique<GranularRelocate>(model, K, capf);
}
