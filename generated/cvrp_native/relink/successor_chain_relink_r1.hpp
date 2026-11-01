// COMPONENT: {"name": "successor_chain_relink", "slot": "relink", "params": {"link_weight": {"type": "float", "range": [0.2, 5.0]}, "merge_prob": {"type": "float", "range": [0.0, 1.0]}}}
class SuccessorChainRelink : public hsf::Relink<CVRP> {
public:
    using Sol = CVRP::Solution;
    SuccessorChainRelink(const CVRP& m, double lw, double mp) : m_(m), lw_(lw), mp_(mp) {}

    int distance(const Sol& a, const Sol& b) override {
        build(a, sa_, false);
        build(b, sb_, false);
        int d = 0;
        for (int c = 1; c <= m_.n; ++c) if (sa_[c] != sb_[c]) ++d;
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        int n = m_.n;
        build(guide, sb_, false);
        build(cur, sa_, true);
        cand_.clear(); w_.clear();
        int d = 0; double tot = 0.0;
        for (int c = 1; c <= n; ++c) {
            if (sa_[c] == sb_[c]) continue;
            ++d;
            if (rt_[c] < 0) continue;
            int t = sb_[c];
            bool good = false;
            if (t == 0) good = true;
            else if (t >= 1 && t <= n && rt_[t] >= 0) good = (rt_[t] != rt_[c]) || (ps_[t] > ps_[c]);
            if (good) {
                double ww = (t == 0) ? 1.0 : lw_;
                cand_.push_back(c); w_.push_back(ww); tot += ww;
            }
        }
        if (d == 0 || cand_.empty()) return guide;
        double u = rng.uniform() * tot;
        int k = 0;
        while (k + 1 < (int)cand_.size() && u >= w_[k]) { u -= w_[k]; ++k; }
        int c = cand_[k], t = sb_[c];
        int r1 = rt_[c], i = ps_[c];
        const auto& R1 = cur[r1];
        int L1 = (int)R1.size();
        Sol out;
        out.reserve(cur.size() + 2);
        if (t == 0) {
            for (int r = 0; r < (int)cur.size(); ++r) if (r != r1 && !cur[r].empty()) out.push_back(cur[r]);
            out.emplace_back(R1.begin(), R1.begin() + i + 1);
            if (i + 1 < L1) out.emplace_back(R1.begin() + i + 1, R1.end());
        } else {
            int r2 = rt_[t], j = ps_[t];
            for (int r = 0; r < (int)cur.size(); ++r)
                if (r != r1 && r != r2 && !cur[r].empty()) out.push_back(cur[r]);
            if (r2 == r1) {
                std::vector<int> h(R1.begin(), R1.begin() + i + 1);
                h.insert(h.end(), R1.begin() + j, R1.end());
                out.push_back(std::move(h));
                if (j > i + 1) out.emplace_back(R1.begin() + i + 1, R1.begin() + j);
            } else {
                const auto& R2 = cur[r2];
                std::vector<int> h(R1.begin(), R1.begin() + i + 1);
                h.insert(h.end(), R2.begin() + j, R2.end());
                out.push_back(std::move(h));
                std::vector<int> y(R2.begin(), R2.begin() + j);
                if (rng.uniform() < mp_) {
                    y.insert(y.end(), R1.begin() + i + 1, R1.end());
                    if (!y.empty()) out.push_back(std::move(y));
                } else {
                    if (!y.empty()) out.push_back(std::move(y));
                    if (i + 1 < L1) out.emplace_back(R1.begin() + i + 1, R1.end());
                }
            }
        }
        int dn = distance(out, guide);
        if (dn == 0 || dn >= d) return guide;
        return out;
    }

private:
    void build(const Sol& s, std::vector<int>& su, bool pos) {
        int n = m_.n;
        su.assign(n + 1, -1);
        if (pos) { rt_.assign(n + 1, -1); ps_.assign(n + 1, -1); }
        for (int r = 0; r < (int)s.size(); ++r) {
            const auto& R = s[r];
            int L = (int)R.size();
            for (int i = 0; i < L; ++i) {
                int c = R[i];
                if (c < 1 || c > n) continue;
                int nx = (i + 1 < L) ? ((R[i + 1] >= 1 && R[i + 1] <= n) ? R[i + 1] : -2) : 0;
                su[c] = nx;
                if (pos) { rt_[c] = r; ps_[c] = i; }
            }
        }
    }
    const CVRP& m_;
    double lw_, mp_;
    std::vector<int> sa_, sb_, rt_, ps_, cand_;
    std::vector<double> w_;
};

std::unique_ptr<hsf::Relink<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<SuccessorChainRelink>(model, params.get("link_weight", 1.0), params.get("merge_prob", 0.3));
}
