// COMPONENT: {"name": "route_transplant_relink", "slot": "relink", "params": {"greedy_prob": {"type": "float", "range": [0.0, 1.0]}}}
class RouteTransplantRelink : public hsf::Relink<CVRP> {
public:
    using Sol = CVRP::Solution;
    RouteTransplantRelink(const CVRP& m, double gp) : m_(m), gp_(gp) {}

    int distance(const Sol& a, const Sol& b) override { return match(a, b, nullptr); }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        int n = m_.n;
        miss_.clear();
        int d = match(cur, guide, &miss_);
        if (d == 0 || miss_.empty()) return guide;
        int g;
        if (miss_.size() > 1 && rng.uniform() < gp_) {
            rt_.assign(n + 1, -1);
            for (int r = 0; r < (int)cur.size(); ++r)
                for (int c : cur[r]) if (c >= 1 && c <= n) rt_[c] = r;
            if (rs_.size() < cur.size()) rs_.resize(cur.size(), 0);
            int best = std::numeric_limits<int>::max(), ties = 0;
            g = miss_[0];
            for (int gi : miss_) {
                ++rstamp_;
                int touched = 0;
                for (int c : guide[gi]) {
                    if (c < 1 || c > n || rt_[c] < 0) continue;
                    int r = rt_[c];
                    if (rs_[r] != rstamp_) { rs_[r] = rstamp_; ++touched; }
                }
                if (touched < best) { best = touched; g = gi; ties = 1; }
                else if (touched == best) { ++ties; if (rng.below(ties) == 0) g = gi; }
            }
        } else {
            g = miss_[rng.below((int)miss_.size())];
        }
        if (mk_.size() < (size_t)(n + 1)) mk_.assign(n + 1, 0);
        ++mstamp_;
        for (int c : guide[g]) if (c >= 1 && c <= n) mk_[c] = mstamp_;
        Sol out;
        out.reserve(cur.size() + 1);
        for (const auto& R : cur) {
            bool hit = false;
            for (int c : R) if (c >= 1 && c <= n && mk_[c] == mstamp_) { hit = true; break; }
            if (!hit) { if (!R.empty()) out.push_back(R); continue; }
            std::vector<int> f;
            f.reserve(R.size());
            for (int c : R) if (!(c >= 1 && c <= n && mk_[c] == mstamp_)) f.push_back(c);
            if (!f.empty()) out.push_back(std::move(f));
        }
        out.push_back(guide[g]);
        int dn = match(out, guide, nullptr);
        if (dn == 0 || dn >= d) return guide;
        return out;
    }

private:
    int match(const Sol& a, const Sol& b, std::vector<int>* missing) {
        int n = m_.n;
        fa_.assign(n + 1, -1);
        int na = 0;
        for (int k = 0; k < (int)a.size(); ++k) {
            if (a[k].empty()) continue;
            ++na;
            int f = a[k][0];
            if (f >= 1 && f <= n && fa_[f] < 0) fa_[f] = k;
        }
        int nb = 0, common = 0;
        for (int gi = 0; gi < (int)b.size(); ++gi) {
            if (b[gi].empty()) continue;
            ++nb;
            int f = b[gi][0];
            bool ok = false;
            if (f >= 1 && f <= n && fa_[f] >= 0 && a[fa_[f]] == b[gi]) { ok = true; fa_[f] = -1; }
            if (ok) ++common;
            else if (missing) missing->push_back(gi);
        }
        return na + nb - 2 * common;
    }
    const CVRP& m_;
    double gp_;
    std::vector<int> fa_, miss_, rt_, rs_, mk_;
    int rstamp_ = 0, mstamp_ = 0;
};

std::unique_ptr<hsf::Relink<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    return std::make_unique<RouteTransplantRelink>(model, params.get("greedy_prob", 0.3));
}
