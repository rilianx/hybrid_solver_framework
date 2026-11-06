// COMPONENT: {"name": "random_removal_regret2_reinsert", "slot": "perturbation", "params": {"per_strength": {"type": "float", "range": [0.5, 4.0]}, "max_frac": {"type": "float", "range": [0.05, 0.5]}, "noise": {"type": "float", "range": [0.0, 0.3]}}}
using Sol = std::vector<std::vector<int>>;
static const double kEpsRR = 1e-9;

static void rr_normalize(const Model& m, const Sol& s, Sol& R, std::vector<double>& load,
                         std::vector<int>& missing, std::vector<char>& seen) {
    int n = m.n;
    seen.assign(n + 1, 0);
    R.clear(); load.clear(); missing.clear();
    for (const auto& r : s) {
        std::vector<int> nr; double l = 0;
        for (int c : r) {
            if (c < 1 || c > n || seen[c]) continue;
            seen[c] = 1; nr.push_back(c); l += m.demand[c];
        }
        while (l > m.capacity + kEpsRR && !nr.empty()) {
            int c = nr.back(); nr.pop_back(); l -= m.demand[c]; missing.push_back(c);
        }
        if (!nr.empty()) { R.push_back(std::move(nr)); load.push_back(l); }
    }
    for (int c = 1; c <= n; ++c) if (!seen[c]) missing.push_back(c);
}

static void rr_canon(const Sol& in, Sol& out) {
    out.clear();
    for (const auto& r : in) if (!r.empty()) {
        out.push_back(r);
        if (out.back().front() > out.back().back()) std::reverse(out.back().begin(), out.back().end());
    }
    std::sort(out.begin(), out.end());
}

static void rr_ensure_distinct(const Model& m, Sol& R, const Sol& s, Rng& rng) {
    Sol a, b; rr_canon(R, a); rr_canon(s, b);
    if (a != b) return;
    std::vector<int> big;
    for (int i = 0; i < (int)R.size(); ++i) if (R[i].size() >= 2) big.push_back(i);
    if (!big.empty()) {
        int r = big[rng.below((int)big.size())];
        int p = rng.below((int)R[r].size());
        int c = R[r][p];
        R[r].erase(R[r].begin() + p);
        R.push_back(std::vector<int>{c});
        return;
    }
    int k = (int)R.size();
    if (k < 2) return;
    int st = rng.below(k);
    for (int t = 0; t < k; ++t) {
        int i = (st + t) % k;
        for (int j = 0; j < k; ++j)
            if (j != i && m.demand[R[i][0]] + m.demand[R[j][0]] <= m.capacity + kEpsRR) {
                R[i].push_back(R[j][0]); R.erase(R.begin() + j); return;
            }
    }
}

class RandomRemovalRegret2 : public hsf::Perturbation<Model> {
    const Model& m;
    double perS, maxFrac, noise;
    std::vector<double> load_;
    std::vector<int> pool_, present_;
    std::vector<char> seen_, rem_, alive_;
    std::vector<std::vector<double>> bc_;
    std::vector<std::vector<int>> bp_;

    inline double insd(const std::vector<int>& r, int p, int c) const {
        int a = p == 0 ? 0 : r[p - 1];
        int b = p == (int)r.size() ? 0 : r[p];
        return m.dist(a, c) + m.dist(c, b) - m.dist(a, b);
    }
    void evalc(const Sol& R, int c, int r, double& bd, int& bpos, Rng& rng) {
        bd = 1e300; bpos = -1;
        if (load_[r] + m.demand[c] > m.capacity + kEpsRR) return;
        const auto& rt = R[r];
        int L = (int)rt.size();
        for (int p = 0; p <= L; ++p) {
            double d = insd(rt, p, c);
            if (d < bd) { bd = d; bpos = p; }
        }
        if (noise > 0 && bpos >= 0) bd *= 1.0 + noise * (2.0 * rng.uniform() - 1.0);
    }
public:
    RandomRemovalRegret2(const Model& mm, double ps, double mf, double nz)
        : m(mm), perS(ps), maxFrac(mf), noise(nz) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol R;
        rr_normalize(m, s, R, load_, pool_, seen_);
        int n = m.n;
        present_.clear();
        for (auto& r : R) for (int c : r) present_.push_back(c);
        int maxk = std::max(1, (int)(maxFrac * n));
        int k = (int)std::lround(std::max(1.0, strength) * perS);
        k = std::max(1, std::min(k, maxk));
        k = std::min(k, (int)present_.size());
        if (k > 0) {
            rem_.assign(n + 1, 0);
            for (int i = 0; i < k; ++i) {
                int j = i + rng.below((int)present_.size() - i);
                std::swap(present_[i], present_[j]);
                rem_[present_[i]] = 1;
                pool_.push_back(present_[i]);
            }
            Sol R2; load_.clear();
            for (auto& r : R) {
                std::vector<int> nr; double l = 0;
                for (int c : r) if (!rem_[c]) { nr.push_back(c); l += m.demand[c]; }
                if (!nr.empty()) { R2.push_back(std::move(nr)); load_.push_back(l); }
            }
            R.swap(R2);
        }
        int K = (int)pool_.size();
        bc_.assign(K, {}); bp_.assign(K, {});
        alive_.assign(K, 1);
        for (int i = 0; i < K; ++i) {
            bc_[i].resize(R.size()); bp_[i].resize(R.size());
            for (int r = 0; r < (int)R.size(); ++r) evalc(R, pool_[i], r, bc_[i][r], bp_[i][r], rng);
        }
        int left = K;
        while (left > 0) {
            int bi = -1, bR = -1; double bestReg = -1.0, bestB1 = 1e300;
            for (int i = 0; i < K; ++i) {
                if (!alive_[i]) continue;
                int c = pool_[i];
                double b1 = 2.0 * m.dist(0, c), b2 = 1e300; int br = -1;
                const auto& row = bc_[i];
                for (int r = 0; r < (int)row.size(); ++r) {
                    double v = row[r];
                    if (v < b1) { b2 = b1; b1 = v; br = r; }
                    else if (v < b2) b2 = v;
                }
                double reg = b2 - b1;
                if (reg > bestReg || (reg == bestReg && b1 < bestB1)) {
                    bestReg = reg; bestB1 = b1; bi = i; bR = br;
                }
            }
            int c = pool_[bi];
            alive_[bi] = 0; --left;
            if (bR < 0) {
                R.push_back(std::vector<int>{c});
                load_.push_back(m.demand[c]);
                int nr = (int)R.size() - 1;
                for (int j = 0; j < K; ++j) if (alive_[j]) {
                    double d; int p;
                    evalc(R, pool_[j], nr, d, p, rng);
                    bc_[j].push_back(d); bp_[j].push_back(p);
                }
            } else {
                int p = bp_[bi][bR];
                R[bR].insert(R[bR].begin() + p, c);
                load_[bR] += m.demand[c];
                for (int j = 0; j < K; ++j) if (alive_[j])
                    evalc(R, pool_[j], bR, bc_[j][bR], bp_[j][bR], rng);
            }
        }
        rr_ensure_distinct(m, R, s, rng);
        return R;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("per_strength", 1.5);
    double mf = params.get("max_frac", 0.2);
    double nz = params.get("noise", 0.05);
    return std::unique_ptr<hsf::Perturbation<Model>>(new RandomRemovalRegret2(model, ps, mf, nz));
}
