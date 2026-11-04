// COMPONENT: {"name": "lis_insertion_relink", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["uniform", "far"]}}}
class LisInsertionRelink : public hsf::Relink<Model> {
public:
    LisInsertionRelink(const Model& md, bool far) : md_(md), far_(far) {
        pos_.assign(std::max(1, md.n), 0);
    }
    int distance(const Sol& a, const Sol& b) override {
        int d = 0;
        size_t M = std::min(a.size(), b.size());
        for (size_t i = 0; i < M; ++i) {
            int k = (int)a[i].size();
            if (k == 0) continue;
            d += k - lis(a[i], b[i], false);
        }
        return d;
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        Sol s = cur;
        machs_.clear();
        for (size_t i = 0; i < s.size(); ++i) if (s[i] != guide[i]) machs_.push_back((int)i);
        if (machs_.empty()) return s;
        int mi = machs_[rng.below((int)machs_.size())];
        auto& v = s[mi];
        int k = (int)v.size();
        lis(v, guide[mi], true);  // fills val_, inLis_
        tmp_.clear();
        if (far_) {
            int best = -1;
            for (int p = 0; p < k; ++p) if (!inLis_[p]) {
                int dd = std::abs(p - val_[p]);
                if (dd > best) { best = dd; tmp_.clear(); }
                if (dd == best) tmp_.push_back(p);
            }
        } else {
            for (int p = 0; p < k; ++p) if (!inLis_[p]) tmp_.push_back(p);
        }
        if (tmp_.empty()) return s;
        int r = tmp_[rng.below((int)tmp_.size())];
        int x = v[r], vx = val_[r];
        // build new sequence without r, find insertion point
        nv_.clear(); nl_.clear(); nval_.clear();
        for (int p = 0; p < k; ++p) if (p != r) { nv_.push_back(v[p]); nl_.push_back(inLis_[p]); nval_.push_back(val_[p]); }
        int ins = 0;
        for (int p = 0; p < (int)nv_.size(); ++p)
            if (nl_[p] && nval_[p] < vx) ins = p + 1;
        nv_.insert(nv_.begin() + ins, x);
        v = nv_;
        return s;
    }
private:
    // LIS of guide positions of x; optionally marks members
    int lis(const std::vector<int>& x, const std::vector<int>& y, bool mark) {
        int k = (int)x.size();
        for (int p = 0; p < k; ++p) pos_[y[p]] = p;
        val_.resize(k);
        for (int p = 0; p < k; ++p) val_[p] = pos_[x[p]];
        tailv_.clear(); taili_.clear();
        par_.assign(k, -1);
        for (int p = 0; p < k; ++p) {
            int L = (int)(std::lower_bound(tailv_.begin(), tailv_.end(), val_[p]) - tailv_.begin());
            par_[p] = L > 0 ? taili_[L - 1] : -1;
            if (L == (int)tailv_.size()) { tailv_.push_back(val_[p]); taili_.push_back(p); }
            else { tailv_[L] = val_[p]; taili_[L] = p; }
        }
        int len = (int)tailv_.size();
        if (mark) {
            inLis_.assign(k, 0);
            int c = len > 0 ? taili_[len - 1] : -1;
            while (c >= 0) { inLis_[c] = 1; c = par_[c]; }
        }
        return len;
    }
    const Model& md_;
    bool far_;
    std::vector<int> pos_, val_, tailv_, taili_, par_, inLis_, tmp_, machs_, nv_, nl_, nval_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<LisInsertionRelink>(model, params.text("pick", "uniform") == "far");
}
