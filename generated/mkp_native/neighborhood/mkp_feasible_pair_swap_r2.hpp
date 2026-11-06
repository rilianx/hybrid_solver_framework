// COMPONENT: {"name": "mkp_feasible_pair_swap", "slot": "neighborhood", "params": {"cand_limit": {"type": "int", "range": [0, 300]}}}
using Sol = Model::Solution;

class MkpCore {
public:
    const Model& M;
    int n, m;
    int mode = -1, cg = 0, og = -1;
    bool srtC = true, srtO = true;
    Sol cached;
    bool has = false;
    std::vector<char> in;
    std::vector<double> load, nl;
    std::vector<int> chosenList, freeList;
    double obj = 0.0, prof = 0.0;
    bool feas = false, fastOk = true;

    explicit MkpCore(const Model& mm)
        : M(mm), n(mm.n), m(mm.m), in(mm.n, 0), load(mm.m, 0.0), nl(mm.m, 0.0) {}

    const double* w(int j) const { return M.wcol.data() + (size_t)j * m; }

    void detect(const Sol& s) {
        mode = 1; cg = 0; og = -1;
        if (s.size() == 1 && (int)s[0].size() == n) {
            bool ok = true;
            for (int j = 0; j < n && ok; ++j) {
                int v = s[0][j];
                if ((v != 0 && v != 1) || ((v == 1) != M.chosen(s, j))) ok = false;
            }
            if (ok) { mode = 0; return; }
        }
        if ((int)s.size() == n && n > 1) {
            bool ok = true;
            for (int j = 0; j < n && ok; ++j)
                if (s[j].size() != 1 || (s[j][0] != 0 && s[j][0] != 1)) ok = false;
            for (int j = 0; j < n && ok; ++j)
                if ((s[j][0] == 1) != M.chosen(s, j)) ok = false;
            if (ok) { mode = 2; return; }
        }
        std::vector<char> ch(n, 0);
        int cnt = 0;
        for (int j = 0; j < n; ++j) { ch[j] = M.chosen(s, j) ? 1 : 0; cnt += ch[j]; }
        for (int g = 0; g < (int)s.size(); ++g) {
            if ((int)s[g].size() != cnt) continue;
            bool ok = true;
            for (int e : s[g]) if (e < 0 || e >= n || !ch[e]) { ok = false; break; }
            if (ok) { cg = g; break; }
        }
        if (s.size() == 2) og = 1 - cg;
        srtC = cg < (int)s.size() && std::is_sorted(s[cg].begin(), s[cg].end());
        srtO = og >= 0 && std::is_sorted(s[og].begin(), s[og].end());
    }

    void sync(const Sol& s) {
        if (has && s == cached) return;
        if (mode < 0) detect(s);
        cached = s; has = true;
        std::fill(in.begin(), in.end(), 0);
        if (mode == 0) { for (int j = 0; j < n; ++j) in[j] = s[0][j] != 0; }
        else if (mode == 2) { for (int j = 0; j < n; ++j) in[j] = s[j][0] != 0; }
        else if (cg < (int)s.size()) { for (int e : s[cg]) if (e >= 0 && e < n) in[e] = 1; }
        chosenList.clear(); freeList.clear();
        std::fill(load.begin(), load.end(), 0.0);
        prof = 0.0;
        for (int j = 0; j < n; ++j) {
            if (in[j]) {
                chosenList.push_back(j); prof += M.profit[j];
                const double* wj = w(j);
                for (int i = 0; i < m; ++i) load[i] += wj[i];
            } else freeList.push_back(j);
        }
        feas = true;
        for (int i = 0; i < m; ++i) if (load[i] > M.capacity[i]) { feas = false; break; }
        obj = M.objective(s);
        if (feas && std::fabs(obj + prof) > 1e-7 * std::max(1.0, std::fabs(prof))) fastOk = false;
    }

    static void insertInto(std::vector<int>& v, int x, bool srt) {
        if (srt) v.insert(std::lower_bound(v.begin(), v.end(), x), x); else v.push_back(x);
    }
    static void eraseFrom(std::vector<int>& v, int x, bool srt) {
        auto it = srt ? std::lower_bound(v.begin(), v.end(), x) : std::find(v.begin(), v.end(), x);
        if (it != v.end() && *it == x) v.erase(it);
    }

    Sol build(const Sol& s, const int* add, int na, const int* rem, int nr) const {
        Sol t = s;
        if (mode == 0) {
            for (int k = 0; k < nr; ++k) t[0][rem[k]] = 0;
            for (int k = 0; k < na; ++k) t[0][add[k]] = 1;
        } else if (mode == 2) {
            for (int k = 0; k < nr; ++k) t[rem[k]][0] = 0;
            for (int k = 0; k < na; ++k) t[add[k]][0] = 1;
        } else {
            if ((int)t.size() <= cg) t.resize(cg + 1);
            for (int k = 0; k < nr; ++k) {
                eraseFrom(t[cg], rem[k], srtC);
                if (og >= 0) insertInto(t[og], rem[k], srtO);
            }
            for (int k = 0; k < na; ++k) {
                insertInto(t[cg], add[k], srtC);
                if (og >= 0) eraseFrom(t[og], add[k], srtO);
            }
        }
        return t;
    }

    double deltaSynced(const Sol& s, const int* add, int na, const int* rem, int nr) {
        double dp = 0.0;
        for (int k = 0; k < na; ++k) dp += M.profit[add[k]];
        for (int k = 0; k < nr; ++k) dp -= M.profit[rem[k]];
        if (feas && fastOk) {
            for (int i = 0; i < m; ++i) nl[i] = load[i];
            for (int k = 0; k < na; ++k) { const double* wj = w(add[k]); for (int i = 0; i < m; ++i) nl[i] += wj[i]; }
            for (int k = 0; k < nr; ++k) { const double* wj = w(rem[k]); for (int i = 0; i < m; ++i) nl[i] -= wj[i]; }
            bool ok = true;
            for (int i = 0; i < m; ++i) if (nl[i] > M.capacity[i]) { ok = false; break; }
            if (ok) return -dp;
        }
        return M.objective(build(s, add, na, rem, nr)) - obj;
    }
};

static std::vector<int> ratioOrder(const Model& M) {
    int n = M.n, m = M.m;
    std::vector<double> key(n);
    for (int j = 0; j < n; ++j) {
        double d = 0.0;
        for (int i = 0; i < m; ++i) {
            double c = M.capacity[i], wv = M.wcol[(size_t)j * m + i];
            if (c > 0) d += wv / c; else if (wv > 0) d += 1e18;
        }
        key[j] = d > 0 ? M.profit[j] / d : std::numeric_limits<double>::infinity();
    }
    std::vector<int> ord(n);
    std::iota(ord.begin(), ord.end(), 0);
    std::stable_sort(ord.begin(), ord.end(), [&](int a, int b) { return key[a] > key[b]; });
    return ord;
}

// mv[0]: 0 = swap (sale mv[1], entra mv[2]); 1 = agregar mv[1]; 2 = quitar mv[1]
class FeasibleSwapNeighborhood : public hsf::Neighborhood<Model> {
    const Model& M;
    MkpCore core;
    std::vector<int> order, cand;
    std::vector<double> slack;
    int candLimit;
    int addBuf[1], remBuf[1];

    void decode(const Move& mv, int& na, int& nr) {
        na = nr = 0;
        if (mv[0] == 0) { remBuf[0] = mv[1]; addBuf[0] = mv[2]; na = nr = 1; }
        else if (mv[0] == 1) { addBuf[0] = mv[1]; na = 1; }
        else { remBuf[0] = mv[1]; nr = 1; }
    }

public:
    FeasibleSwapNeighborhood(const Model& mm, int lim)
        : M(mm), core(mm), order(ratioOrder(mm)), slack(mm.m, 0.0), candLimit(lim) {}

    void moves(const Sol& s, std::vector<Move>& out) override {
        core.sync(s);
        const int mm = core.m;
        if (core.feas) {
            for (int i = 0; i < mm; ++i) slack[i] = M.capacity[i] - core.load[i];
            cand.clear();
            for (int j : order) {
                if (core.in[j]) continue;
                cand.push_back(j);
                if (candLimit > 0 && (int)cand.size() >= candLimit) break;
            }
            for (int j : cand) {
                const double* wj = core.w(j);
                bool fit = true;
                for (int i = 0; i < mm; ++i) if (wj[i] > slack[i]) { fit = false; break; }
                if (fit) { Move mv{}; mv[0] = 1; mv[1] = j; out.push_back(mv); }
            }
            for (int r : core.chosenList) {
                const double* wr = core.w(r);
                for (int j : cand) {
                    const double* wj = core.w(j);
                    bool fit = true;
                    for (int i = 0; i < mm; ++i) if (wj[i] - wr[i] > slack[i]) { fit = false; break; }
                    if (fit) { Move mv{}; mv[0] = 0; mv[1] = r; mv[2] = j; out.push_back(mv); }
                }
            }
        }
        if (out.empty()) {
            for (int j : core.freeList) { Move mv{}; mv[0] = 1; mv[1] = j; out.push_back(mv); }
            for (int r : core.chosenList) { Move mv{}; mv[0] = 2; mv[1] = r; out.push_back(mv); }
        }
    }
    Sol apply(const Sol& s, const Move& mv) override {
        core.sync(s);
        int na, nr; decode(mv, na, nr);
        return core.build(s, addBuf, na, remBuf, nr);
    }
    double delta(const Sol& s, const Move& mv) override {
        core.sync(s);
        int na, nr; decode(mv, na, nr);
        return core.deltaSynced(s, addBuf, na, remBuf, nr);
    }
    Move tabu_key(const Move& mv) override {
        Move k{};
        if (mv[0] == 0) { k[0] = 0; k[1] = mv[2]; k[2] = mv[1]; }
        else if (mv[0] == 1) { k[0] = 2; k[1] = mv[1]; }
        else { k[0] = 1; k[1] = mv[1]; }
        return k;
    }
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& mv) override {
        // camino barato (O(m)) cuando el movimiento queda factible; si viola capacidad, el delta exacto
        core.sync(s);
        int na, nr; decode(mv, na, nr);
        return core.deltaSynced(s, addBuf, na, remBuf, nr);
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int lim = (int)params.get("cand_limit", 0.0);
    return std::make_unique<FeasibleSwapNeighborhood>(model, lim);
}
