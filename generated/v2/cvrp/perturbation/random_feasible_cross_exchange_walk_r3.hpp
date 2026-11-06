// COMPONENT: {"name": "random_feasible_cross_exchange_walk", "slot": "perturbation", "params": {"per_strength": {"type": "float", "range": [0.5, 2.0]}, "seg_frac": {"type": "float", "range": [0.25, 0.75]}, "p_intra": {"type": "float", "range": [0.0, 0.3]}, "cluster_routes": {"type": "int", "range": [2, 3]}, "p_tail": {"type": "float", "range": [0.3, 0.7]}}}
using Sol = std::vector<std::vector<int>>;
static const double kEpsCW = 1e-9;

static void cw_normalize(const Model& m, const Sol& s, Sol& R, std::vector<double>& load,
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
        while (l > m.capacity + kEpsCW && !nr.empty()) {
            int c = nr.back(); nr.pop_back(); l -= m.demand[c]; missing.push_back(c);
        }
        if (!nr.empty()) { R.push_back(std::move(nr)); load.push_back(l); }
    }
    for (int c = 1; c <= n; ++c) if (!seen[c]) missing.push_back(c);
}

static void cw_canon(const Sol& in, Sol& out) {
    out.clear();
    for (const auto& r : in) if (!r.empty()) {
        out.push_back(r);
        if (out.back().front() > out.back().back()) std::reverse(out.back().begin(), out.back().end());
    }
    std::sort(out.begin(), out.end());
}

static void cw_ensure_distinct(const Model& m, Sol& R, const Sol& s, Rng& rng) {
    Sol a, b; cw_canon(R, a); cw_canon(s, b);
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
            if (j != i && m.demand[R[i][0]] + m.demand[R[j][0]] <= m.capacity + kEpsCW) {
                R[i].push_back(R[j][0]); R.erase(R.begin() + j); return;
            }
    }
}

class RandomCrossExchangeWalk : public hsf::Perturbation<Model> {
    const Model& m;
    double perS, pIntra, segFrac, pTail;
    int clusterK;
    std::vector<double> load_;
    std::vector<int> missing_, segA_, segB_, tmp_, cluster_;
    std::vector<char> seen_;
    std::vector<std::pair<double, int>> cand_;

    bool fits(double l) const { return l <= m.capacity + kEpsCW; }

    // Segment length proportional to the route length (large blocks).
    int segLen(int L, Rng& rng) const {
        int l = (int)std::lround(segFrac * L * (0.5 + rng.uniform()));
        return std::max(1, std::min(L, l));
    }

    // Elige una ruta ancla y sus rutas más cercanas (cluster sobre el que camina).
    void pickCluster(const Sol& R, Rng& rng) {
        cluster_.clear();
        int nr = (int)R.size();
        if (nr == 0) return;
        int r0 = rng.below(nr);
        cluster_.push_back(r0);
        int k = std::min(clusterK, nr);
        if (k < 2) return;
        const auto& A = R[r0];
        int samples = std::min<int>(4, (int)A.size());
        int sa[4];
        for (int t = 0; t < samples; ++t) sa[t] = A[rng.below((int)A.size())];
        cand_.clear();
        for (int r = 0; r < nr; ++r) {
            if (r == r0) continue;
            double best = std::numeric_limits<double>::infinity();
            for (int b : R[r])
                for (int t = 0; t < samples; ++t) {
                    double d = m.dist(sa[t], b);
                    if (d < best) best = d;
                }
            cand_.push_back({best + 1e-9 * rng.uniform(), r});
        }
        int take = std::min<int>(k - 1, (int)cand_.size());
        std::partial_sort(cand_.begin(), cand_.begin() + take, cand_.end());
        for (int t = 0; t < take; ++t) cluster_.push_back(cand_[t].second);
    }

    bool tryMove(Sol& R, Rng& rng) {
        int kc = (int)cluster_.size();
        if (kc == 0) return false;
        if (kc < 2 || rng.uniform() < pIntra) {
            int r = cluster_[rng.below(kc)];
            int L = (int)R[r].size();
            if (L < 4) return false;
            int len = std::max(3, std::min(L - 1, segLen(L, rng)));
            int i = rng.below(L - len + 1), j = i + len - 1;
            std::reverse(R[r].begin() + i, R[r].begin() + j + 1);
            return true;
        }
        int a = rng.below(kc), b = rng.below(kc - 1);
        if (b >= a) ++b;
        int r1 = cluster_[a], r2 = cluster_[b];
        std::vector<int>& A = R[r1];
        std::vector<int>& B = R[r2];
        int La = (int)A.size(), Lb = (int)B.size();
        if (rng.uniform() >= pTail) {
            // cross-exchange de segmentos grandes (proporcionales a la ruta)
            if (La == 0 || Lb == 0) return false;
            int la = segLen(La, rng);
            int lb = segLen(Lb, rng);
            if (la == La && lb == Lb) return false;  // solo renombraría rutas
            if (la + lb < 3 && La + Lb >= 3) return false;
            int ia = rng.below(La - la + 1), ib = rng.below(Lb - lb + 1);
            double dA = 0, dB = 0;
            for (int t = ia; t < ia + la; ++t) dA += m.demand[A[t]];
            for (int t = ib; t < ib + lb; ++t) dB += m.demand[B[t]];
            double nA = load_[r1] - dA + dB, nB = load_[r2] - dB + dA;
            if (!fits(nA) || !fits(nB)) return false;
            segA_.assign(A.begin() + ia, A.begin() + ia + la);
            segB_.assign(B.begin() + ib, B.begin() + ib + lb);
            if (rng.uniform() < 0.5) std::reverse(segA_.begin(), segA_.end());
            if (rng.uniform() < 0.5) std::reverse(segB_.begin(), segB_.end());
            tmp_.assign(A.begin(), A.begin() + ia);
            tmp_.insert(tmp_.end(), segB_.begin(), segB_.end());
            tmp_.insert(tmp_.end(), A.begin() + ia + la, A.end());
            A.swap(tmp_);
            tmp_.assign(B.begin(), B.begin() + ib);
            tmp_.insert(tmp_.end(), segA_.begin(), segA_.end());
            tmp_.insert(tmp_.end(), B.begin() + ib + lb, B.end());
            B.swap(tmp_);
            load_[r1] = nA; load_[r2] = nB;
            return true;
        } else {
            // 2-opt*: intercambio de colas
            int i = La >= 2 ? 1 + rng.below(La - 1) : rng.below(La + 1);
            double pa = 0;
            for (int t = 0; t < i; ++t) pa += m.demand[A[t]];
            tmp_.clear();
            double pb = 0;
            for (int jj = 0; jj <= Lb; ++jj) {
                if (jj > 0) pb += m.demand[B[jj - 1]];
                if ((i == 0 && jj == 0) || (i == La && jj == Lb)) continue;
                if ((i == 0 && jj == Lb) || (i == La && jj == 0)) continue;
                if (fits(pa + (load_[r2] - pb)) && fits(pb + (load_[r1] - pa))) tmp_.push_back(jj);
            }
            if (tmp_.empty()) return false;
            int j = tmp_[rng.below((int)tmp_.size())];
            pb = 0;
            for (int t = 0; t < j; ++t) pb += m.demand[B[t]];
            double nA = pa + (load_[r2] - pb), nB = pb + (load_[r1] - pa);
            segA_.assign(A.begin() + i, A.end());
            segB_.assign(B.begin() + j, B.end());
            A.resize(i); A.insert(A.end(), segB_.begin(), segB_.end());
            B.resize(j); B.insert(B.end(), segA_.begin(), segA_.end());
            load_[r1] = nA; load_[r2] = nB;
            return true;
        }
    }
public:
    RandomCrossExchangeWalk(const Model& mm, double ps, double sf, double pi, int ck, double pt)
        : m(mm), perS(ps), pIntra(pi), segFrac(sf), pTail(pt), clusterK(std::max(2, ck)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol R;
        cw_normalize(m, s, R, load_, missing_, seen_);
        // reparación (solo si la entrada era infactible): inserción más barata factible
        for (int c : missing_) {
            double best = 2.0 * m.dist(0, c); int bR = -1, bP = 0;
            for (int r = 0; r < (int)R.size(); ++r) {
                if (!fits(load_[r] + m.demand[c])) continue;
                const auto& rt = R[r];
                int L = (int)rt.size(), prev = 0;
                for (int p = 0; p <= L; ++p) {
                    int nx = p == L ? 0 : rt[p];
                    double d = m.dist(prev, c) + m.dist(c, nx) - m.dist(prev, nx);
                    if (d < best) { best = d; bR = r; bP = p; }
                    prev = nx;
                }
            }
            if (bR < 0) { R.push_back(std::vector<int>{c}); load_.push_back(m.demand[c]); }
            else { R[bR].insert(R[bR].begin() + bP, c); load_[bR] += m.demand[c]; }
        }
        pickCluster(R, rng);
        int moves = std::max(1, (int)std::lround(std::max(1.0, strength) * perS));
        for (int mv = 0; mv < moves; ++mv)
            for (int t = 0; t < 30; ++t)
                if (tryMove(R, rng)) break;
        Sol out; out.reserve(R.size());
        for (auto& r : R) if (!r.empty()) out.push_back(std::move(r));
        cw_ensure_distinct(m, out, s, rng);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double ps = params.get("per_strength", 1.0);
    double sf = params.get("seg_frac", 0.45);
    double pi = params.get("p_intra", 0.1);
    int ck = (int)params.get("cluster_routes", 2);
    double pt = params.get("p_tail", 0.5);
    return std::unique_ptr<hsf::Perturbation<Model>>(new RandomCrossExchangeWalk(model, ps, sf, pi, ck, pt));
}
