// COMPONENT: {"name": "random_multi_insertion", "slot": "perturbation", "params": {"scale": {"type": "float", "range": [0.5, 3.0]}, "extra": {"type": "int", "range": [0, 3]}}}
class RandomMultiInsertion : public hsf::Perturbation<Model> {
public:
    RandomMultiInsertion(const Model& m, double scale, int extra) : md(m), scale_(scale), extra_(extra) {}
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out = s;
        int R = (int)out.size();
        if (R == 0) return out;
        int total = 0;
        for (int r = 0; r < R; ++r) total += (int)out[r].size();
        if (total == 0) return out;
        if (R == 1 && total < 2) return out;
        int k = std::max(1, (int)std::lround(scale_ * std::max(1.0, strength)) + extra_);
        for (int t = 0; t < k; ++t) {
            // elegir un elemento uniforme entre todas las secuencias
            int idx = rng.below(total), src = 0;
            while (idx >= (int)out[src].size()) { idx -= (int)out[src].size(); ++src; }
            auto x = out[src][idx];
            out[src].erase(out[src].begin() + idx);
            int dst = rng.below(R);
            int L = (int)out[dst].size();
            int pos = rng.below(L + 1);
            if (dst == src && pos == idx && L > 0) pos = (pos + 1 + rng.below(L)) % (L + 1);
            out[dst].insert(out[dst].begin() + pos, x);
        }
        if (out == s) {
            // forzar un cambio: mover un elemento a otra posición/secuencia
            int idx = rng.below(total), src = 0;
            while (idx >= (int)out[src].size()) { idx -= (int)out[src].size(); ++src; }
            auto x = out[src][idx];
            out[src].erase(out[src].begin() + idx);
            int dst = R > 1 ? (src + 1 + rng.below(R - 1)) % R : src;
            int L = (int)out[dst].size();
            int pos = (dst == src && L > 0) ? (idx + 1) % (L + 1) : rng.below(L + 1);
            out[dst].insert(out[dst].begin() + pos, x);
        }
        return out;
    }
private:
    const Model& md;
    double scale_;
    int extra_;
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    double scale = params.get("scale", 1.0);
    int extra = (int)params.get("extra", 0);
    return std::make_unique<RandomMultiInsertion>(model, scale, extra);
}
