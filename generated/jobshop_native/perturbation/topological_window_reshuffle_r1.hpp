// COMPONENT: {"name": "topological_window_reshuffle", "slot": "perturbation", "params": {"window": {"type": "int", "range": [3, 40]}, "windows_per_strength": {"type": "float", "range": [0.3, 3.0]}}}
class TopologicalWindowReshuffle : public hsf::Perturbation<JobShop> {
    using Sol = JobShop::Solution;
    const JobShop& M;
    int win;
    double wps;
    std::vector<int> start, L, stamp, avail, W, placedSt;
    int clock = 0;

    void build_order(const Sol& s) {
        int mk;
        M.schedule(s, start, mk);
        L.resize(M.n_ops);
        std::iota(L.begin(), L.end(), 0);
        std::sort(L.begin(), L.end(), [&](int a, int b) {
            if (start[a] != start[b]) return start[a] < start[b];
            int ka = a - M.off[M.job_of[a]], kb = b - M.off[M.job_of[b]];
            if (ka != kb) return ka < kb;
            return a < b;
        });
    }
    Sol decode(const std::vector<int>& ord) const {
        Sol out(M.m);
        for (int op : ord) {
            int j = M.job_of[op];
            out[M.routes[j][op - M.off[j]].first].push_back(j);
        }
        return out;
    }
    void reshuffle(std::vector<int>& ord, int pos, int w, Rng& rng) {
        ++clock;
        W.assign(ord.begin() + pos, ord.begin() + pos + w);
        for (int op : W) stamp[op] = clock;
        avail.clear();
        for (int op : W) {
            int k = op - M.off[M.job_of[op]];
            if (k == 0 || stamp[op - 1] != clock) avail.push_back(op);  // predecesor fuera de la ventana
        }
        int idx = pos;
        while (!avail.empty()) {
            int r = rng.below((int)avail.size());
            int op = avail[r];
            avail[r] = avail.back();
            avail.pop_back();
            ord[idx++] = op;
            int j = M.job_of[op];
            if (op + 1 < M.off[j + 1] && stamp[op + 1] == clock) avail.push_back(op + 1);
        }
    }

public:
    TopologicalWindowReshuffle(const JobShop& model, int w, double p) : M(model), win(w), wps(p) {
        stamp.assign(M.n_ops, 0);
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        build_order(s);
        int N = M.n_ops;
        if (N >= 2) {
            int w = std::min(N, std::max(2, win));
            int nw = std::max(1, (int)std::lround(strength * wps));
            std::vector<int> ord;
            for (int attempt = 0; attempt < 30; ++attempt) {
                ord = L;
                int ww = std::min(N, w + attempt / 5);
                for (int t = 0; t < nw; ++t) reshuffle(ord, rng.below(N - ww + 1), ww, rng);
                Sol out = decode(ord);
                if (out != s) return out;
            }
        }
        for (int t = 0; t < 50; ++t) { Sol r = M.random(rng); if (r != s) return r; }
        return decode(L);
    }
};

std::unique_ptr<hsf::Perturbation<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    return std::make_unique<TopologicalWindowReshuffle>(model, (int)params.get("window", 10),
                                                        params.get("windows_per_strength", 1.0));
}
