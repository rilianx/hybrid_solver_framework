// COMPONENT: {"name": "item_window_lot_replan", "slot": "perturbation", "params": {"win_scale": {"type": "float", "range": [1.0, 4.0]}, "items_hit": {"type": "int", "range": [1, 4]}, "mode": {"type": "cat", "values": ["merge", "random", "mixed"]}, "max_tries": {"type": "int", "range": [3, 30]}}}
using Sol = Model::Solution;

static Sol fallbackPerturbB(const Model& m, const Sol& s, Rng& rng) {
    int n = (int)s.size(), T = n ? (int)s[0].size() : 0, N = n * T;
    if (N > 0) {
        Sol c = s;
        int off = rng.below(N);
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            int old = c[i][t];
            c[i][t] = old ? 0 : 1;
            if (m.feasible(c)) return c;
            c[i][t] = old;
        }
        for (int k = 0; k < N; ++k) {
            int idx = (off + k) % N, i = idx / T, t = idx % T;
            if (t + 1 < T && c[i][t] != c[i][t + 1]) {
                std::swap(c[i][t], c[i][t + 1]);
                if (m.feasible(c)) return c;
                std::swap(c[i][t], c[i][t + 1]);
            }
        }
    }
    Sol tr = m.trivial();
    if (tr != s && m.feasible(tr)) return tr;
    if (N > 0) { Sol c = s; c[0][0] = c[0][0] ? 0 : 1; return c; }
    return s;
}

class ItemWindowLotReplan : public hsf::Perturbation<Model> {
public:
    ItemWindowLotReplan(const Model& m, double ws, int ih, int mode, int mt)
        : m_(m), winScale_(ws), itemsHit_(std::max(1, ih)), mode_(mode), maxTries_(std::max(1, mt)) {}

    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        int n = (int)s.size(), T = n ? (int)s[0].size() : 0;
        if (n == 0 || T == 0) return s;
        double str = std::max(1.0, strength);
        int L = std::min(T, std::max(2, (int)std::ceil(str * winScale_) + 1));
        int hits = std::min(n, itemsHit_);
        for (int tr = 0; tr < maxTries_; ++tr) {
            Sol c = s;
            for (int h = 0; h < hits; ++h) {
                int i = rng.below(n);
                int a = rng.below(T - L + 1), b = a + L - 1;
                int md = mode_ == 2 ? rng.below(2) : mode_;
                std::vector<int>& row = c[i];
                if (md == 0) {
                    int first = -1;
                    for (int t = a; t <= b; ++t)
                        if (dem(i, t) > Model::EPS) { first = t; break; }
                    bool same = true;
                    for (int t = a; t <= b; ++t) {
                        int want = (t == first) ? 1 : 0;
                        if (row[t] != want) same = false;
                        row[t] = want;
                    }
                    if (same) {
                        // already merged: split the lot instead
                        int lo = (first >= 0 ? first + 1 : a);
                        if (lo <= b) row[lo + rng.below(b - lo + 1)] = 1;
                        else row[a + rng.below(L)] ^= 1;
                    }
                } else {
                    int cnt = 0;
                    for (int t = 0; t < T; ++t) cnt += s[i][t] ? 1 : 0;
                    double p = std::min(0.85, std::max(0.15, (double)cnt / T));
                    bool changed = false;
                    for (int t = a; t <= b; ++t) {
                        int v = rng.uniform() < p ? 1 : 0;
                        if (v != row[t]) changed = true;
                        row[t] = v;
                    }
                    if (!changed) { int t = a + rng.below(L); row[t] = row[t] ? 0 : 1; }
                }
            }
            if (c != s && m_.feasible(c)) return c;
        }
        return fallbackPerturbB(m_, s, rng);
    }

private:
    double dem(int i, int t) const {
        if (i < (int)m_.d.size() && t < (int)m_.d[i].size()) return m_.d[i][t];
        return 0.0;
    }
    const Model& m_;
    double winScale_;
    int itemsHit_, mode_, maxTries_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    std::string md = params.text("mode", "mixed");
    int mode = md == "merge" ? 0 : (md == "random" ? 1 : 2);
    return std::make_unique<ItemWindowLotReplan>(model, params.get("win_scale", 2.0),
        (int)params.get("items_hit", 1), mode, (int)params.get("max_tries", 10));
}
