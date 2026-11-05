// COMPONENT: {"name": "setup_flip_toggle", "slot": "neighborhood", "params": {"use_estimate": {"type": "int", "range": [0, 1]}, "max_offset": {"type": "int", "range": [0, 2]}}}
using Sol = Model::Solution;

struct FlipEval {
    const Model& M;
    Sol base, work;
    double obj = 0.0;
    bool has = false;
    explicit FlipEval(const Model& m) : M(m) {}
    double baseObj(const Sol& s) {
        if (!has || s != base) { base = s; work = s; obj = M.objective(s); has = true; }
        return obj;
    }
};

// Flip conjunto de dos setups en productos distintos: (i,t) y (j,u), i<j, |u-t| <= offset.
// Cambia dos productos a la vez (coordinación entre ítems), algo que los movimientos
// de un solo producto no alcanzan.
class SetupFlipToggle : public hsf::Neighborhood<Model> {
public:
    SetupFlipToggle(const Model& m, bool est, int off) : M(m), useEst(est), offset(off), ev(m) {
        for (int i = 0; i < M.n; ++i)
            for (int j = i + 1; j < M.n; ++j)
                for (int t = 0; t < M.T; ++t) {
                    int lo = std::max(0, t - offset), hi = std::min(M.T - 1, t + offset);
                    for (int u = lo; u <= hi; ++u) {
                        Move mv{}; mv[0] = i; mv[1] = t; mv[2] = j; mv[3] = u;
                        cache.push_back(mv);
                    }
                }
    }

    void moves(const Sol& s, std::vector<Move>& out) override {
        out.insert(out.end(), cache.begin(), cache.end());
        (void)s;
    }

    void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) override {
        out.clear();
        int total = (int)cache.size();
        if (k < 0 || k >= total) { moves(s, out); return; }
        out.reserve(k);
        if ((long long)k * 2 <= total) {
            picked.clear();
            while ((int)out.size() < k) {
                int idx = rng.below(total);
                if (picked.insert(idx).second) out.push_back(cache[idx]);
            }
        } else {
            idxs.resize(total);
            for (int q = 0; q < total; ++q) idxs[q] = q;
            for (int q = 0; q < k; ++q) {
                std::swap(idxs[q], idxs[q + rng.below(total - q)]);
                out.push_back(cache[idxs[q]]);
            }
        }
    }

    Sol apply(const Sol& s, const Move& m) override {
        Sol r = s;
        r[m[0]][m[1]] = s[m[0]][m[1]] ? 0 : 1;
        r[m[2]][m[3]] = s[m[2]][m[3]] ? 0 : 1;
        return r;
    }

    double delta(const Sol& s, const Move& m) override {
        double b = ev.baseObj(s);
        int i = m[0], t = m[1], j = m[2], u = m[3];
        int o1 = ev.work[i][t], o2 = ev.work[j][u];
        ev.work[i][t] = o1 ? 0 : 1;
        ev.work[j][u] = o2 ? 0 : 1;
        double a = M.objective(ev.work);
        ev.work[i][t] = o1;
        ev.work[j][u] = o2;
        return a - b;
    }

    bool has_estimate() const override { return useEst; }

    double estimate(const Sol& s, const Move& m) override {
        return singleEstimate(s, m[0], m[1]) + singleEstimate(s, m[2], m[3]);
    }

private:
    double singleExact(const Sol& s, int i, int t) {
        double b = ev.baseObj(s);
        int old = ev.work[i][t];
        ev.work[i][t] = old ? 0 : 1;
        double a = M.objective(ev.work);
        ev.work[i][t] = old;
        return a - b;
    }

    double singleEstimate(const Sol& s, int i, int t) {
        const std::vector<int>& y = s[i];
        int p = -1;
        for (int u = t - 1; u >= 0; --u) if (y[u]) { p = u; break; }
        // Sin setup previo la demanda descubierta se penaliza de forma que la fórmula
        // barata no captura: ahí se usa el delta exacto del flip individual.
        if (p < 0) return singleExact(s, i, t);
        double D = 0.0;
        for (int u = t; u < M.T; ++u) {
            if (u > t && y[u]) break;
            D += M.d[i][u];
        }
        double shift = M.h[i] * (t - p) * D;
        if (y[t]) return -M.s[i] + shift;
        return M.s[i] - shift;
    }

    const Model& M;
    bool useEst;
    int offset;
    FlipEval ev;
    std::vector<Move> cache;
    std::unordered_set<int> picked;
    std::vector<int> idxs;
};

std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const hsf::Config& params) {
    bool est = params.get("use_estimate", 1.0) >= 0.5;
    int off = (int)std::lround(params.get("max_offset", 1.0));
    off = std::max(0, std::min(2, off));
    return std::make_unique<SetupFlipToggle>(model, est, off);
}
