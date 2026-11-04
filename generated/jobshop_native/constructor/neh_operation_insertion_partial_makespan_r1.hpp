// COMPONENT: {"name": "neh_operation_insertion_partial_makespan", "slot": "constructor", "params": {"noise": {"type": "float", "range": [0.0, 1.0]}, "max_positions": {"type": "int", "range": [4, 200]}}}
class NehOperationInsertion : public hsf::Constructor<Model> {
public:
    NehOperationInsertion(const Model& md, double noise, int maxpos)
        : md_(md), noise_(noise), maxpos_(maxpos) {
        int T = md_.total_ops;
        opj_.assign(T, 0); opm_.assign(T, 0);
        tot_.assign(md_.n, 0);
        int id = 0;
        for (int j = 0; j < md_.n; ++j)
            for (auto& o : md_.routes[j]) { opj_[id] = j; opm_[id] = o.first; tot_[j] += o.second; ++id; }
        mp_.assign(T, -1); msx_.assign(T, -1); indeg_.assign(T, 0); q_.assign(T, 0);
        st_.assign(T, 0); active_.assign(T, 0);
    }
    Model::Solution build(Rng& rng) override {
        int n = md_.n, T = md_.total_ops;
        std::fill(active_.begin(), active_.end(), 0);
        act_.clear();
        seq_.assign(md_.m, {});
        std::vector<std::pair<double,int>> order(n);
        for (int j = 0; j < n; ++j)
            order[j] = {-(double)tot_[j] * (1.0 - noise_ * rng.uniform()), j};
        std::sort(order.begin(), order.end());
        std::vector<int> firstOp(n + 1, 0);
        for (int j = 0; j < n; ++j) firstOp[j + 1] = firstOp[j] + (int)md_.routes[j].size();
        (void)T;
        for (auto& pr : order) {
            int j = pr.second;
            for (int o = firstOp[j]; o < firstOp[j + 1]; ++o) {
                active_[o] = 1; act_.push_back(o);
                int mach = opm_[o];
                if (mach >= md_.m) continue;
                auto& sq = seq_[mach];
                int L = (int)sq.size();
                cpos_.clear();
                if (L + 1 <= maxpos_) { for (int p = 0; p <= L; ++p) cpos_.push_back(p); }
                else {
                    for (int t = 0; t < maxpos_ - 1; ++t) cpos_.push_back(rng.below(L + 1));
                    cpos_.push_back(L);
                    std::sort(cpos_.begin(), cpos_.end());
                    cpos_.erase(std::unique(cpos_.begin(), cpos_.end()), cpos_.end());
                }
                int bestp = L;
                long long bmk = LLONG_MAX, bsec = LLONG_MAX;
                for (int p : cpos_) {
                    sq.insert(sq.begin() + p, o);
                    long long mk = evalPartial();
                    if (mk >= 0) {
                        long long sec = st_[o] + md_.op_proc[o];
                        if (mk < bmk || (mk == bmk && sec < bsec)) { bmk = mk; bsec = sec; bestp = p; }
                    }
                    sq.erase(sq.begin() + p);
                }
                sq.insert(sq.begin() + bestp, o);
            }
        }
        Model::Solution s(md_.m);
        for (int i = 0; i < md_.m; ++i) {
            s[i].reserve(seq_[i].size());
            for (int o : seq_[i]) s[i].push_back(opj_[o]);
        }
        return s;
    }
private:
    long long evalPartial() {
        for (int o : act_) { mp_[o] = -1; msx_[o] = -1; }
        for (auto& sq : seq_)
            for (size_t t = 1; t < sq.size(); ++t) { msx_[sq[t - 1]] = sq[t]; mp_[sq[t]] = sq[t - 1]; }
        int qh = 0, qt = 0;
        for (int o : act_) {
            indeg_[o] = ((md_.op_k[o] > 0 && active_[o - 1]) ? 1 : 0) + (mp_[o] >= 0 ? 1 : 0);
            st_[o] = 0;
            if (indeg_[o] == 0) q_[qt++] = o;
        }
        long long mk = 0;
        while (qh < qt) {
            int o = q_[qh++];
            long long e = st_[o] + md_.op_proc[o];
            if (e > mk) mk = e;
            int a = md_.op_next[o];
            if (a >= 0 && active_[a]) { if (st_[a] < e) st_[a] = e; if (--indeg_[a] == 0) q_[qt++] = a; }
            int b = msx_[o];
            if (b >= 0) { if (st_[b] < e) st_[b] = e; if (--indeg_[b] == 0) q_[qt++] = b; }
        }
        if (qt < (int)act_.size()) return -1;
        return mk;
    }
    const Model& md_;
    double noise_;
    int maxpos_;
    std::vector<int> opj_, opm_, mp_, msx_, indeg_, q_, act_, cpos_;
    std::vector<char> active_;
    std::vector<long long> st_, tot_;
    std::vector<std::vector<int>> seq_;
};

std::unique_ptr<hsf::Constructor<Model>> make_component(const Model& model, const hsf::Config& params) {
    double noise = std::min(1.0, std::max(0.0, params.get("noise", 0.3)));
    int maxpos = std::max(2, (int)params.get("max_positions", 40));
    return std::make_unique<NehOperationInsertion>(model, noise, maxpos);
}
