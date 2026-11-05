// COMPONENT: {"name": "time_window_cross_machine_destruction", "slot": "destruction", "params": {"center_critical_prob": {"type": "float", "range": [0.0, 1.0]}, "jitter": {"type": "float", "range": [0.0, 3.0]}}}
class TimeWindowDestruction : public hsf::Destruction<Model> {
public:
    using Sol = Model::Solution;
    TimeWindowDestruction(const Model& md, double pc, double jitter)
        : md_(md), pc_(pc), jitter_(jitter) {
        n_ = md.n; m_ = md.m; T_ = md.total_ops;
        msz_.assign(m_, 0); off_.assign(m_, 0);
        pos_.assign((size_t)m_ * n_, -1);
        long long acc = 0;
        for (int i = 0; i < m_; ++i) {
            const auto& js = md.machine_jobs[i];
            msz_[i] = (int)js.size();
            off_[i] = acc;
            for (int a = 0; a < msz_[i]; ++a) pos_[(size_t)i * n_ + js[a]] = a;
            acc += (long long)msz_[i] * (msz_[i] - 1);
        }
        total_ = acc;
        mark_.assign((size_t)std::max<long long>(total_, 1), 0);
        opJob_.assign(T_, 0); opMach_.assign(T_, 0);
        int id = 0;
        double sp = 0;
        for (int j = 0; j < n_; ++j)
            for (auto& pr : md.routes[j]) {
                if (id < T_) { opJob_[id] = j; opMach_[id] = pr.first; }
                sp += pr.second; ++id;
            }
        avgP_ = T_ > 0 ? std::max(1.0, sp / T_) : 1.0;
        seq_.assign(m_, {}); added_.assign(m_, {});
        mp_.assign(T_, -1); ms_.assign(T_, -1); indeg_.assign(T_, 0); q_.assign(T_, 0);
        om_.assign(T_, 0); done_.assign(T_, 0);
        st_.assign(T_, 0); tail_.assign(T_, 0);
    }

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        out_.clear();
        if (total_ <= 0) return out_;
        ++mstamp_;
        long long target = std::llround(ratio * (double)total_);
        target = std::max(1LL, std::min(target, total_));
        schedule(s);
        double center;
        crit_.clear();
        if (rng.uniform() < pc_) {
            for (int o = 0; o < T_; ++o)
                if (done_[o] && st_[o] + tail_[o] == mk_ && opMach_[o] < m_) crit_.push_back(o);
        }
        if (!crit_.empty()) {
            int o = crit_[rng.below((int)crit_.size())];
            center = (double)st_[o] + 0.5 * md_.op_proc[o];
        } else {
            center = rng.uniform() * (double)std::max<long long>(1, mk_);
        }
        cand_.clear();
        for (int o = 0; o < T_; ++o) {
            int i = opMach_[o];
            if (i >= m_ || msz_[i] < 2) continue;
            double s0 = (double)st_[o], e0 = s0 + md_.op_proc[o];
            double dist = std::max(0.0, std::max(s0 - center, center - e0));
            cand_.push_back({dist + jitter_ * avgP_ * rng.uniform(), o});
        }
        std::sort(cand_.begin(), cand_.end());
        for (int i = 0; i < m_; ++i) added_[i].clear();
        for (auto& c : cand_) {
            int o = c.second, i = opMach_[o], j = opJob_[o];
            for (int jj : added_[i]) freePair(i, j, jj);
            added_[i].push_back(j);
            if ((long long)out_.size() >= target) break;
        }
        return out_;
    }

private:
    const Model& md_;
    double pc_, jitter_, avgP_;
    int n_, m_, T_;
    long long total_;
    std::vector<int> msz_, pos_;
    std::vector<long long> off_;
    std::vector<int> mark_; int mstamp_ = 0;
    std::vector<int> out_, crit_;
    std::vector<int> opJob_, opMach_;
    std::vector<std::vector<int>> seq_, added_;
    std::vector<int> mp_, ms_, indeg_, q_, om_, done_;
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
            for (int p = 1; p < (int)seq_[i].size(); ++p) {
                int op = seq_[i][p], pr = seq_[i][p - 1];
                mp_[op] = pr; ms_[pr] = op;
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
    double pc = params.get("center_critical_prob", 0.5);
    double jit = params.get("jitter", 0.5);
    return std::make_unique<TimeWindowDestruction>(model, pc, jit);
}
