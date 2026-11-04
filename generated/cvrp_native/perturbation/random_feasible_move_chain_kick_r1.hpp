// COMPONENT: {"name": "random_feasible_move_chain_kick", "slot": "perturbation", "params": {"moves_base": {"type": "int", "range": [1, 10]}, "moves_per_strength": {"type": "float", "range": [0.5, 5.0]}, "w_relocate": {"type": "float", "range": [0.0, 1.0]}, "w_swap": {"type": "float", "range": [0.0, 1.0]}, "w_twoopt_star": {"type": "float", "range": [0.0, 1.0]}, "w_reverse": {"type": "float", "range": [0.0, 1.0]}}}
using Sol = Model::Solution;

static void ensureDistinct(Sol& out, const Sol& s, const Model& m) {
    if (out != s) return;
    for (auto& r : out) if (r.size() >= 2) { int c = r.back(); r.pop_back(); out.push_back({c}); return; }
    for (size_t i = 0; i < out.size(); ++i)
        for (size_t j = i + 1; j < out.size(); ++j)
            if (m.demand[out[i][0]] + m.demand[out[j][0]] <= m.capacity + 1e-9) {
                out[i].push_back(out[j][0]); out.erase(out.begin() + j); return;
            }
    if (out.size() >= 2) std::swap(out[0], out[1]);
}

class MoveChain : public hsf::Perturbation<Model> {
    const Model& m; double base, per, w[4];
    std::vector<double> load;
    double cap() const { return m.capacity + 1e-9; }
public:
    MoveChain(const Model& mm, double b, double p, double a, double sw, double t, double rv) : m(mm), base(b), per(p) {
        w[0] = a; w[1] = sw; w[2] = t; w[3] = rv;
        if (w[0] + w[1] + w[2] + w[3] <= 1e-12) w[0] = w[1] = w[2] = w[3] = 1.0;
    }
    bool relocate(Sol& out, Rng& rng) {
        int R = (int)out.size(); int a = rng.below(R);
        if (out[a].empty()) return false;
        int i = rng.below((int)out[a].size()); int c = out[a][i]; double d = m.demand[c];
        int b = rng.below(R + 1);
        if (b == R) {
            if (out[a].size() < 2) return false;
            out[a].erase(out[a].begin() + i); load[a] -= d; out.push_back({c}); load.push_back(d); return true;
        }
        if (b == a) {
            if (out[a].size() < 2) return false;
            out[a].erase(out[a].begin() + i);
            int p = rng.below((int)out[a].size() + 1);
            if (p == i) p = (p + 1) % ((int)out[a].size() + 1);
            out[a].insert(out[a].begin() + p, c); return true;
        }
        if (load[b] + d > cap()) return false;
        out[a].erase(out[a].begin() + i); load[a] -= d;
        int p = rng.below((int)out[b].size() + 1);
        out[b].insert(out[b].begin() + p, c); load[b] += d; return true;
    }
    bool swapMove(Sol& out, Rng& rng) {
        int R = (int)out.size(); if (R < 2) return false;
        int a = rng.below(R), b = rng.below(R - 1); if (b >= a) ++b;
        if (out[a].empty() || out[b].empty()) return false;
        int i = rng.below((int)out[a].size()), j = rng.below((int)out[b].size());
        int ca = out[a][i], cb = out[b][j];
        double da = m.demand[ca], db = m.demand[cb];
        if (load[a] - da + db > cap() || load[b] - db + da > cap()) return false;
        out[a][i] = cb; out[b][j] = ca; load[a] += db - da; load[b] += da - db; return true;
    }
    bool twoOptStar(Sol& out, Rng& rng) {
        int R = (int)out.size(); if (R < 2) return false;
        int a = rng.below(R), b = rng.below(R - 1); if (b >= a) ++b;
        int i = rng.below((int)out[a].size() + 1), j = rng.below((int)out[b].size() + 1);
        if ((i == 0 && j == 0) || (i == (int)out[a].size() && j == (int)out[b].size())) return false;
        double pa = 0, pb = 0;
        for (int k = 0; k < i; ++k) pa += m.demand[out[a][k]];
        for (int k = 0; k < j; ++k) pb += m.demand[out[b][k]];
        double na = pa + (load[b] - pb), nb = pb + (load[a] - pa);
        if (na > cap() || nb > cap()) return false;
        std::vector<int> A(out[a].begin(), out[a].begin() + i), B(out[b].begin(), out[b].begin() + j);
        A.insert(A.end(), out[b].begin() + j, out[b].end());
        B.insert(B.end(), out[a].begin() + i, out[a].end());
        out[a].swap(A); out[b].swap(B); load[a] = na; load[b] = nb; return true;
    }
    bool reverse(Sol& out, Rng& rng) {
        int a = rng.below((int)out.size()); int L = (int)out[a].size();
        if (L < 2) return false;
        int i = rng.below(L), j = rng.below(L - 1); if (j >= i) ++j;
        if (i > j) std::swap(i, j);
        std::reverse(out[a].begin() + i, out[a].begin() + j + 1); return true;
    }
    Sol perturb(const Sol& s, double strength, Rng& rng) override {
        Sol out; out.reserve(s.size() + 4);
        for (const auto& r : s) if (!r.empty()) out.push_back(r);
        if (out.empty()) return s;
        load.assign(out.size(), 0.0);
        for (size_t r = 0; r < out.size(); ++r) for (int c : out[r]) load[r] += m.demand[c];
        int moves = std::max(1, (int)std::lround(base + per * std::max(0.0, strength - 1.0)));
        double tot = w[0] + w[1] + w[2] + w[3];
        int done = 0, tries = 0, maxTries = moves * 30;
        while (done < moves && tries < maxTries) {
            ++tries;
            double u = rng.uniform() * tot; bool ok;
            if (u < w[0]) ok = relocate(out, rng);
            else if (u < w[0] + w[1]) ok = swapMove(out, rng);
            else if (u < w[0] + w[1] + w[2]) ok = twoOptStar(out, rng);
            else ok = reverse(out, rng);
            if (ok) {
                ++done;
                for (size_t r = 0; r < out.size();) {
                    if (out[r].empty()) { out.erase(out.begin() + r); load.erase(load.begin() + r); } else ++r;
                }
                if (out.empty()) break;
            }
        }
        ensureDistinct(out, s, m);
        return out;
    }
};

std::unique_ptr<hsf::Perturbation<Model>> make_component(const Model& model, const hsf::Config& params) {
    return std::make_unique<MoveChain>(model, params.get("moves_base", 3), params.get("moves_per_strength", 1.5),
        params.get("w_relocate", 0.4), params.get("w_swap", 0.3), params.get("w_twoopt_star", 0.2), params.get("w_reverse", 0.1));
}
