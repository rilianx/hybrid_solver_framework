// COMPONENT: {"name": "facility_close_open_greedy_repair", "slot": "neighborhood", "params": {"swap_candidates": {"type": "int", "range": [0, 10]}}}
class FacilityCloseOpen : public hsf::Neighborhood<Model> {
public:
    FacilityCloseOpen(const Model& md, int sc) : M(md), S(std::max(0, sc)) {
        owner.assign(M.m, -1);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        int N = std::min((int)s.size(), M.n);
        closedList.clear();
        for (int i = 0; i < N; ++i) {
            if (!s[i].empty()) out.push_back(mk(0, i, 0));
            else { out.push_back(mk(1, i, 0)); closedList.push_back(i); }
        }
        if (S > 0 && !closedList.empty()) {
            for (int i = 0; i < N; ++i) {
                if (s[i].empty()) continue;
                scored.clear();
                for (int k : closedList) {
                    double sc = M.fixed[k];
                    for (int j : s[i]) if (j >= 0 && j < M.m) sc += cst(k, j);
                    scored.emplace_back(sc, k);
                }
                int take = std::min(S, (int)scored.size());
                std::partial_sort(scored.begin(), scored.begin() + take, scored.end());
                for (int q = 0; q < take; ++q) out.push_back(mk(2, i, scored[q].second));
            }
        }
        if (N > 0) out.push_back(mk(3, 0, 0));  // reparación greedy pura sobre los centros abiertos
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        int N = (int)r.size();
        load.assign(N, 0.0);
        std::fill(owner.begin(), owner.end(), -1);
        for (int i = 0; i < N; ++i)
            for (int j : r[i]) if (j >= 0 && j < M.m) { load[i] += M.demand[j]; owner[j] = i; }
        int type = mv[0];
        if (type == 0) {
            if (mv[1] >= 0 && mv[1] < N) closeFac(r, mv[1], -1);
        } else if (type == 1) {
            if (mv[1] >= 0 && mv[1] < N) openFac(r, mv[1]);
        } else if (type == 2) {
            if (mv[1] >= 0 && mv[1] < N && mv[2] >= 0 && mv[2] < N) {
                closeFac(r, mv[1], mv[2]);
                openFac(r, mv[2]);
            }
        }
        polish(r);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        return M.objective(apply(s, mv)) - M.objective(s);
    }

    Move tabu_key(const Move& mv) override {
        if (mv[0] == 0) return mk(1, mv[1], 0);
        if (mv[0] == 1) return mk(0, mv[1], 0);
        if (mv[0] == 3) return mv;
        return mk(2, mv[2], mv[1]);
    }

private:
    const Model& M;
    int S;
    std::vector<int> owner;
    std::vector<double> load;
    std::vector<int> closedList;
    std::vector<std::pair<double, int>> scored;
    std::vector<int> lst;
    std::vector<std::pair<double, int>> cand;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }
    static Move mk(int a, int b, int c) {
        Move mv; mv.fill(0);
        mv[0] = a; mv[1] = b; mv[2] = c;
        return mv;
    }

    void place(Sol& r, int j, int t) {
        r[t].push_back(j);
        load[t] += M.demand[j];
        owner[j] = t;
    }

    void closeFac(Sol& r, int i, int pref) {
        int N = (int)r.size();
        lst = r[i];
        r[i].clear();
        load[i] = 0.0;
        if (N <= 1) { for (int j : lst) place(r, j, i); return; }
        std::sort(lst.begin(), lst.end(), [&](int a, int b) { return M.demand[a] > M.demand[b]; });
        const double eps = Model::EPS;
        for (int j : lst) {
            if (j < 0 || j >= M.m) continue;
            double d = M.demand[j];
            int best = -1; double bv = std::numeric_limits<double>::infinity();
            // 1) centros abiertos (o el preferido) con capacidad residual
            for (int t = 0; t < N; ++t) {
                if (t == i) continue;
                if (r[t].empty() && t != pref) continue;
                if (load[t] + d > M.capacity[t] + eps) continue;
                double v = cst(t, j);
                if (v < bv) { bv = v; best = t; }
            }
            // 2) cualquier centro con capacidad, pagando apertura si está cerrado
            if (best < 0) {
                for (int t = 0; t < N; ++t) {
                    if (t == i) continue;
                    if (load[t] + d > M.capacity[t] + eps) continue;
                    double v = cst(t, j) + (r[t].empty() ? M.fixed[t] : 0.0);
                    if (v < bv) { bv = v; best = t; }
                }
            }
            // 3) mínimo exceso de capacidad
            if (best < 0) {
                double bo = std::numeric_limits<double>::infinity();
                for (int t = 0; t < N; ++t) {
                    if (t == i) continue;
                    double o = load[t] + d - M.capacity[t];
                    double v = cst(t, j);
                    if (o < bo - eps || (std::fabs(o - bo) <= eps && v < bv)) { bo = o; bv = v; best = t; }
                }
            }
            if (best < 0) best = i;
            place(r, j, best);
        }
    }

    // Reasignación greedy: cada cliente pasa al centro abierto más barato con capacidad residual
    // (o sale de un centro sobrecargado). Cada paso baja costo de asignación o exceso: termina.
    void polish(Sol& r) {
        const double eps = Model::EPS;
        const double inf = std::numeric_limits<double>::infinity();
        int N = (int)r.size();
        for (int pass = 0; pass < 3; ++pass) {
            bool changed = false;
            for (int o = 0; o < N; ++o) {
                size_t p = 0;
                while (p < r[o].size()) {
                    int j = r[o][p];
                    if (j < 0 || j >= M.m) { ++p; continue; }
                    double d = M.demand[j];
                    bool over = load[o] > M.capacity[o] + eps;
                    double bv = over ? inf : cst(o, j) - eps;
                    int best = -1;
                    for (int t = 0; t < N; ++t) {
                        if (t == o || r[t].empty()) continue;
                        if (load[t] + d > M.capacity[t] + eps) continue;
                        double v = cst(t, j);
                        if (v < bv) { bv = v; best = t; }
                    }
                    if (best < 0) { ++p; continue; }
                    r[o][p] = r[o].back();
                    r[o].pop_back();
                    load[o] -= d;
                    place(r, j, best);
                    changed = true;
                }
            }
            if (!changed) break;
        }
    }

    void openFac(Sol& r, int k) {
        const double eps = Model::EPS;
        cand.clear();
        for (int j = 0; j < M.m; ++j) {
            int o = owner[j];
            if (o == k) continue;
            double cur = (o >= 0) ? cst(o, j) : std::numeric_limits<double>::max() / 4;
            double gain = cur - cst(k, j);
            if (o >= 0 && load[o] > M.capacity[o] + eps) gain += M.fixed[k] + 1.0;  // alivia sobrecarga
            if (gain > 0) cand.emplace_back(-gain / std::max(M.demand[j], 1e-12), j);
        }
        std::sort(cand.begin(), cand.end());
        for (auto& pc : cand) {
            int j = pc.second;
            double d = M.demand[j];
            if (load[k] + d > M.capacity[k] + eps) continue;
            int o = owner[j];
            if (o >= 0) {
                auto& v = r[o];
                auto it = std::find(v.begin(), v.end(), j);
                if (it != v.end()) { *it = v.back(); v.pop_back(); }
                load[o] -= d;
            }
            place(r, j, k);
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int sc = (int)params.get("swap_candidates", 3.0);
    return std::make_unique<FacilityCloseOpen>(model, sc);
}
