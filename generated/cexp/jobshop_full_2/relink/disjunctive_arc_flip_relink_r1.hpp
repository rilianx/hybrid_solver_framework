// COMPONENT: {"name": "disjunctive_arc_flip_relink", "slot": "relink", "params": {"machine_focus": {"type": "float", "range": [0.0, 1.0]}}}
class ArcFlipRelink : public hsf::Relink<Model> {
public:
    ArcFlipRelink(const Model& md, double focus) : md_(md), focus_(focus) {
        pos_.assign(std::max(1, md.n), 0);
    }
    int distance(const Sol& a, const Sol& b) override {
        long long d = 0;
        size_t M = std::min(a.size(), b.size());
        for (size_t i = 0; i < M; ++i) {
            const auto& x = a[i]; const auto& y = b[i];
            int k = (int)x.size();
            if (k < 2) continue;
            for (int p = 0; p < k; ++p) pos_[y[p]] = p;
            bit_.assign(k + 1, 0);
            for (int p = 0; p < k; ++p) {
                int v = pos_[x[p]];
                int c = 0;
                for (int t = v + 1; t > 0; t -= t & -t) c += bit_[t];
                d += p - c;
                for (int t = v + 1; t <= k; t += t & -t) ++bit_[t];
            }
        }
        return (int)d;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        Sol s = cur;
        cand_.clear(); machs_.clear();
        for (size_t i = 0; i < s.size(); ++i) {
            int k = (int)s[i].size();
            if (k < 2) continue;
            for (int p = 0; p < k; ++p) pos_[guide[i][p]] = p;
            bool any = false;
            for (int p = 0; p + 1 < k; ++p)
                if (pos_[s[i][p]] > pos_[s[i][p + 1]]) { cand_.push_back({(int)i, p}); any = true; }
            if (any) machs_.push_back((int)i);
        }
        if (cand_.empty()) return s;
        int mi, p;
        if (rng.uniform() < focus_) {
            mi = machs_[rng.below((int)machs_.size())];
            tmp_.clear();
            for (auto& c : cand_) if (c.first == mi) tmp_.push_back(c.second);
            p = tmp_[rng.below((int)tmp_.size())];
        } else {
            auto c = cand_[rng.below((int)cand_.size())];
            mi = c.first; p = c.second;
        }
        std::swap(s[mi][p], s[mi][p + 1]);
        return s;
    }
private:
    const Model& md_;
    double focus_;
    std::vector<int> pos_, bit_, tmp_, machs_;
    std::vector<std::pair<int,int>> cand_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<ArcFlipRelink>(model, params.get("machine_focus", 0.3));
}
