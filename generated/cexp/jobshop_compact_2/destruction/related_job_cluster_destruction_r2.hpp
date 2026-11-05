// COMPONENT: {"name": "related_job_cluster_destruction", "slot": "destruction", "params": {"adj_window": {"type": "int", "range": [1, 5]}, "greed": {"type": "float", "range": [1.0, 8.0]}}}
class RelatedJobClusterDestruction : public hsf::Destruction<Model> {
public:
    using Sol = Model::Solution;
    RelatedJobClusterDestruction(const Model& md, int w, double greed)
        : md_(md), w_(std::max(1, w)), greed_(greed) {
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
        opJob_.assign(T_, 0);
        int id = 0;
        for (int j = 0; j < n_; ++j)
            for (auto& pr : md.routes[j]) { (void)pr; if (id < T_) opJob_[id] = j; ++id; }
        for (int j = 0; j < n_; ++j) {
            bool ok = false;
            for (auto& pr : md.routes[j]) if (pr.first < m_ && msz_[pr.first] >= 2) ok = true;
            if (ok) elig_.push_back(j);
        }
        seq_.assign(m_, {});
        pis_.assign(T_, -1); om_.assign(T_, 0);
        score_.assign(n_, 0.0); chosen_.assign(n_, 0);
    }

    std::vector<int> destroy(const Sol& s, double ratio, Rng& rng) override {
        out_.clear();
        if (total_ <= 0 || elig_.empty()) return out_;
        ++mstamp_;
        long long target = std::llround(ratio * (double)total_);
        target = std::max(1LL, std::min(target, total_));
        cleanSeq(s);
        ++cstamp_;
        std::fill(score_.begin(), score_.end(), 0.0);
        chosenList_.clear();
        int j = elig_[rng.below((int)elig_.size())];
        while (true) {
            for (auto& pr : md_.routes[j]) {
                int i = pr.first;
                if (i >= m_) continue;
                freeJobOnMachine(i, j);
            }
            chosenList_.push_back(j);
            chosen_[j] = cstamp_;
            if ((long long)out_.size() >= target) break;
            for (auto& pr : md_.routes[j]) {
                int i = pr.first;
                if (i >= m_) continue;
                int op = md_.opflat[(size_t)i * n_ + j];
                if (op < 0) continue;
                int p = pis_[op];
                const auto& sq = seq_[i];
                int L = (int)sq.size();
                for (int d = 1; d <= w_; ++d) {
                    double wt = (double)(w_ - d + 1);
                    if (p - d >= 0) score_[opJob_[sq[p - d]]] += wt;
                    if (p + d < L) score_[opJob_[sq[p + d]]] += wt;
                }
            }
            cand_.clear();
            for (int c : elig_)
                if (chosen_[c] != cstamp_ && score_[c] > 0) cand_.push_back({score_[c] + 0.5 * rng.uniform(), c});
            if (cand_.empty()) {
                rest_.clear();
                for (int c : elig_) if (chosen_[c] != cstamp_) rest_.push_back(c);
                if (rest_.empty()) break;
                j = rest_[rng.below((int)rest_.size())];
                continue;
            }
            std::sort(cand_.begin(), cand_.end(),
                      [](const std::pair<double,int>& a, const std::pair<double,int>& b) { return a.first > b.first; });
            int idx = (int)(std::pow(rng.uniform(), greed_) * (double)cand_.size());
            if (idx >= (int)cand_.size()) idx = (int)cand_.size() - 1;
            j = cand_[idx].second;
        }
        return out_;
    }

private:
    const Model& md_;
    int w_; double greed_;
    int n_, m_, T_;
    long long total_;
    std::vector<int> msz_, pos_;
    std::vector<long long> off_;
    std::vector<int> mark_; int mstamp_ = 0;
    std::vector<int> out_, opJob_, elig_, chosenList_, rest_;
    std::vector<std::vector<int>> seq_;
    std::vector<int> pis_, om_, chosen_;
    int ostamp_ = 0, cstamp_ = 0;
    std::vector<double> score_;
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
    // libera TODAS las variables de orden del job ja en la máquina i:
    // su fila completa (contigua) y su columna (ja respecto a cada otro job)
    inline void freeJobOnMachine(int i, int ja) {
        int a = pos_[(size_t)i * n_ + ja];
        int sz = msz_[i];
        if (a < 0 || sz < 2) return;
        long long base = off_[i];
        long long row = base + (long long)a * (sz - 1);
        for (int k = 0; k < sz - 1; ++k) freeVar(row + k);
        for (int b = 0; b < sz; ++b) {
            if (b == a) continue;
            freeVar(base + (long long)b * (sz - 1) + (a < b ? a : a - 1));
        }
    }
    void cleanSeq(const Sol& s) {
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
        for (int i = 0; i < m_; ++i)
            for (int p = 0; p < (int)seq_[i].size(); ++p) pis_[seq_[i][p]] = p;
    }
};

std::unique_ptr<hsf::Destruction<Model>> make_component(const Model& model, const hsf::Config& params) {
    int w = (int)params.get("adj_window", 2);
    double g = params.get("greed", 3.0);
    return std::make_unique<RelatedJobClusterDestruction>(model, w, g);
}
