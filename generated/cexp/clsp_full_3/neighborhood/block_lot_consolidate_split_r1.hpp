// COMPONENT: {"name": "block_lot_consolidate_split", "slot": "neighborhood", "params": {"max_len": {"type": "int", "range": [2, 8]}}}
using Sol = Model::Solution;

struct BlockEval {
    const Model& M;
    Sol base, work;
    double obj = 0.0;
    bool has = false;
    explicit BlockEval(const Model& m) : M(m) {}
    double baseObj(const Sol& s) {
        if (!has || s != base) { base = s; work = s; obj = M.objective(s); has = true; }
        return obj;
    }
};

class BlockLotRewrite : public hsf::Neighborhood<Model> {
public:
    BlockLotRewrite(const Model& m, int L) : M(m), Lmax(L), ev(m) { saved.reserve(16); }

    static inline int target(int a, int u, int mode) {
        if (mode == 1) return 1;
        return u == a ? 1 : 0;
    }

    bool changes(const std::vector<int>& y, int a, int L, int mode) const {
        for (int u = a; u < a + L; ++u)
            if ((y[u] != 0 ? 1 : 0) != target(a, u, mode) || (y[u] != 0 && y[u] != 1)) return true;
        return false;
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        for (int i = 0; i < M.n; ++i) {
            const std::vector<int>& y = s[i];
            for (int a = 0; a < M.T; ++a)
                for (int L = 2; L <= Lmax && a + L <= M.T; ++L)
                    for (int mode = 0; mode < 2; ++mode) {
                        if (!changes(y, a, L, mode)) continue;
                        Move mv{}; mv[0] = i; mv[1] = a; mv[2] = L; mv[3] = mode;
                        out.push_back(mv);
                    }
        }
        if (out.empty()) {
            // horizonte de 1 período: abrir/cerrar el setup como fallback
            for (int i = 0; i < M.n; ++i) {
                Move mv{}; mv[0] = i; mv[1] = 0; mv[2] = 1; mv[3] = s[i][0] ? 2 : 1;
                out.push_back(mv);
            }
        }
    }

    void rewrite(std::vector<int>& y, const Move& m) const {
        int a = m[1], L = m[2], mode = m[3];
        if (mode == 2) { for (int u = a; u < a + L; ++u) y[u] = 0; return; }
        for (int u = a; u < a + L; ++u) y[u] = target(a, u, mode);
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        rewrite(r[m[0]], m);
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = ev.baseObj(s);
        std::vector<int>& y = ev.work[m[0]];
        int a = m[1], L = m[2];
        saved.assign(y.begin() + a, y.begin() + a + L);
        rewrite(y, m);
        double r = M.objective(ev.work);
        std::copy(saved.begin(), saved.end(), y.begin() + a);
        return r - b;
    }

    Move tabu_key(const Move& m) override {
        Move k = m;
        if (m[3] == 0) k[3] = 1;
        else if (m[3] == 1) k[3] = 0;
        else k[3] = 1;
        return k;
    }

private:
    const Model& M;
    int Lmax;
    BlockEval ev;
    std::vector<int> saved;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    int L = (int)std::lround(params.get("max_len", 4.0));
    L = std::max(2, std::min(8, L));
    return std::make_unique<BlockLotRewrite>(model, L);
}
