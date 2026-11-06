// COMPONENT: {"name": "neh_operation_sequence_insertion", "slot": "constructor", "params": {"max_pos": {"type": "int", "range": [4, 64]}, "order_noise": {"type": "float", "range": [0.0, 0.5]}}}
class NehOpSeqInsertion : public hsf::Constructor<Model> {
public:
    NehOpSeqInsertion(const Model& m, int maxPos, double noise) : M(m), maxPos(maxPos), noise(noise) {}

    Sol build(Rng& rng) override {
        const int J = M.n_jobs, NM = M.n_machines;
        cnt.assign(J, 0); jr.assign(J, 0); mr.assign(NM, 0);
        std::vector<std::pair<double, int>> order;
        order.reserve(J);
        for (int j = 0; j < J; ++j) {
            double s = 0;
            for (int k = 0; k < M.job_len[j]; ++k) s += M.op_proc[M.job_off[j] + k];
            double key = s * (1.0 + noise * (2.0 * rng.uniform() - 1.0));
            order.push_back({-key, j});
        }
        std::sort(order.begin(), order.end());
        seq.clear();
        seq.reserve(M.n_ops);
        std::vector<int> positions;
        for (auto& pr : order) {
            int j = pr.second;
            int lastPos = -1;
            for (int k = 0; k < M.job_len[j]; ++k) {
                int len = (int)seq.size();
                int avail = len - lastPos;  // positions lastPos+1 .. len
                positions.clear();
                if (avail <= maxPos) {
                    for (int p = lastPos + 1; p <= len; ++p) positions.push_back(p);
                } else {
                    int slots = maxPos - 1;
                    for (int t = 0; t < slots; ++t) {
                        int p = lastPos + 1 + (int)((t + rng.uniform()) * avail / slots);
                        if (p > len) p = len;
                        if (positions.empty() || positions.back() != p) positions.push_back(p);
                    }
                    if (positions.back() != len) positions.push_back(len);
                }
                long long bestMk = std::numeric_limits<long long>::max();
                int bestP = len, ties = 0;
                for (int p : positions) {
                    long long mk = decode(p, j);
                    if (mk < bestMk) { bestMk = mk; bestP = p; ties = 1; }
                    else if (mk == bestMk) { ++ties; if (rng.below(ties) == 0) bestP = p; }
                }
                seq.insert(seq.begin() + bestP, j);
                lastPos = bestP;
            }
        }
        Sol sol(NM);
        for (int m = 0; m < NM; ++m) sol[m].reserve(M.mach_jobs[m].size());
        std::fill(cnt.begin(), cnt.end(), 0);
        for (int j : seq) {
            int op = M.job_off[j] + cnt[j]++;
            sol[M.op_mach[op]].push_back(j);
        }
        return sol;
    }

private:
    long long decode(int insPos, int insJob) {
        std::fill(cnt.begin(), cnt.end(), 0);
        std::fill(jr.begin(), jr.end(), 0);
        std::fill(mr.begin(), mr.end(), 0);
        long long mk = 0;
        const int len = (int)seq.size();
        for (int i = 0; i <= len; ++i) {
            if (i == insPos) mk = std::max(mk, step(insJob));
            if (i < len) mk = std::max(mk, step(seq[i]));
        }
        return mk;
    }
    inline long long step(int j) {
        int op = M.job_off[j] + cnt[j]++;
        int m = M.op_mach[op];
        long long fin = std::max(jr[j], mr[m]) + M.op_proc[op];
        jr[j] = fin; mr[m] = fin;
        return fin;
    }

    const Model& M;
    int maxPos;
    double noise;
    std::vector<int> seq, cnt;
    std::vector<long long> jr, mr;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    int maxPos = std::max(4, std::min(64, (int)params.get("max_pos", 16)));
    double noise = std::min(0.5, std::max(0.0, params.get("order_noise", 0.1)));
    return std::make_unique<NehOpSeqInsertion>(model, maxPos, noise);
}
