// COMPONENT: {"name": "facility_close_open_greedy_redistribution", "slot": "neighborhood", "params": {"pull_frac": {"type": "float", "range": [0.3, 1.0]}}}
class CloseOpenFacility : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    CloseOpenFacility(const Model& model, double pf) : M(model), pullFrac(pf) {
        nf = (int)M.capacity.size();
        nc = (int)M.demand.size();
        load.assign(nf, 0.0);
        cnt.assign(nf, 0);
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        const auto& a = s[0];
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j = 0; j < nc; ++j)
            if (a[j] >= 0) cnt[a[j]]++;
        for (int f = 0; f < nf; ++f) {
            if (cnt[f] > 0) {
                if (nf > 1) out.push_back(mk(0, f));
            } else {
                out.push_back(mk(1, f));
            }
        }
    }

    Sol apply(const Sol& s, const Move& mv) override {
        Sol r = s;
        auto& a = r[0];
        const double EPS = 1e-9;
        std::fill(load.begin(), load.end(), 0.0);
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j = 0; j < nc; ++j)
            if (a[j] >= 0) { load[a[j]] += M.demand[j]; cnt[a[j]]++; }
        int i = mv[1];
        if (mv[0] == 0) {
            buf.clear();
            for (int j = 0; j < nc; ++j)
                if (a[j] == i) buf.push_back(j);
            std::stable_sort(buf.begin(), buf.end(),
                             [&](int x, int y) { return M.demand[x] > M.demand[y]; });
            for (int j : buf) {
                double d = M.demand[j];
                load[i] -= d; cnt[i]--;
                int best = -1; double bc = 0.0;
                for (int f = 0; f < nf; ++f) {  // abiertos con hueco
                    if (f == i || cnt[f] == 0) continue;
                    if (load[f] + d > M.capacity[f] + EPS) continue;
                    double c = M.cost[f][j];
                    if (best < 0 || c < bc) { best = f; bc = c; }
                }
                if (best < 0) {  // cualquiera con hueco, pagando apertura
                    for (int f = 0; f < nf; ++f) {
                        if (f == i || load[f] + d > M.capacity[f] + EPS) continue;
                        double c = M.cost[f][j] + (cnt[f] == 0 ? M.fixed[f] : 0.0);
                        if (best < 0 || c < bc) { best = f; bc = c; }
                    }
                }
                if (best < 0) {  // sin hueco: el más barato (infactible)
                    for (int f = 0; f < nf; ++f) {
                        if (f == i) continue;
                        double c = M.cost[f][j];
                        if (best < 0 || c < bc) { best = f; bc = c; }
                    }
                }
                if (best < 0) { load[i] += d; cnt[i]++; continue; }
                a[j] = best; load[best] += d; cnt[best]++;
            }
        } else {
            gains.clear();
            for (int j = 0; j < nc; ++j) {
                int cur = a[j];
                if (cur == i) continue;
                double g = (cur < 0) ? 1e300 : (M.cost[cur][j] - M.cost[i][j]);
                if (g > 0) gains.push_back({g, j});
            }
            std::stable_sort(gains.begin(), gains.end(),
                             [](const std::pair<double, int>& x, const std::pair<double, int>& y) {
                                 return x.first > y.first;
                             });
            double limit = M.capacity[i] * pullFrac;
            for (const auto& pr : gains) {
                int j = pr.second;
                double d = M.demand[j];
                if (load[i] + d > limit + EPS) continue;
                int cur = a[j];
                if (cur >= 0) { load[cur] -= d; cnt[cur]--; }
                a[j] = i; load[i] += d; cnt[i]++;
            }
        }
        return r;
    }

    double delta(const Sol& s, const Move& mv) override {
        sync(s);
        Sol r = apply(s, mv);
        return M.objective(r) - base;
    }

    Move tabu_key(const Move& mv) override { return mk(1 - mv[0], mv[1]); }

private:
    const Model& M;
    double pullFrac = 1.0;
    int nf = 0, nc = 0;
    std::vector<double> load;
    std::vector<int> cnt, buf;
    std::vector<std::pair<double, int>> gains;
    Sol work;
    double base = 0.0;
    bool valid = false;

    static Move mk(int t, int f) {
        Move m{};
        m[0] = t; m[1] = f;
        return m;
    }
    void sync(const Sol& s) {
        if (!valid || work != s) {
            work = s;
            base = M.objective(work);
            valid = true;
        }
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    double pf = params.get("pull_frac", 1.0);
    return std::make_unique<CloseOpenFacility>(model, pf);
}
