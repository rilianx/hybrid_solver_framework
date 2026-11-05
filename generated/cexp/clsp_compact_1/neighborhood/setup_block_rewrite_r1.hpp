// COMPONENT: {"name": "setup_block_rewrite", "slot": "neighborhood", "params": {"block_len": {"type": "int", "range": [2, 5]}, "min_hamming": {"type": "int", "range": [2, 3]}}}
class SetupBlockRewrite : public hsf::Neighborhood<Model> {
public:
    using Sol = Model::Solution;
    SetupBlockRewrite(const Model& m, int L, int h) : M(m), Lp(std::max(1, L)), H(std::max(1, h)) {}

    // m = {i, t, L, newmask, oldmask}
    void moves(const Sol& s, std::vector<Move>& out) override {
        int n = (int)s.size();
        for (int i = 0; i < n; ++i) {
            int T = (int)s[i].size();
            if (T == 0) continue;
            int L = std::min(Lp, T);
            int h = std::min(H, L);
            int full = 1 << L;
            for (int t = 0; t + L <= T; ++t) {
                int old = 0;
                for (int k = 0; k < L; ++k) if (s[i][t + k]) old |= (1 << k);
                for (int nm = 0; nm < full; ++nm) {
                    if (nm == old) continue;
                    if (popc(nm ^ old) < h) continue;
                    out.push_back(Move{i, t, L, nm, old, 0, 0});
                }
            }
        }
        if (out.empty()) {
            for (int i = 0; i < n; ++i)
                for (int t = 0; t < (int)s[i].size(); ++t) {
                    int old = s[i][t] ? 1 : 0;
                    out.push_back(Move{i, t, 1, 1 - old, old, 0, 0});
                }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        modify(r, m);
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double base = baseObj(s);
        work = s;
        modify(work, m);
        return M.objective(work) - base;
    }

    Move tabu_key(const Move& m) override { return Move{m[0], m[1], m[2], m[4], m[3], 0, 0}; }

private:
    const Model& M;
    int Lp, H;
    Sol work, cached;
    double cachedVal = 0.0;
    bool cacheValid = false;

    static int popc(int x) { int c = 0; while (x) { x &= x - 1; ++c; } return c; }

    static void modify(Sol& r, const Move& m) {
        int i = m[0], t = m[1], L = m[2], nm = m[3];
        for (int k = 0; k < L; ++k) r[i][t + k] = (nm >> k) & 1;
    }

    double baseObj(const Sol& s) {
        if (cacheValid && s == cached) return cachedVal;
        cachedVal = M.objective(s);
        cached = s;
        cacheValid = true;
        return cachedVal;
    }
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)params.get("block_len", 3);
    int h = (int)params.get("min_hamming", 2);
    return std::unique_ptr<hsf::Neighborhood<Model>>(new SetupBlockRewrite(model, L, h));
}
