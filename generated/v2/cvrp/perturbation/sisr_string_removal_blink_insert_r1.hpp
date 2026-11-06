// COMPONENT: {"name": "sisr_string_removal_blink_insert", "slot": "perturbation", "params": {"per_strength": {"type": "float", "range": [1.0, 6.0]}, "max_frac": {"type": "float", "range": [0.05, 0.5]}, "max_string": {"type": "int", "range": [2, 15]}, "blink": {"type": "float", "range": [0.0, 0.2]}, "knn": {"type": "int", "range": [10, 80]}}}
using Sol = std::vector<std::vector<int>>;
static const double kEpsSS = 1e-9;

static void ss_normalize(const Model& m, const Sol& s, Sol& R, std::vector<double>& load,
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
        while (l > m.capacity + kEpsSS && !nr.empty()) {
            int c = nr.back(); nr.pop_back(); l -= m.demand[c]; missing.push_back(c);
        }
        if (!nr.empty()) { R.push_back(std::move(nr)); load.push_back(l); }
    }
    for (int c = 1; c <= n; ++c) if (!seen[c]) missing.push_back(c);
}

static void ss_canon(const Sol& in, Sol& out) {
    out.clear();
    for (const auto& r : in) if (!r.empty()) {
        out.push_back(r);
        if (out.back().front() > out.back().back()) std::reverse(out.back().begin(), out.back().end());
    }
    std::sort(out.begin(), out.end());
}

static void ss_ensure_distinct(const Model& m, Sol& R, const Sol& s, Rng& rng) {
    Sol a, b; ss_canon(R, a); ss_canon(s, b);
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
            if (j != i && m.demand[R[i][0]] + m.demand[R[j][0]] <= m.capacity + kEpsSS) {
                R[i].push_back(R[j][0]); R.erase(R.begin() + j); return;
            }
    }
}

class SisrStringRemoval : public hsf::Perturbation<Model> {
    const Model& m;
    double perS, maxFrac, blink;
    int maxStr, knn;
    std::vector<std::vector<int>> nbr_;
    std::vector<char> nbrDone_;
    std::vector<double> load_;
    std::vector<int> pool_, routeOf_;
    std::vector<char> seen_, rem_, ruined_;
    std::vector<std::pair<double, int>> tmp_;

    const std::vector<int>& neighbors(int c) {
        if (!nbrDone_[c]) {
            nbrDone_[c] = 1;
            int n = m.n;
            tmp_.clear();
            for (int o = 1; o <= n; ++o) if (o != c) tmp_.push_back({m.dist(c, o), o});
            int kn = std::min(knn, (int)tmp_.size());
            if (kn > 0) std::partial_sort(tmp_.begin(), tmp_.begin() + kn, tmp_.end());
            nbr_[c].resize(kn);
            for (int i = 0; i < kn; ++i) nbr_[c][i] = tmp_[i].second;
        }
        return nbr_[c];
    }
public:
    SisrStringRemoval(const Model& mm, double ps, double mf, int ms, double bl, int kn)
        : m(mm), perS(ps), maxFrac(mf), blink(bl), maxStr(ms), knn(kn) {
        nbr_.assign(m.n + 1, {});
        nbrDone_.assign(m.n + 1, 0);
    }

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol R;
        ss_normalize(m, s, R, load_, pool_, seen_);
        int n = m.n;
        routeOf_.assign(n + 1, -1);
        int present = 0;
        for (int r = 0; r < (int)R.size(); ++r)
            for (int c : R[r]) { routeOf_[c] = r; ++present; }
        if (present > 0) {
            int maxk = std::max(1, (int)(maxFrac * n));
            int k = (int)std::lround(std::max(1.0, strength) * perS);
            k = std::max(1, std::min(k, std::min(maxk, present)));
            int avg = std::max(1, present / std::max(1, (int)R.size()));
            int Lmax = std::max(1, std::min(maxStr, avg));
            rem_.assign(n + 1, 0);
            ruined_.assign(R.size(), 0);
            int removed = 0;
            auto process = [&](int c) {
                int r = routeOf_[c];
                if (r < 0 || rem_[c] || ruined_[r]) return;
                ruined_[r] = 1;
                const auto& rt = R[r];
                int L = (int)rt.size();
                int l = 1 + rng.below(std::min(Lmax, L));
                int idx = (int)(std::find(rt.begin(), rt.end(), c) - rt.begin());
                int lo = std::max(0, idx - l + 1), hi = std::min(idx, L - l);
                int st = lo + rng.below(hi - lo + 1);
                for (int t = st; t < st + l; ++t) {
                    rem_[rt[t]] = 1; pool_.push_back(rt[t]); ++removed;
                }
            };
            int seed;
            do { seed = 1 + rng.below(n); } while (routeOf_[seed] < 0);
            process(seed);
            if (removed < k) {
                const auto& nb = neighbors(seed);
                for (int c : nb) { if (removed >= k) break; process(c); }
            }
            Sol R2; std::vector<double> L2;
            for (auto& r : R) {
                std::vector<int> nr; double l = 0;
                for (int c : r) if (!rem_[c]) { nr.push_back(c); l += m.demand[c]; }
                if (!nr.empty()) { R2.push_back(std::move(nr)); L2.push_back(l); }
            }
            R.swap(R2); load_.swap(L2);
        }
        // orden de reinserción
        std::shuffle(pool_.begin(), pool_.end(), rng.g);
        int ord = rng.below(4);
        if (ord == 1)
            std::stable_sort(pool_.begin(), pool_.end(), [&](int a, int b) { return m.demand[a] > m.demand[b]; });
        else if (ord == 2)
            std::stable_sort(pool_.begin(), pool_.end(), [&](int a, int b) { return m.dist(0, a) > m.dist(0, b); });
        else if (ord == 3)
            std::stable_sort(pool_.begin(), pool_.end(), [&](int a, int b) { return m.dist(0, a) < m.dist(0, b); });
        for (int c : pool_) {
            double best = 2.0 * m.dist(0, c); int bR = -1, bP = 0;
            double dc = m.demand[c];
            for (int r = 0; r < (int)R.size(); ++r) {
                if (load_[r] + dc > m.capacity + kEpsSS) continue;
                const auto& rt = R[r];
                int L = (int)rt.size();
                int prev = 0;
                for (int p = 0; p <= L; ++p) {
                    int nx = p == L ? 0 : rt[p];
                    if (!(blink > 0 && rng.uniform() < blink)) {
                        double d = m.dist(prev, c) + m.dist(c, nx) - m.dist(prev, nx);
                        if (d < best) { best = d; bR = r; bP = p; }
                    }
                    prev = nx;
                }
            }
            if (bR < 0) { R.push_back(std::vector<int>{c}); load_.push_back(dc); }
            else { R[bR].insert(R[bR].begin() + bP, c); load_[bR] += dc; }
        }
        ss_ensure_distinct(m, R, s, rng);
        return R;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("per_strength", 3.0);
    double mf = params.get("max_frac", 0.2);
    int ms = (int)params.get("max_string", 8);
    double bl = params.get("blink", 0.01);
    int kn = (int)params.get("knn", 40);
    return std::unique_ptr<hsf::Perturbation<Model>>(new SisrStringRemoval(model, ps, mf, ms, bl, kn));
}
