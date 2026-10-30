// COMPONENT: {"name": "noisy_giffler_thompson_rebuild", "slot": "perturbation", "params": {"noise": {"type": "float", "range": [0.05, 3.0]}, "random_pick_prob": {"type": "float", "range": [0.0, 0.3]}}}
class NoisyGifflerThompsonRebuild : public hsf::Perturbation<JobShop> {
    using Sol = JobShop::Solution;
    const JobShop& M;
    double noise, rpick, avgp;
    std::vector<int> start, nxt, jr, mr;
    std::vector<double> pri;

    Sol gt(Rng& rng) {
        Sol out(M.m);
        nxt.assign(M.n, 0), jr.assign(M.n, 0), mr.assign(M.m, 0);
        for (int step = 0; step < M.n_ops; ++step) {
            long long cstar = std::numeric_limits<long long>::max();
            int best = -1;
            for (int j = 0; j < M.n; ++j) {
                int k = nxt[j];
                if (k >= (int)M.routes[j].size()) continue;
                auto [mm, p] = M.routes[j][k];
                long long est = std::max(jr[j], mr[mm]);
                if (est + p < cstar) cstar = est + p, best = j;
            }
            int mstar = M.routes[best][nxt[best]].first;
            bool rnd = rng.uniform() < rpick;
            int chosen = -1, cnt = 0;
            double bp = std::numeric_limits<double>::infinity();
            for (int j = 0; j < M.n; ++j) {
                int k = nxt[j];
                if (k >= (int)M.routes[j].size() || M.routes[j][k].first != mstar) continue;
                long long est = std::max(jr[j], mr[mstar]);
                if (!(est < cstar || j == best)) continue;
                if (rnd) { if (rng.below(++cnt) == 0) chosen = j; }
                else {
                    double pv = pri[M.off[j] + k];
                    if (pv < bp) bp = pv, chosen = j;
                }
            }
            int k = nxt[chosen];
            int p = M.routes[chosen][k].second;
            int est = std::max(jr[chosen], mr[mstar]);
            jr[chosen] = mr[mstar] = est + p;
            out[mstar].push_back(chosen);
            ++nxt[chosen];
        }
        return out;
    }

public:
    NoisyGifflerThompsonRebuild(const JobShop& model, double nz, double rp) : M(model), noise(nz), rpick(rp) {
        avgp = M.n_ops > 0 ? std::max(1.0, (double)M.horizon / M.n_ops) : 1.0;
        pri.assign(M.n_ops, 0.0);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int mk;
        M.schedule(s, start, mk);
        std::normal_distribution<double> nd(0.0, 1.0);
        double sigma = noise * std::max(1.0, strength) * avgp;
        for (int attempt = 0; attempt < 8; ++attempt) {
            for (int op = 0; op < M.n_ops; ++op) pri[op] = start[op] + sigma * nd(rng.g);
            Sol out = gt(rng);
            if (out != s) return out;
            sigma *= 2.0;
        }
        for (int t = 0; t < 50; ++t) { Sol r = M.random(rng); if (r != s) return r; }
        return gt(rng);
    }
};

std::unique_ptr<hsf::Perturbation<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<NoisyGifflerThompsonRebuild>(model, params.get("noise", 0.5),
                                                         params.get("random_pick_prob", 0.05));
}
