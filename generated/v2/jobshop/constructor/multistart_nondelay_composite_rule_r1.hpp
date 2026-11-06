// COMPONENT: {"name": "multistart_nondelay_composite_rule", "slot": "constructor", "params": {"restarts": {"type": "int", "range": [1, 30]}, "noise": {"type": "float", "range": [0.0, 0.5]}}}
class MultistartNonDelay : public hsf::Constructor<Model> {
public:
    MultistartNonDelay(const Model& m, int restarts, double noise) : M(m), restarts(restarts), noise(noise) {
        const int J = M.n_jobs;
        tot.assign(J, 0);
        pmax = 1; remmax = 1; lenmax = 1;
        for (int j = 0; j < J; ++j) {
            long long s = 0;
            for (int k = 0; k < M.job_len[j]; ++k) {
                int p = M.op_proc[M.job_off[j] + k];
                s += p;
                pmax = std::max(pmax, (long long)p);
            }
            tot[j] = s;
            remmax = std::max(remmax, s);
            lenmax = std::max(lenmax, M.job_len[j]);
        }
    }

    Sol build(Rng& rng) override {
        Sol best;
        long long bestMk = std::numeric_limits<long long>::max();
        Sol cur;
        for (int r = 0; r < restarts; ++r) {
            double w[4];
            for (int i = 0; i < 4; ++i) w[i] = rng.uniform();
            long long mk = run(rng, w, cur);
            if (mk < bestMk) { bestMk = mk; best = cur; }
        }
        return best;
    }

private:
    long long run(Rng& rng, const double* w, Sol& sol) {
        const int J = M.n_jobs, NM = M.n_machines;
        sol.assign(NM, std::vector<int>());
        for (int m = 0; m < NM; ++m) sol[m].reserve(M.mach_jobs[m].size());
        nxt.assign(J, 0); jr.assign(J, 0); mr.assign(NM, 0);
        rem = tot;
        active.clear();
        for (int j = 0; j < J; ++j) if (M.job_len[j] > 0) active.push_back(j);
        long long mk = 0;
        while (!active.empty()) {
            long long smin = std::numeric_limits<long long>::max();
            for (int j : active) {
                int op = M.job_off[j] + nxt[j];
                smin = std::min(smin, std::max(jr[j], mr[M.op_mach[op]]));
            }
            int ba = -1;
            double bs = -1e300;
            for (int a = 0; a < (int)active.size(); ++a) {
                int j = active[a];
                int op = M.job_off[j] + nxt[j];
                int m = M.op_mach[op];
                if (std::max(jr[j], mr[m]) != smin) continue;
                double sc = -w[0] * (double)M.op_proc[op] / pmax
                          + w[1] * (double)rem[j] / remmax
                          + w[2] * (double)(M.job_len[j] - nxt[j]) / lenmax
                          + w[3] * (double)M.op_proc[op] / pmax * 0.5
                          + noise * rng.uniform();
                if (sc > bs) { bs = sc; ba = a; }
            }
            int j = active[ba];
            int op = M.job_off[j] + nxt[j];
            int m = M.op_mach[op];
            long long fin = smin + M.op_proc[op];
            jr[j] = fin; mr[m] = fin;
            if (fin > mk) mk = fin;
            rem[j] -= M.op_proc[op];
            sol[m].push_back(j);
            if (++nxt[j] == M.job_len[j]) { active[ba] = active.back(); active.pop_back(); }
        }
        return mk;
    }

    const Model& M;
    int restarts;
    double noise;
    long long pmax, remmax;
    int lenmax;
    std::vector<long long> tot, rem, jr, mr;
    std::vector<int> nxt, active;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int restarts = std::max(1, std::min(30, (int)params.get("restarts", 8)));
    double noise = std::min(0.5, std::max(0.0, params.get("noise", 0.1)));
    return std::make_unique<MultistartNonDelay>(model, restarts, noise);
}
