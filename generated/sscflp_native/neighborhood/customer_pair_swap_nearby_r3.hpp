// COMPONENT: {"name": "customer_pair_swap_nearby", "slot": "neighborhood", "params": {"k_nearest": {"type": "int", "range": [2, 20]}}}
class CustomerPairSwap : public hsf::Neighborhood<Model> {
public:
    CustomerPairSwap(const Model& md, int k) : M(md) {
        K = std::max(1, std::min(k, std::max(1, M.n)));
        near.resize(M.m);
        inNear.assign((size_t)M.m * std::max(1, M.n), 0);
        std::vector<int> idx(M.n);
        double maxc = 0.0, maxf = 0.0;
        for (int j = 0; j < M.m; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            int kk = std::min(K, M.n);
            std::partial_sort(idx.begin(), idx.begin() + kk, idx.end(),
                              [&](int a, int b) { return cst(a, j) < cst(b, j); });
            near[j].assign(idx.begin(), idx.begin() + kk);
            for (int t : near[j]) inNear[(size_t)j * M.n + t] = 1;
            for (int i = 0; i < M.n; ++i) maxc = std::max(maxc, std::fabs(cst(i, j)));
        }
        for (int i = 0; i < M.n; ++i) maxf = std::max(maxf, std::fabs(M.fixed[i]));
        pen = std::max(1.0, M.penalty) * (maxc + maxf + 1.0);
        owner.assign(M.m, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        std::fill(owner.begin(), owner.end(), -1);
        int N = std::min((int)s.size(), M.n);
        for (int i = 0; i < N; ++i)
            for (int j : s[i]) if (j >= 0 && j < M.m) owner[j] = i;
        for (int j1 = 0; j1 < M.m; ++j1) {
            int i1 = owner[j1];
            if (i1 < 0) continue;
            for (int i2 : near[j1]) {
                if (i2 == i1 || i2 >= N) continue;
                for (int j2 : s[i2]) {
                    if (j2 < 0 || j2 >= M.m || j2 == j1) continue;
                    // evita duplicados: el par también lo genera j2 si i1 está entre sus cercanos
                    if (j2 < j1 && inNear[(size_t)j2 * M.n + i1]) continue;
                    if (j1 < j2) out.push_back(mk(j1, i1, j2, i2));
                    else out.push_back(mk(j2, i2, j1, i1));
                }
            }
        }
        // traslados simples (b = -1) a los centros cercanos: siempre presentes, permiten cambiar
        // cargas y abrir/cerrar centros, cosa que el intercambio puro no puede
        size_t before = out.size();
        for (int j = 0; j < M.m; ++j)
            for (int t : near[j])
                if (t != owner[j] && t < N) out.push_back(mk(j, owner[j], -1, t));
        if (out.size() == before)
            for (int j = 0; j < M.m; ++j)
                for (int t = 0; t < N; ++t)
                    if (t != owner[j]) out.push_back(mk(j, owner[j], -1, t));
        // consolidation moves: close a centre (b = -2) / attract to a centre the customers that
        // get cheaper there (b = -3); a single swap or move cannot do this
        load.assign(std::max(N, 1), 0.0);
        for (int i = 0; i < N; ++i) load[i] = sumLoad(s[i]);
        if (N > 1)
            for (int i = 0; i < N; ++i)
                if (!s[i].empty()) out.push_back(mk(-1, i, -2, -1));
        for (int t = 0; t < N; ++t) {
            bool ok = false;
            for (int j = 0; j < M.m && !ok; ++j) {
                int o = owner[j];
                if (o == t) continue;
                if ((o < 0 || cst(t, j) < cst(o, j)) && load[t] + M.demand[j] <= M.capacity[t]) ok = true;
            }
            if (ok) out.push_back(mk(-1, -1, -3, t));
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        if (mv[2] == -2) return applyClose(s, mv[1]);
        if (mv[2] == -3) return applyAttract(s, mv[3]);
        Sol r = s;
        int a = mv[0], ia = mv[1], b = mv[2], ib = mv[3];
        if (b < 0) {
            if (ia >= 0 && ia < (int)r.size()) {
                auto& v = r[ia];
                auto it = std::find(v.begin(), v.end(), a);
                if (it != v.end()) { *it = v.back(); v.pop_back(); }
            }
            if (ib >= 0 && ib < (int)r.size()) r[ib].push_back(a);
            return r;
        }
        if (ia >= 0 && ia < (int)r.size()) {
            auto it = std::find(r[ia].begin(), r[ia].end(), a);
            if (it != r[ia].end()) *it = b;
        }
        if (ib >= 0 && ib < (int)r.size()) {
            auto it = std::find(r[ib].begin(), r[ib].end(), b);
            if (it != r[ib].end()) *it = a;
        }
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        return M.objective(apply(s, mv)) - M.objective(s);
    }

    Move tabu_key(const Move& mv) override {
        if (mv[2] < -1) return mv;
        return mk(mv[0], mv[3], mv[2], mv[1]);
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        if (mv[2] < -1) return delta(s, mv);
        int a = mv[0], ia = mv[1], b = mv[2], ib = mv[3];
        if (b < 0) {
            double d = M.demand[a];
            double e = cst(ib, a);
            if (ia >= 0) {
                e -= cst(ia, a);
                if (s[ia].size() == 1) e -= M.fixed[ia];
                double l = sumLoad(s[ia]);
                e += pen * (over(l - d, ia) - over(l, ia));
            } else e -= pen * (d + 1.0);
            if (s[ib].empty()) e += M.fixed[ib];
            double l2 = sumLoad(s[ib]);
            e += pen * (over(l2 + d, ib) - over(l2, ib));
            return e;
        }
        double e = cst(ib, a) + cst(ia, b) - cst(ia, a) - cst(ib, b);
        double la = sumLoad(s[ia]), lb = sumLoad(s[ib]);
        double dd = M.demand[b] - M.demand[a];
        e += pen * (over(la + dd, ia) - over(la, ia) + over(lb - dd, ib) - over(lb, ib));
        return e;
    }

private:
    const Model& M;
    int K;
    double pen;
    std::vector<std::vector<int>> near;
    std::vector<char> inNear;
    std::vector<int> owner;
    std::vector<int> ownA;
    std::vector<double> load, loadA;
    std::vector<std::pair<double, int>> cand;

    Sol applyClose(const Sol& s, int i) {
        Sol r = s;
        int R = (int)r.size();
        if (i < 0 || i >= R || R < 2) return r;
        std::vector<int> cust;
        cust.swap(r[i]);
        int N = std::min(R, M.n);
        loadA.assign(std::max(N, 1), 0.0);
        std::vector<int> opens;
        for (int k = 0; k < N; ++k) {
            if (k == i) continue;
            loadA[k] = sumLoad(r[k]);
            if (!r[k].empty()) opens.push_back(k);
        }
        if (opens.empty())
            for (int k = 0; k < N; ++k) if (k != i) opens.push_back(k);
        if (opens.empty()) { r[i].swap(cust); return r; }
        std::sort(cust.begin(), cust.end(), [&](int x, int y) { return M.demand[x] > M.demand[y]; });
        for (int j : cust) {
            int bf = -1, ba = -1;
            double cf = std::numeric_limits<double>::infinity(), ca = cf;
            for (int k : opens) {
                double c = cst(k, j);
                if (c < ca) { ca = c; ba = k; }
                if (loadA[k] + M.demand[j] <= M.capacity[k] && c < cf) { cf = c; bf = k; }
            }
            int k = bf >= 0 ? bf : ba;
            r[k].push_back(j);
            loadA[k] += M.demand[j];
        }
        return r;
    }

    Sol applyAttract(const Sol& s, int t) {
        Sol r = s;
        int R = (int)r.size();
        if (t < 0 || t >= R || t >= M.n) return r;
        int N = std::min(R, M.n);
        ownA.assign(M.m, -1);
        for (int i = 0; i < N; ++i)
            for (int j : r[i]) if (j >= 0 && j < M.m) ownA[j] = i;
        double lt = sumLoad(r[t]);
        cand.clear();
        for (int j = 0; j < M.m; ++j) {
            int o = ownA[j];
            if (o == t) continue;
            if (o < 0) cand.push_back({std::numeric_limits<double>::max(), j});
            else {
                double g = cst(o, j) - cst(t, j);
                if (g > 0) cand.push_back({g, j});
            }
        }
        std::sort(cand.begin(), cand.end(),
                  [](const std::pair<double, int>& x, const std::pair<double, int>& y) {
                      return x.first > y.first || (x.first == y.first && x.second < y.second);
                  });
        for (auto& pr : cand) {
            int j = pr.second;
            double d = M.demand[j];
            if (lt + d > M.capacity[t]) continue;
            int o = ownA[j];
            if (o >= 0) {
                auto& v = r[o];
                auto it = std::find(v.begin(), v.end(), j);
                if (it != v.end()) { *it = v.back(); v.pop_back(); }
            }
            r[t].push_back(j);
            lt += d;
        }
        return r;
    }

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    double over(double l, int i) const { return std::max(0.0, l - M.capacity[i]); }
    double sumLoad(const std::vector<int>& v) const {
        double l = 0.0;
        for (int j : v) l += M.demand[j];
        return l;
    }
    static Move mk(int a, int b, int c, int d) {
        Move mv; mv.fill(0);
        mv[0] = a; mv[1] = b; mv[2] = c; mv[3] = d;
        return mv;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_nearest", 5.0);
    return std::make_unique<CustomerPairSwap>(model, k);
}
