// COMPONENT: {"name": "route_prefix_growth_relink", "slot": "relink", "params": {"greedy_prob": {"type": "float", "range": [0.0, 1.0]}}}
class RoutePrefixRelink : public hsf::Relink<Model> {
public:
    using Sol = Model::Solution;
    RoutePrefixRelink(const Model& m, double g) : m_(m), greedy_(g) {}

    int distance(const Sol& a, const Sol& b) override {
        size_t Rm = std::min(a.size(), b.size());
        long long d = 0;
        for (size_t i = 0; i < Rm; ++i) {
            int l = lcpOf(a[i], b[i]);
            d += (long long)a[i].size() + (long long)b[i].size() - 2LL * l;
        }
        for (size_t i = Rm; i < a.size(); ++i) d += (long long)a[i].size() + 1;
        for (size_t i = Rm; i < b.size(); ++i) d += (long long)b[i].size() + 1;
        return (int)d;
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        const size_t Rc = cur.size(), Rg = guide.size();
        const size_t Rm = std::min(Rc, Rg);
        lcp_.assign(Rm, 0);
        cand_.clear();
        for (size_t i = 0; i < Rm; ++i) {
            lcp_[i] = lcpOf(cur[i], guide[i]);
            if (lcp_[i] < (int)guide[i].size()) cand_.push_back((int)i);
        }
        if (Rc < Rg) cand_.push_back(-1);
        if (Rc > Rg && cur.back().empty()) cand_.push_back(-2);
        if (cand_.empty()) {
            Sol s = cur;
            if (Rc > Rg) { s.pop_back(); return s; }
            for (size_t i = 0; i < Rm; ++i)
                if ((int)s[i].size() > lcp_[i]) { s[i].resize(lcp_[i]); return s; }
            return guide;
        }
        rid_.assign(m_.n + 1, -1);
        pos_.assign(m_.n + 1, -1);
        for (size_t j = 0; j < Rc; ++j)
            for (size_t q = 0; q < cur[j].size(); ++q) {
                int c = cur[j][q];
                if (valid(c)) { rid_[c] = (int)j; pos_[c] = (int)q; }
            }
        int k;
        if (cand_.size() > 1 && rng.uniform() < greedy_) {
            load_.assign(Rc, 0.0);
            for (size_t j = 0; j < Rc; ++j)
                for (int c : cur[j]) if (valid(c)) load_[j] += m_.demand[c];
            double best = std::numeric_limits<double>::infinity();
            k = cand_[0];
            int ties = 0;
            for (int ci : cand_) {
                double v = (ci < 0) ? 0.0 : fixDelta(cur, guide, ci, Rm);
                if (v < best - 1e-12) { best = v; k = ci; ties = 1; }
                else if (v <= best + 1e-12) { if (rng.below(++ties) == 0) k = ci; }
            }
        } else {
            k = cand_[rng.below((int)cand_.size())];
        }
        Sol s = cur;
        if (k == -1) s.emplace_back();
        else if (k == -2) s.pop_back();
        else applyFix(s, guide, k, Rm);
        return s;
    }

private:
    const Model& m_;
    double greedy_;
    std::vector<int> rid_, pos_, lcp_, cand_;
    std::vector<double> load_;

    bool valid(int c) const { return c >= 1 && c <= m_.n; }
    double D(int i, int j) const {
        if (i < 0 || i > m_.n || j < 0 || j > m_.n) return 0.0;
        return m_.dist(i, j);
    }
    static int lcpOf(const std::vector<int>& a, const std::vector<int>& b) {
        size_t L = std::min(a.size(), b.size()), i = 0;
        while (i < L && a[i] == b[i]) ++i;
        return (int)i;
    }
    // localiza c en cur fuera de los prefijos ya alineados; devuelve false si no es removible
    bool locate(const Sol& s, int c, size_t Rm, int& j, int& q) const {
        if (!valid(c) || rid_[c] < 0) return false;
        j = rid_[c]; q = pos_[c];
        if (q >= (int)s[j].size() || s[j][q] != c) return false;
        int lj = (j < (int)Rm) ? lcp_[j] : 0;
        return q >= lj;
    }
    double fixDelta(const Sol& cur, const Sol& guide, int i, size_t Rm) const {
        int p = lcp_[i];
        int c = guide[i][p];
        int j = -1, q = -1;
        bool rem = locate(cur, c, Rm, j, q);
        double dl = 0.0;
        double dem = valid(c) ? m_.demand[c] : 0.0;
        if (rem) {
            const auto& r = cur[j];
            int pr = q > 0 ? r[q - 1] : 0;
            int nx = q + 1 < (int)r.size() ? r[q + 1] : 0;
            dl += D(pr, nx) - D(pr, c) - D(c, nx);
        }
        const auto& ri = cur[i];
        int pr2 = p > 0 ? ri[p - 1] : 0;
        int nx2 = p < (int)ri.size() ? ri[p] : 0;
        dl += D(pr2, c) + D(c, nx2) - D(pr2, nx2);
        if (!(rem && j == i)) {
            double li = load_[i];
            dl += m_.penalty * (std::max(0.0, li + dem - m_.capacity) - std::max(0.0, li - m_.capacity));
            if (rem) {
                double lj = load_[j];
                dl += m_.penalty * (std::max(0.0, lj - dem - m_.capacity) - std::max(0.0, lj - m_.capacity));
            }
        }
        return dl;
    }
    void applyFix(Sol& s, const Sol& guide, int i, size_t Rm) const {
        int p = lcp_[i];
        int c = guide[i][p];
        int j = -1, q = -1;
        bool rem = locate(s, c, Rm, j, q);
        if (rem) {
            if (j == i) {
                s[i].erase(s[i].begin() + q);
                s[i].insert(s[i].begin() + p, c);
            } else {
                s[j].erase(s[j].begin() + q);
                s[i].insert(s[i].begin() + p, c);
            }
        } else {
            s[i].insert(s[i].begin() + p, c);
        }
    }
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double g = params.get("greedy_prob", 0.3);
    return std::make_unique<RoutePrefixRelink>(model, g);
}
