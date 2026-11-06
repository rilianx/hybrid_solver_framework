// COMPONENT: {"name": "customer_shift_knn", "slot": "neighborhood", "params": {"k_nearest": {"type": "int", "range": [2, 40]}}}
class CustomerShiftKnn : public hsf::Neighborhood<Model> {
public:
    CustomerShiftKnn(const Model& md, int k) : M(md) {
        K = std::max(1, std::min(k, std::max(1, M.n)));
        near.resize(M.m);
        ord.resize((size_t)M.m * M.n);
        std::vector<int> idx(M.n);
        double maxc = 0.0, maxf = 0.0;
        for (int j = 0; j < M.m; ++j) {
            std::iota(idx.begin(), idx.end(), 0);
            int kk = std::min(K, M.n);
            std::sort(idx.begin(), idx.end(),
                      [&](int a, int b) { return cst(a, j) < cst(b, j); });
            near[j].assign(idx.begin(), idx.begin() + kk);
            std::copy(idx.begin(), idx.end(), ord.begin() + (size_t)j * M.n);
            for (int i = 0; i < M.n; ++i) maxc = std::max(maxc, std::fabs(cst(i, j)));
        }
        mark.assign(M.n, 0);
        openv.assign(M.n, 0);
        wantOpen.assign(M.n, 0);
        loadBuf.assign(M.n, 0.0);
        moved.assign(M.m, 0);
        for (int i = 0; i < M.n; ++i) maxf = std::max(maxf, std::fabs(M.fixed[i]));
        pen = std::max(1.0, M.penalty) * (maxc + maxf + 1.0);
        owner.assign(M.m, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        buildOwner(s);
        int N = std::min((int)s.size(), M.n);
        for (int i = 0; i < M.n; ++i) {
            openv[i] = (i < N && !s[i].empty()) ? 1 : 0;
            wantOpen[i] = 0;
        }
        for (int j = 0; j < M.m; ++j) {
            int o = owner[j];
            ++stamp;
            for (int t : near[j]) {
                if (t != o && t < N && mark[t] != stamp) {
                    mark[t] = stamp;
                    out.push_back(mk(j, o, t));
                    if (!openv[t] && (o < 0 || cst(t, j) < cst(o, j))) wantOpen[t] = 1;
                }
            }
            // también las K instalaciones abiertas más baratas para este cliente
            int cnt = 0;
            const int* oj = ord.data() + (size_t)j * M.n;
            for (int q = 0; q < M.n && cnt < K; ++q) {
                int t = oj[q];
                if (t >= N || t == o || !openv[t]) continue;
                ++cnt;
                if (mark[t] != stamp) {
                    mark[t] = stamp;
                    out.push_back(mk(j, o, t));
                }
            }
        }
        if (out.empty()) {
            for (int j = 0; j < M.m; ++j)
                for (int t = 0; t < N; ++t)
                    if (t != owner[j]) out.push_back(mk(j, owner[j], t));
        }
        // movimientos compuestos: cerrar una instalación abierta / abrir una cerrada prometedora
        if (N >= 2) {
            for (int f = 0; f < N; ++f)
                if (openv[f]) out.push_back(mkT(1, f));
            for (int t = 0; t < N; ++t)
                if (!openv[t] && wantOpen[t]) out.push_back(mkT(2, t));
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        if (mv[3] == 1) return applyClose(s, mv[1]);
        if (mv[3] == 2) return applyOpen(s, mv[2]);
        Sol r = s;
        int j = mv[0], f = mv[1], t = mv[2];
        if (f >= 0 && f < (int)r.size()) {
            auto& v = r[f];
            auto it = std::find(v.begin(), v.end(), j);
            if (it != v.end()) { *it = v.back(); v.pop_back(); }
        }
        if (t >= 0 && t < (int)r.size()) r[t].push_back(j);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        return M.objective(apply(s, mv)) - M.objective(s);
    }

    Move tabu_key(const Move& mv) override {
        if (mv[3] == 1) return mkT(2, mv[1]);
        if (mv[3] == 2) return mkT(1, mv[2]);
        return mk(mv[0], mv[2], mv[1]);
    }

    bool has_estimate() const override { return true; }

    double estimate(const Sol& s, const Move& mv) override {
        if (mv[3] != 0) return delta(s, mv);
        int j = mv[0], f = mv[1], t = mv[2];
        double d = M.demand[j];
        double e = cst(t, j);
        if (f >= 0 && f < (int)s.size()) {
            e -= cst(f, j);
            if (s[f].size() == 1) e -= M.fixed[f];
            double lf = sumLoad(s[f]);
            e += pen * (over(lf - d, f) - over(lf, f));
        } else {
            e -= pen * (d + 1.0);
        }
        if (s[t].empty()) e += M.fixed[t];
        double lt = sumLoad(s[t]);
        e += pen * (over(lt + d, t) - over(lt, t));
        return e;
    }

private:
    const Model& M;
    int K;
    double pen;
    std::vector<std::vector<int>> near;
    std::vector<int> owner;
    std::vector<int> ord;
    std::vector<int> mark;
    std::vector<char> openv;
    std::vector<char> wantOpen;
    std::vector<double> loadBuf;
    std::vector<char> moved;
    std::vector<std::pair<double, int>> cand;
    int stamp = 0;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    double over(double l, int i) const { return std::max(0.0, l - M.capacity[i]); }
    double sumLoad(const std::vector<int>& v) const {
        double l = 0.0;
        for (int j : v) if (j >= 0 && j < M.m) l += M.demand[j];
        return l;
    }
    void buildOwner(const Sol& s) {
        std::fill(owner.begin(), owner.end(), -1);
        for (int i = 0; i < (int)s.size(); ++i)
            for (int j : s[i]) if (j >= 0 && j < M.m) owner[j] = i;
    }

    // cierra f: cada cliente va a la abierta más barata con capacidad (si no, la abierta más barata)
    Sol applyClose(const Sol& s, int f) {
        Sol r = s;
        int N = std::min((int)r.size(), M.n);
        if (f < 0 || f >= N || N < 2) return r;
        std::vector<int> cust = r[f];
        r[f].clear();
        for (int i = 0; i < N; ++i) loadBuf[i] = (i == f) ? 0.0 : sumLoad(r[i]);
        for (int j : cust) {
            if (j < 0 || j >= M.m) { r[f].push_back(j); continue; }
            double d = M.demand[j];
            int bFit = -1, bOpen = -1, bAny = -1;
            double cFit = std::numeric_limits<double>::infinity(), cOpen = cFit, cAny = cFit;
            for (int i = 0; i < N; ++i) {
                if (i == f) continue;
                double c = cst(i, j);
                if (c < cAny) { cAny = c; bAny = i; }
                if (s[i].empty()) continue;
                if (c < cOpen) { cOpen = c; bOpen = i; }
                if (loadBuf[i] + d <= M.capacity[i] + 1e-9 && c < cFit) { cFit = c; bFit = i; }
            }
            int b = bFit >= 0 ? bFit : (bOpen >= 0 ? bOpen : bAny);
            if (b < 0) { r[f].push_back(j); continue; }
            r[b].push_back(j);
            loadBuf[b] += d;
        }
        return r;
    }

    // abre t: atrae a los clientes que más ahorran, respetando su capacidad
    Sol applyOpen(const Sol& s, int t) {
        Sol r = s;
        int N = std::min((int)r.size(), M.n);
        if (t < 0 || t >= N) return r;
        cand.clear();
        for (int i = 0; i < N; ++i) {
            if (i == t) continue;
            for (int j : s[i]) {
                if (j < 0 || j >= M.m) continue;
                double g = cst(i, j) - cst(t, j);
                if (g > 0) cand.push_back({g, j});
            }
        }
        if (cand.empty()) return r;
        std::sort(cand.begin(), cand.end(),
                  [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
                      return a.first > b.first;
                  });
        double load = sumLoad(s[t]);
        double cap = M.capacity[t];
        int chosen = 0;
        for (auto& c : cand) {
            int j = c.second;
            double d = M.demand[j];
            if (load + d <= cap + 1e-9 || chosen == 0) {
                moved[j] = 1;
                r[t].push_back(j);
                load += d;
                ++chosen;
            }
        }
        for (int i = 0; i < N; ++i) {
            if (i == t) continue;
            auto& v = r[i];
            v.erase(std::remove_if(v.begin(), v.end(),
                                   [&](int j) { return j >= 0 && j < M.m && moved[j]; }),
                    v.end());
        }
        for (auto& c : cand) moved[c.second] = 0;
        return r;
    }

    static Move mk(int a, int b, int c) {
        Move mv; mv.fill(0);
        mv[0] = a; mv[1] = b; mv[2] = c;
        return mv;
    }
    static Move mkT(int type, int fac) {
        Move mv; mv.fill(0);
        mv[0] = -1; mv[1] = fac; mv[2] = fac; mv[3] = type;
        return mv;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int k = (int)params.get("k_nearest", 8.0);
    return std::make_unique<CustomerShiftKnn>(model, k);
}
