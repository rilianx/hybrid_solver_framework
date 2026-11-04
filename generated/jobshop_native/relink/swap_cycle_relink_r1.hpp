// COMPONENT: {"name": "swap_cycle_relink", "slot": "relink", "params": {"machine_focus": {"type": "float", "range": [0.0, 1.0]}}}
class SwapCycleRelink : public hsf::Relink<Model> {
public:
    SwapCycleRelink(const Model& md, double focus) : md_(md), focus_(focus) {
        pos_.assign(std::max(1, md.n), 0);
        posc_.assign(std::max(1, md.n), 0);
    }
    int distance(const Sol& a, const Sol& b) override {
        int d = 0;
        size_t M = std::min(a.size(), b.size());
        for (size_t i = 0; i < M; ++i) {
            const auto& x = a[i]; const auto& y = b[i];
            int k = (int)x.size();
            if (k == 0) continue;
            for (int p = 0; p < k; ++p) pos_[y[p]] = p;
            vis_.assign(k, 0);
            int cyc = 0;
            for (int p = 0; p < k; ++p) {
                if (vis_[p]) continue;
                ++cyc;
                int q = p;
                while (!vis_[q]) { vis_[q] = 1; q = pos_[x[q]]; }
            }
            d += k - cyc;
        }
        return d;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        Sol s = cur;
        cand_.clear(); machs_.clear();
        for (size_t i = 0; i < s.size(); ++i) {
            bool diff = false;
            for (size_t p = 0; p < s[i].size(); ++p)
                if (s[i][p] != guide[i][p]) { cand_.push_back({(int)i, (int)p}); diff = true; }
            if (diff) machs_.push_back((int)i);
        }
        if (cand_.empty()) return s;
        int mi, p;
        if (rng.uniform() < focus_) {
            mi = machs_[rng.below((int)machs_.size())];
            tmp_.clear();
            for (size_t q = 0; q < s[mi].size(); ++q) if (s[mi][q] != guide[mi][q]) tmp_.push_back((int)q);
            p = tmp_[rng.below((int)tmp_.size())];
        } else {
            auto c = cand_[rng.below((int)cand_.size())];
            mi = c.first; p = c.second;
        }
        auto& v = s[mi];
        int x = guide[mi][p];
        int q = p;
        for (size_t t = 0; t < v.size(); ++t) if (v[t] == x) { q = (int)t; break; }
        std::swap(v[p], v[q]);
        return s;
    }
private:
    const Model& md_;
    double focus_;
    std::vector<int> pos_, posc_, vis_, tmp_, machs_;
    std::vector<std::pair<int,int>> cand_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<SwapCycleRelink>(model, params.get("machine_focus", 0.5));
}
