// COMPONENT: {"name": "lis_insertion_relink", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["uniform", "weighted"]}}}
class LisInsertionRelink : public hsf::Relink<JobShop> {
    const JobShop& md;
    bool weighted;
    std::vector<int> pos, ma, mb, p, tails, tailIdx, pred, nonLis, lisIdx;
    std::vector<char> inLis;
    std::vector<int> diffM;
    std::vector<long long> weight;
    int stamp = 0;

    bool compat(const std::vector<int>& a, const std::vector<int>& b) {
        if (a.size() != b.size()) return false;
        ++stamp;
        int n = md.n;
        for (size_t i = 0; i < b.size(); ++i) {
            int j = b[i];
            if (j < 0 || j >= n || mb[j] == stamp) return false;
            mb[j] = stamp;
            pos[j] = (int)i;
        }
        for (int j : a) {
            if (j < 0 || j >= n || mb[j] != stamp || ma[j] == stamp) return false;
            ma[j] = stamp;
        }
        return true;
    }
    // LIS de p (valores distintos); deja tails/tailIdx/pred listos para reconstruir
    int lis(const std::vector<int>& a) {
        int L = (int)a.size();
        p.resize(L);
        for (int i = 0; i < L; ++i) p[i] = pos[a[i]];
        tails.clear(); tailIdx.clear();
        pred.assign(L, -1);
        for (int i = 0; i < L; ++i) {
            int k = (int)(std::lower_bound(tails.begin(), tails.end(), p[i]) - tails.begin());
            if (k == (int)tails.size()) { tails.push_back(p[i]); tailIdx.push_back(i); }
            else { tails[k] = p[i]; tailIdx[k] = i; }
            pred[i] = k > 0 ? tailIdx[k - 1] : -1;
        }
        return (int)tails.size();
    }
    long long contrib(const std::vector<int>& a, const std::vector<int>& b) {
        if (a == b) return 0;
        if (compat(a, b)) return (long long)a.size() - lis(a);
        return 1 + (long long)std::max(a.size(), b.size());
    }

public:
    LisInsertionRelink(const JobShop& m, bool w) : md(m), weighted(w) {
        int n = std::max(1, md.n);
        pos.assign(n, 0); ma.assign(n, 0); mb.assign(n, 0);
    }
    int distance(const Sol& a, const Sol& b) override {
        long long d = std::llabs((long long)a.size() - (long long)b.size());
        size_t M = std::min(a.size(), b.size());
        for (size_t mm = 0; mm < M; ++mm) d += contrib(a[mm], b[mm]);
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) {
            Sol r = cur;
            r.resize(guide.size());
            for (size_t i = cur.size(); i < guide.size(); ++i) r[i] = guide[i];
            return r;
        }
        diffM.clear(); weight.clear();
        long long tot = 0;
        for (size_t mm = 0; mm < cur.size(); ++mm) {
            long long c = contrib(cur[mm], guide[mm]);
            if (c > 0) { diffM.push_back((int)mm); weight.push_back(c); tot += c; }
        }
        if (diffM.empty()) return guide;
        int mm;
        if (weighted && tot > 0) {
            long long t = (long long)(rng.uniform() * (double)tot);
            if (t >= tot) t = tot - 1;
            size_t k = 0;
            while (k + 1 < diffM.size() && t >= weight[k]) t -= weight[k], ++k;
            mm = diffM[k];
        } else {
            mm = diffM[rng.below((int)diffM.size())];
        }
        Sol r = cur;
        if (!compat(cur[mm], guide[mm])) { r[mm] = guide[mm]; return r; }
        const auto& s = cur[mm];
        int L = (int)s.size();
        int len = lis(s);
        inLis.assign(L, 0);
        lisIdx.clear();
        for (int i = tailIdx[len - 1]; i >= 0; i = pred[i]) inLis[i] = 1, lisIdx.push_back(i);
        nonLis.clear();
        for (int i = 0; i < L; ++i) if (!inLis[i]) nonLis.push_back(i);
        if (nonLis.empty()) { r[mm] = guide[mm]; return r; }
        int x = nonLis[rng.below((int)nonLis.size())];
        int px = p[x];
        int y = -1, py = -1;  // miembro del LIS con mayor p < px
        for (int i : lisIdx) if (p[i] < px && p[i] > py) py = p[i], y = i;
        std::vector<int> ns;
        ns.reserve(L);
        if (y < 0) ns.push_back(s[x]);
        for (int i = 0; i < L; ++i) {
            if (i == x) continue;
            ns.push_back(s[i]);
            if (i == y) ns.push_back(s[x]);
        }
        r[mm] = std::move(ns);
        return r;
    }
};

std::unique_ptr<hsf::Relink<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    bool w = params.text("pick", "uniform") == "weighted";
    return std::make_unique<LisInsertionRelink>(model, w);
}
