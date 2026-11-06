// COMPONENT: {"name": "giffler_thompson_grasp", "slot": "constructor", "params": {"alpha": {"type": "float", "range": [0.0, 1.0]}, "rule": {"type": "cat", "values": ["mwkr", "spt", "mopnr", "lpt", "random"]}}}
class GifflerThompsonGrasp : public hsf::Constructor<Model> {
public:
    GifflerThompsonGrasp(const Model& m, double alpha, int rule) : M(m), alpha(alpha), rule(rule) {}

    Sol build(Rng& rng) override {
        const int J = M.n_jobs, NM = M.n_machines;
        Sol sol(NM);
        for (int m = 0; m < NM; ++m) sol[m].reserve(M.mach_jobs[m].size());
        nxt.assign(J, 0);
        jr.assign(J, 0);
        mr.assign(NM, 0);
        rem.assign(J, 0);
        active.clear();
        for (int j = 0; j < J; ++j) {
            long long s = 0;
            for (int k = 0; k < M.job_len[j]; ++k) s += M.op_proc[M.job_off[j] + k];
            rem[j] = s;
            if (M.job_len[j] > 0) active.push_back(j);
        }
        while (!active.empty()) {
            long long best = std::numeric_limits<long long>::max();
            int bm = -1;
            for (int j : active) {
                int op = M.job_off[j] + nxt[j];
                int m = M.op_mach[op];
                long long est = std::max(jr[j], mr[m]);
                long long ect = est + M.op_proc[op];
                if (ect < best) { best = ect; bm = m; }
            }
            cand.clear(); score.clear();
            for (int a = 0; a < (int)active.size(); ++a) {
                int j = active[a];
                int op = M.job_off[j] + nxt[j];
                int m = M.op_mach[op];
                if (m != bm) continue;
                long long est = std::max(jr[j], mr[m]);
                if (est >= best) continue;
                double sc;
                switch (rule) {
                    case 0: sc = (double)rem[j]; break;
                    case 1: sc = -(double)M.op_proc[op]; break;
                    case 2: sc = (double)(M.job_len[j] - nxt[j]); break;
                    case 3: sc = (double)M.op_proc[op]; break;
                    default: sc = rng.uniform(); break;
                }
                cand.push_back(a);
                score.push_back(sc);
            }
            double mx = -1e300, mn = 1e300;
            for (double s : score) { mx = std::max(mx, s); mn = std::min(mn, s); }
            double thr = mx - alpha * (mx - mn) - 1e-9;
            rcl.clear();
            for (int i = 0; i < (int)cand.size(); ++i) if (score[i] >= thr) rcl.push_back(cand[i]);
            int a = rcl[rng.below((int)rcl.size())];
            int j = active[a];
            int op = M.job_off[j] + nxt[j];
            int m = M.op_mach[op];
            long long fin = std::max(jr[j], mr[m]) + M.op_proc[op];
            jr[j] = fin; mr[m] = fin;
            rem[j] -= M.op_proc[op];
            sol[m].push_back(j);
            if (++nxt[j] == M.job_len[j]) { active[a] = active.back(); active.pop_back(); }
        }
        return sol;
    }

private:
    const Model& M;
    double alpha;
    int rule;
    std::vector<int> nxt, active, cand, rcl;
    std::vector<long long> jr, mr, rem;
    std::vector<double> score;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double alpha = std::min(1.0, std::max(0.0, params.get("alpha", 0.3)));
    std::string r = params.text("rule", "mwkr");
    int rule = 0;
    if (r == "spt") rule = 1; else if (r == "mopnr") rule = 2; else if (r == "lpt") rule = 3; else if (r == "random") rule = 4;
    return std::make_unique<GifflerThompsonGrasp>(model, alpha, rule);
}
