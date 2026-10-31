// COMPONENT: {"name": "hamming_position_swap_relink", "slot": "relink", "params": {"pick": {"type": "cat", "values": ["position", "machine"]}}}
class HammingPositionSwapRelink : public hsf::Relink<JobShop> {
    const JobShop& md;
    bool by_machine;
    std::vector<int> pos, cpos, ma, mb;
    std::vector<std::pair<int, int>> cand;
    std::vector<int> mstart;
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
        for (size_t i = 0; i < a.size(); ++i) {
            int j = a[i];
            if (j < 0 || j >= n || mb[j] != stamp || ma[j] == stamp) return false;
            ma[j] = stamp;
            cpos[j] = (int)i;
        }
        return true;
    }

public:
    HammingPositionSwapRelink(const JobShop& m, bool bm) : md(m), by_machine(bm) {
        int n = std::max(1, md.n);
        pos.assign(n, 0); cpos.assign(n, 0); ma.assign(n, 0); mb.assign(n, 0);
    }
    int distance(const Sol& a, const Sol& b) override {
        long long d = std::llabs((long long)a.size() - (long long)b.size());
        size_t M = std::min(a.size(), b.size());
        for (size_t mm = 0; mm < M; ++mm) {
            if (a[mm] == b[mm]) continue;
            if (compat(a[mm], b[mm])) {
                for (size_t i = 0; i < a[mm].size(); ++i) d += a[mm][i] != b[mm][i];
            } else {
                d += 1 + (long long)std::max(a[mm].size(), b[mm].size());
            }
        }
        return (int)std::min<long long>(d, std::numeric_limits<int>::max());
    }
    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        if (cur.size() != guide.size()) {
            Sol r = cur;
            r.resize(guide.size());
            for (size_t i = cur.size(); i < guide.size(); ++i) r[i] = guide[i];
            return r;
        }
        cand.clear();
        mstart.clear();
        for (size_t mm = 0; mm < cur.size(); ++mm) {
            if (cur[mm] == guide[mm]) continue;
            mstart.push_back((int)cand.size());
            if (!compat(cur[mm], guide[mm])) { cand.push_back({(int)mm, -1}); continue; }
            for (size_t i = 0; i < cur[mm].size(); ++i)
                if (cur[mm][i] != guide[mm][i]) cand.push_back({(int)mm, (int)i});
        }
        if (cand.empty()) return guide;
        int idx;
        if (by_machine) {
            int k = rng.below((int)mstart.size());
            int lo = mstart[k];
            int hi = k + 1 < (int)mstart.size() ? mstart[k + 1] : (int)cand.size();
            idx = lo + rng.below(hi - lo);
        } else {
            idx = rng.below((int)cand.size());
        }
        auto [mm, i] = cand[idx];
        Sol r = cur;
        if (i < 0) { r[mm] = guide[mm]; return r; }
        compat(cur[mm], guide[mm]);  // recalcula cpos de esta máquina
        int want = guide[mm][i];
        int k = cpos[want];
        std::swap(r[mm][i], r[mm][k]);
        return r;
    }
};

std::unique_ptr<hsf::Relink<JobShop>> make_component(const JobShop& model, const hsf::Config& params) {
    bool bm = params.text("pick", "position") == "machine";
    return std::make_unique<HammingPositionSwapRelink>(model, bm);
}
