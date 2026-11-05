// COMPONENT: {"name": "critical_path_window_destruction", "slot": "destruction", "params": {"window": {"type": "int", "range": [1, 8]}, "noise": {"type": "float", "range": [0.0, 0.6]}}}
class CriticalPathWindowDestruction : public hsf::Destruction<Model> {
public:
    using Sol = Model::Solution;
    CriticalPathWindowDestruction(const Model& md, int window, double noise)
        : md_(md), w_(std::max(1, window)), noise_(noise) {
        n_ = md.n; m_ = md.m; T_ = md.total_ops;
        msz_.assign(m_, 0); off_.assign(m_, 0);
        pos_.assign((size_t)m_ * n_, -1);
        long long acc = 0; maxsz_ = 0;
        for (int i = 0; i < m_; ++i) {
            const auto& js = md.machine_jobs[i];
            msz_[i] = (int)js.size();
            maxsz_ = std::max(maxsz_, msz_[i]);
            off_[i] = acc;
            for (int a = 0; a < msz_[i]; ++a) pos_[(size_t)i * n_ + js[a]] = a;
            acc += (long long)msz_[i] * (msz_[i] - 1);
        }
        total_ = acc;
        mark_.assign((size_t)std::max<long long>(total_, 1), 0);
        opJob_.assign(T_, 0); opMach_.assign(T_, 0);
        int id = 0;
        for (int j = 0; j < n_; ++j)
            for (auto& pr : md.routes[j]) { if (id < T_) { opJob_[id] = j; opMach_[id] = pr.first; } ++id; }
        seq_.assign(m_, {});
        mp_.assign(T_, -1); ms_.assign(T_, -1); indeg_.assign(T_, 0); q_.assign(T_, 0);
        pis_.assign(T_, -1); om_.assign(T_, 0); done_.assign(T_, 0);
        st_.assign(T_, 0); tail_.assign(T_, 0);
    }

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        out_.clear();
        if (total_ <= 0) return out_;
        ++mstamp_;
        long long target = std::llround(ratio * (double)total_);
        target = std::max(1LL, std::min(target, total_));
        target_ = target;
        schedule(s);
        cand_.clear();
        double mk = (double)std::max<long long>(1, mk_);
        for (int o = 0; o < T_; ++o) {
            int i = opMach_[o];
            if (i >= m_ || msz_[i] < 2 || pis_[o] < 0) continue;
            double crit = done_[o] ? (double)(st_[o] + tail_[o]) / mk : 1.5;
            cand_.push_back({crit * (1.0 - noise_ * rng.uniform()), o});
        }
        std::sort(cand_.begin(), cand_.end(),
                  [](const std::pair<double,int>& a, const std::pair<double,int>& b) { return a.first > b.first; });
        for (int ww = w_; ; ww *= 2) {
            for (auto& c : cand_) {
                int o = c.second, i = opMach_[o], p = pis_[o];
                const auto& sq = seq_[i];
                int L = (int)sq.size();
                for (int d = 1; d <= ww; ++d) {
                    if (p - d >= 0) freePair(i, opJob_[o], opJob_[sq[p - d]]);
                    if (p + d < L) freePair(i, opJob_[o], opJob_[sq[p + d]]);
                }
                if ((long long)out_.size() >= target_) return out_;
            }
            if (ww >= maxsz_) break;
        }
        return out_;
    }

private:
    const Model& md_;
    int w_; double noise_;
    int n_, m_, T_, maxsz_;
    long long total_, target_ = 0;
    std::vector<int> msz_, pos_;
    std::vector<long long> off_;
    std::vector<int> mark_; int mstamp_ = 0;
    std::vector<int> out_;
    std::vector<int> opJob_, opMach_;
    std::vector<std::vector<int>> seq_;
    std::vector<int> mp_, ms_, indeg_, q_, pis_, om_, done_;
    int ostamp_ = 0;
    std::vector<long long> st_, tail_;
    long long mk_ = 0;
    std::vector<std::pair<double,int>> cand_;

    inline void freeVar(long long idx) {
        if (mark_[idx] != mstamp_) { mark_[idx] = mstamp_; out_.push_back((int)idx); }
    }
    inline void freePair(int i, int ja, int jb) {
        int a = pos_[(size_t)i * n_ + ja], b = pos_[(size_t)i * n_ + jb];
        if (a < 0 || b < 0 || a == b) return;
        long long base = off_[i]; int sz = msz_[i];
        freeVar(base + (long long)a * (sz - 1) + (b < a ? b : b - 1));
        freeVar(base + (long long)b * (sz - 1) + (a < b ? a : a - 1));
    }
    void schedule(const Sol& s) {
        ++ostamp_;
        int lim = std::min((int)s.size(), m_);
        for (int i = 0; i < m_; ++i) seq_[i].clear();
        for (int i = 0; i < lim; ++i)
            for (int j : s[i]) {
                if ((unsigned)j >= (unsigned)n_) continue;
                int op = md_.opflat[(size_t)i * n_ + j];
                if (op < 0 || om_[op] == ostamp_) continue;
                om_[op] = ostamp_; seq_[i].push_back(op);
            }
        for (int i = 0; i < m_; ++i)
            for (int j : md_.machine_jobs[i]) {
                int op = md_.opflat[(size_t)i * n_ + j];
                if (op >= 0 && om_[op] != ostamp_) { om_[op] = ostamp_; seq_[i].push_back(op); }
            }
        std::fill(mp_.begin(), mp_.end(), -1);
        std::fill(ms_.begin(), ms_.end(), -1);
        for (int i = 0; i < m_; ++i)
            for (int p = 0; p < (int)seq_[i].size(); ++p) {
                int op = seq_[i][p]; pis_[op] = p;
                if (p > 0) { mp_[op] = seq_[i][p - 1]; ms_[seq_[i][p - 1]] = op; }
            }
        int qh = 0, qt = 0;
        for (int o = 0; o < T_; ++o) {
            indeg_[o] = (md_.op_k[o] > 0 ? 1 : 0) + (mp_[o] >= 0 ? 1 : 0);
            st_[o] = 0; tail_[o] = 0; done_[o] = 0;
            if (indeg_[o] == 0) q_[qt++] = o;
        }
        long long mk = 0;
        while (qh < qt) {
            int o = q_[qh++]; done_[o] = 1;
            long long e = st_[o] + md_.op_proc[o];
            if (e > mk) mk = e;
            int a = md_.op_next[o];
            if (a >= 0) { if (st_[a] < e) st_[a] = e; if (--indeg_[a] == 0) q_[qt++] = a; }
            int b = ms_[o];
            if (b >= 0) { if (st_[b] < e) st_[b] = e; if (--indeg_[b] == 0) q_[qt++] = b; }
        }
        mk_ = mk;
        for (int k = qt - 1; k >= 0; --k) {
            int o = q_[k]; long long t = 0;
            int a = md_.op_next[o]; if (a >= 0 && done_[a]) t = std::max(t, tail_[a]);
            int b = ms_[o]; if (b >= 0 && done_[b]) t = std::max(t, tail_[b]);
            tail_[o] = md_.op_proc[o] + t;
        }
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("window", 3);
    double noise = params.get("noise", 0.2);
    return std::make_unique<CriticalPathWindowDestruction>(model, w, noise);
}
