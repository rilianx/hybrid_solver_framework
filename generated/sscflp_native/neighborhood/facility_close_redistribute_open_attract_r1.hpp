// COMPONENT: {"name": "facility_close_redistribute_open_attract", "slot": "neighborhood", "params": {"close_target": {"type": "cat", "values": ["open_only", "any"]}, "overload_priority": {"type": "float", "range": [0.0, 10.0]}}}
class FacilityCloseOpen : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    FacilityCloseOpen(const Model& md, bool anyTarget, double ovl) : M(md), allowAny(anyTarget) {
        double maxC = 0;
        for (double v : M.cost) maxC = std::max(maxC, v);
        bonus = ovl * (1.0 + maxC);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        sync(s);
        int nOpen = 0;
        for (int i = 0; i < M.n; ++i) if (cnt[i] > 0) ++nOpen;
        for (int i = 0; i < M.n; ++i) {
            Move mv{};
            mv[1] = i;
            if (cnt[i] > 0) {
                if (M.n < 2) continue;
                if (!allowAny && nOpen < 2) continue;
                mv[0] = 0;  // cerrar y redistribuir
            } else {
                mv[0] = 1;  // abrir y atraer
            }
            out.push_back(mv);
        }
        if (out.empty()) { Move mv{}; mv[0] = 1; mv[1] = 0; out.push_back(mv); }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        build(s[0], mv, r[0]);
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        tmp = s;
        build(s[0], mv, tmp[0]);
        return M.objective(tmp) - obj;
    }

    Move tabu_key(const Move& mv) override {
        Move k{}; k[0] = 1 - mv[0]; k[1] = mv[1];
        return k;
    }

private:
    const Model& M;
    bool allowAny = false;
    double bonus = 0;
    std::vector<int> ca, cnt;
    std::vector<double> load;
    double obj = 0;
    bool valid = false;
    Sol tmp;
    // memoria de trabajo
    std::vector<double> wl;
    std::vector<int> wc, buf;
    std::vector<std::pair<double, int>> cand;

    double cst(int i, int j) const { return M.cost[(size_t)i * M.m + j]; }

    void sync(const Sol& s) {
        const std::vector<int>& a = s[0];
        if (valid && a == ca) return;
        ca = a;
        load.assign(M.n, 0.0);
        cnt.assign(M.n, 0);
        for (int j = 0; j < M.m; ++j) {
            int f = a[j];
            if (f >= 0 && f < M.n) { load[f] += M.demand[j]; cnt[f]++; }
        }
        obj = M.objective(s);
        valid = true;
    }

    // determinista: misma (a, mv) -> misma salida
    void build(const std::vector<int>& a, const Move& mv, std::vector<int>& out) {
        int n = M.n, m = M.m, i = mv[1];
        wl.assign(n, 0.0);
        wc.assign(n, 0);
        for (int j = 0; j < m; ++j) {
            int f = a[j];
            if (f >= 0 && f < n) { wl[f] += M.demand[j]; wc[f]++; }
        }
        if (mv[0] == 0) {
            buf.clear();
            for (int j = 0; j < m; ++j) if (a[j] == i) buf.push_back(j);
            std::sort(buf.begin(), buf.end(), [&](int x, int y) {
                return M.demand[x] > M.demand[y] || (M.demand[x] == M.demand[y] && x < y);
            });
            for (int j : buf) {
                double d = M.demand[j];
                wl[i] -= d; wc[i]--;
                int bestFit = -1, bestAny = -1;
                double sFit = std::numeric_limits<double>::infinity();
                double eAny = std::numeric_limits<double>::infinity(), cAny = eAny;
                for (int g = 0; g < n; ++g) {
                    if (g == i) continue;
                    bool open = wc[g] > 0;
                    if (!allowAny && !open) continue;
                    double c = cst(g, j);
                    if (wl[g] + d <= M.capacity[g] + 1e-9) {
                        double sc = c + (open ? 0.0 : M.fixed[g]);
                        if (sc < sFit) { sFit = sc; bestFit = g; }
                    } else {
                        double e = wl[g] + d - M.capacity[g];
                        if (e < eAny || (e == eAny && c < cAny)) { eAny = e; cAny = c; bestAny = g; }
                    }
                }
                int g = bestFit >= 0 ? bestFit : bestAny;
                if (g < 0) g = i;
                out[j] = g;
                wl[g] += d; wc[g]++;
            }
        } else {
            if (wc[i] > 0) return;
            cand.clear();
            for (int j = 0; j < m; ++j) {
                int f = a[j];
                if (f < 0 || f >= n) { cand.push_back({1e300, j}); continue; }
                double sv = cst(f, j) - cst(i, j);
                if (wl[f] > M.capacity[f] + 1e-9) sv += bonus;
                if (sv > 0) cand.push_back({sv, j});
            }
            std::sort(cand.begin(), cand.end(), [](const std::pair<double, int>& x, const std::pair<double, int>& y) {
                return x.first > y.first || (x.first == y.first && x.second < y.second);
            });
            for (auto& pr : cand) {
                int j = pr.second;
                double d = M.demand[j];
                if (wl[i] + d > M.capacity[i] + 1e-9) continue;
                int f = a[j];
                if (f >= 0 && f < n) { wl[f] -= d; wc[f]--; }
                out[j] = i;
                wl[i] += d; wc[i]++;
            }
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool anyT = params.text("close_target", "open_only") == "any";
    double ovl = params.get("overload_priority", 1.0);
    return std::make_unique<FacilityCloseOpen>(model, anyT, ovl);
}
