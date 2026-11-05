// COMPONENT: {"name": "setup_shift_relink", "slot": "relink", "params": {"p_nearest": {"type": "float", "range": [0.0, 1.0]}}}
class SetupShiftRelink : public hsf::Relink<Model> {
public:
    using S = Model::Solution;
    SetupShiftRelink(const Model& m, double p) : m_(m), pNear_(p) {}

    static int itemDist(const std::vector<int>& a, const std::vector<int>& b) {
        int nA = 0, nB = 0, nC = 0;
        const size_t T = std::min(a.size(), b.size());
        for (size_t t = 0; t < T; ++t) {
            if (a[t] == b[t]) continue;
            if (b[t] == 0) ++nA;
            else if (a[t] == 0) ++nB;
            else ++nC;
        }
        return std::max(nA, nB) + nC;
    }

    int distance(const S& a, const S& b) override {
        int d = 0;
        const size_t n = std::min(a.size(), b.size());
        for (size_t i = 0; i < n; ++i) d += itemDist(a[i], b[i]);
        return d;
    }

    S step(const S& cur, const S& guide, Rng& rng) override {
        items_.clear();
        const size_t n = std::min(cur.size(), guide.size());
        for (size_t i = 0; i < n; ++i)
            if (itemDist(cur[i], guide[i]) > 0) items_.push_back((int)i);
        S out = cur;
        if (items_.empty()) return out;
        const int i = items_[rng.below((int)items_.size())];
        const auto& c = cur[i];
        const auto& g = guide[i];
        A_.clear(); B_.clear(); C_.clear();
        const size_t T = std::min(c.size(), g.size());
        for (size_t t = 0; t < T; ++t) {
            if (c[t] == g[t]) continue;
            if (g[t] == 0) A_.push_back((int)t);
            else if (c[t] == 0) B_.push_back((int)t);
            else C_.push_back((int)t);
        }
        // tipos de paso disponibles: 0=mover, 1=quitar sobrante, 2=añadir faltante, 3=corregir C
        int kinds[4], nk = 0;
        if (!A_.empty() && !B_.empty()) kinds[nk++] = 0;
        if (A_.size() > B_.size()) kinds[nk++] = 1;
        if (B_.size() > A_.size()) kinds[nk++] = 2;
        if (!C_.empty()) kinds[nk++] = 3;
        if (nk == 0) return out; // no ocurre: itemDist > 0
        const int kind = kinds[rng.below(nk)];
        auto& row = out[i];
        if (kind == 0) {
            const int a = A_[rng.below((int)A_.size())];
            int b;
            if (rng.uniform() < pNear_) {
                b = B_[0];
                int best = std::abs(b - a);
                int ties = 1;
                for (size_t j = 1; j < B_.size(); ++j) {
                    int dd = std::abs(B_[j] - a);
                    if (dd < best) { best = dd; b = B_[j]; ties = 1; }
                    else if (dd == best && rng.below(++ties) == 0) b = B_[j];
                }
            } else {
                b = B_[rng.below((int)B_.size())];
            }
            row[a] = g[a];
            row[b] = g[b];
        } else if (kind == 1) {
            const int a = A_[rng.below((int)A_.size())];
            row[a] = g[a];
        } else if (kind == 2) {
            const int b = B_[rng.below((int)B_.size())];
            row[b] = g[b];
        } else {
            const int t = C_[rng.below((int)C_.size())];
            row[t] = g[t];
        }
        return out;
    }

private:
    const Model& m_;
    double pNear_;
    std::vector<int> items_, A_, B_, C_;
};

std::unique_ptr<hsf::Relink<Model>> make_component(const Model& model, const hsf::Config& params) {
    double p = params.get("p_nearest", 0.6);
    p = std::min(1.0, std::max(0.0, p));
    return std::make_unique<SetupShiftRelink>(model, p);
}
