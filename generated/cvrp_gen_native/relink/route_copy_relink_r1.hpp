// COMPONENT: {"name": "route_copy_relink", "slot": "relink", "params": {"reinsert": {"type": "cat", "values": ["cheapest", "random_route"]}}}
class RouteCopyRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    RouteCopyRelink(const Model& m, bool cheapest)
        : m_(m), cheapest_(cheapest), mark_(m.n + 1, 0) {}

    int distance(const Sol& a, const Sol& b) override {
        size_t R = std::max(a.size(), b.size());
        int d = 0;
        for (size_t i = 0; i < R; ++i)
            if (i >= a.size() || i >= b.size() || a[i] != b[i]) ++d;
        return d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        const size_t Rc = cur.size(), Rg = guide.size();
        const size_t Rm = std::min(Rc, Rg);
        mis_.assign(Rc, 0);
        cand_.clear();
        for (size_t i = 0; i < Rc; ++i) {
            bool mm = (i >= Rg) || cur[i] != guide[i];
            mis_[i] = mm ? 1 : 0;
            if (i < Rm && mm) cand_.push_back((int)i);
        }
        if (Rc < Rg) cand_.push_back((int)Rc);
        if (Rc > Rg) cand_.push_back(-1);
        if (cand_.empty()) return guide;
        int k = cand_[rng.below((int)cand_.size())];
        Sol s = cur;
        left_.clear();
        if (k >= 0) {
            if (++stamp_ == std::numeric_limits<int>::max()) {
                std::fill(mark_.begin(), mark_.end(), 0);
                stamp_ = 1;
            }
            for (int c : guide[k]) if (valid(c)) mark_[c] = stamp_;
            if ((size_t)k < Rc) {
                for (int c : s[k]) if (!(valid(c) && mark_[c] == stamp_)) left_.push_back(c);
                s[k] = guide[k];
                mis_[k] = 0;
            } else {
                s.push_back(guide[k]);
                mis_.push_back(0);
            }
            for (size_t j = 0; j < Rc; ++j) {
                if ((int)j == k || !mis_[j]) continue;
                auto& r = s[j];
                r.erase(std::remove_if(r.begin(), r.end(),
                        [&](int c) { return valid(c) && mark_[c] == stamp_; }), r.end());
            }
        } else {
            left_ = s.back();
            s.pop_back();
            mis_.pop_back();
        }
        if (left_.empty()) return s;
        targets_.clear();
        for (size_t j = 0; j < s.size(); ++j)
            if (mis_[j]) targets_.push_back((int)j);
        if (targets_.empty()) {
            if (s.size() < Rg) s.push_back(left_);
            return s;
        }
        std::shuffle(left_.begin(), left_.end(), rng.g);
        loads_.assign(s.size(), 0.0);
        for (int j : targets_)
            for (int c : s[j]) if (valid(c)) loads_[j] += m_.demand[c];
        for (int c : left_) {
            if (!valid(c)) { s[targets_[rng.below((int)targets_.size())]].push_back(c); continue; }
            double dem = m_.demand[c];
            int bestR = -1, bestP = 0;
            double best = std::numeric_limits<double>::infinity();
            auto evalRoute = [&](int j) {
                const auto& r = s[j];
                int L = (int)r.size();
                double over = std::max(0.0, loads_[j] + dem - m_.capacity) - std::max(0.0, loads_[j] - m_.capacity);
                double pen = over * m_.penalty;
                for (int p = 0; p <= L; ++p) {
                    int pr = p > 0 ? r[p - 1] : 0;
                    int nx = p < L ? r[p] : 0;
                    double dl = D(pr, c) + D(c, nx) - D(pr, nx) + pen;
                    if (dl < best) { best = dl; bestR = j; bestP = p; }
                }
            };
            if (cheapest_) for (int j : targets_) evalRoute(j);
            else evalRoute(targets_[rng.below((int)targets_.size())]);
            s[bestR].insert(s[bestR].begin() + bestP, c);
            loads_[bestR] += dem;
        }
        return s;
    }

private:
    const Model& m_;
    bool cheapest_;
    std::vector<int> mark_;
    int stamp_ = 0;
    std::vector<char> mis_;
    std::vector<int> cand_, left_, targets_;
    std::vector<double> loads_;
    bool valid(int c) const { return c >= 1 && c <= m_.n; }
    double D(int i, int j) const {
        if (i < 0 || i > m_.n || j < 0 || j > m_.n) return 0.0;
        return m_.dist(i, j);
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool cheapest = params.text("reinsert", "cheapest") != "random_route";
    return std::make_unique<RouteCopyRelink>(model, cheapest);
}
