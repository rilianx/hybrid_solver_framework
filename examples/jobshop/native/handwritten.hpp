// El catálogo escrito a mano del job shop en C++ (el de `components.py`) y sus helpers: camino crítico,
// bloques y cabezas/colas. No lo ve el LLM que genera componentes (ve solo `model.hpp`).
#pragma once

#include "model.hpp"

namespace jobshop {

// camino crítico (como `model_parts.critical_path`): operaciones (j, k) en orden
inline std::vector<std::pair<int, int>> critical_path(const JobShop& js, const JobShop::Solution& sol, const std::vector<int>& start) {
    std::vector<int> pos(js.n * js.m, -1);
    for (int mm = 0; mm < (int)sol.size() && mm < js.m; ++mm)
        for (int i = (int)sol[mm].size() - 1; i >= 0; --i) {
            int j = sol[mm][i];
            if (j >= 0 && j < js.n) pos[mm * js.n + j] = i;
        }
    int j = 0, best = -1;
    for (int jj = 0; jj < js.n; ++jj) {
        int last = js.off[jj + 1] - 1, e = start[last] + js.routes[jj].back().second;
        if (e > best) best = e, j = jj;
    }
    std::vector<std::pair<int, int>> path{{j, (int)js.routes[j].size() - 1}};
    while (true) {
        auto [jj, k] = path.back();
        int s = start[js.off[jj] + k];
        if (s <= 0) break;
        int mm = js.routes[jj][k].first, i = pos[mm * js.n + jj];
        if (i > 0) {
            int pj = sol[mm][i - 1];
            int pk = (pj >= 0 && pj < js.n) ? js.opk[pj][mm] : -1;
            if (pk >= 0 && start[js.off[pj] + pk] + js.routes[pj][pk].second == s) {
                path.push_back({pj, pk});
                continue;
            }
        }
        if (k > 0 && start[js.off[jj] + k - 1] + js.routes[jj][k - 1].second == s) {
            path.push_back({jj, k - 1});
            continue;
        }
        break;
    }
    std::reverse(path.begin(), path.end());
    return path;
}

// bloques del camino crítico: (máquina, trabajos consecutivos), de 2 o más
inline std::vector<std::pair<int, std::vector<int>>> critical_blocks(const JobShop& js, const JobShop::Solution& sol) {
    int mk;
    std::vector<int> start;
    js.schedule(sol, start, mk);
    std::vector<std::pair<int, std::vector<int>>> blocks;
    for (auto [j, k] : critical_path(js, sol, start)) {
        int mm = js.routes[j][k].first;
        if (!blocks.empty() && blocks.back().first == mm) blocks.back().second.push_back(j);
        else blocks.push_back({mm, {j}});
    }
    std::vector<std::pair<int, std::vector<int>>> out;
    for (auto& b : blocks) if (b.second.size() > 1) out.push_back(b);
    return out;
}


// ------------------------------------------------------------------ catálogo escrito a mano
using M = JobShop;
using Sol = M::Solution;

struct JobOrder : hsf::Constructor<M> {
    const M& js;
    explicit JobOrder(const M& m) : js(m) {}
    Sol build(Rng&) override { return js.trivial(); }
};

struct EarliestEnd : hsf::GreedyScore<M> {
    double score(const M::Partial&, const M::Action& a) override { return a.end + 1e-3 * a.start; }
};

struct MostWorkRemaining : hsf::GreedyScore<M> {
    std::vector<std::vector<int>> rest;
    double scale;
    explicit MostWorkRemaining(const M& js) : rest(js.n), scale(1.0 + js.horizon) {
        for (int j = 0; j < js.n; ++j) {
            int r = 0;
            rest[j].resize(js.routes[j].size());
            for (int k = (int)js.routes[j].size() - 1; k >= 0; --k) rest[j][k] = (r += js.routes[j][k].second);
        }
    }
    double score(const M::Partial&, const M::Action& a) override { return a.start - rest[a.job][a.op] / scale; }
};

inline int index_of(const std::vector<int>& v, int x) { return (int)(std::find(v.begin(), v.end(), x) - v.begin()); }

inline Sol swap_jobs(const Sol& s, int mm, int a, int b) {
    Sol t = s;
    std::swap(t[mm][index_of(t[mm], a)], t[mm][index_of(t[mm], b)]);
    return t;
}

// Cabezas (inicio más temprano) y colas (camino más largo desde el fin de la operación hasta el final) del
// plan semiactivo, y los vecinos de cada operación en su máquina: lo que usan las estimaciones de movimientos.
struct HeadsTails {
    M::Solution sol;
    std::vector<int> r, q, mprev, mnext;
    int makespan = 0;
    bool valid = false;

    void compute(const M& js, const M::Solution& s) {
        if (valid && s == sol) return;
        sol = s;
        js.schedule(s, r, makespan);
        mprev.assign(js.n_ops, -1), mnext.assign(js.n_ops, -1);
        for (int mm = 0; mm < js.m && mm < (int)s.size(); ++mm)
            for (size_t i = 0; i + 1 < s[mm].size(); ++i) {
                int a = s[mm][i], b = s[mm][i + 1];
                if (a < 0 || a >= js.n || b < 0 || b >= js.n || js.opk[a][mm] < 0 || js.opk[b][mm] < 0) continue;
                int oa = js.off[a] + js.opk[a][mm], ob = js.off[b] + js.opk[b][mm];
                mnext[oa] = ob, mprev[ob] = oa;
            }
        // colas: en orden de inicio decreciente (un orden topológico inverso, porque todo tiempo es >= 1)
        std::vector<int> ops(js.n_ops);
        for (int i = 0; i < js.n_ops; ++i) ops[i] = i;
        std::sort(ops.begin(), ops.end(), [&](int a, int b) { return r[a] > r[b]; });
        q.assign(js.n_ops, 0);
        for (int op : ops) {
            int j = js.job_of[op], k = op - js.off[j], t = 0;
            if (k + 1 < (int)js.routes[j].size()) t = std::max(t, q[op + 1] + js.routes[j][k + 1].second);
            if (mnext[op] >= 0) t = std::max(t, q[mnext[op]] + p(js, mnext[op]));
            q[op] = t;
        }
        valid = true;
    }
    static int p(const M& js, int op) { int j = js.job_of[op]; return js.routes[j][op - js.off[j]].second; }
    int end(const M& js, int op) const { return op < 0 ? 0 : r[op] + p(js, op); }
    int qp(const M& js, int op) const { return op < 0 ? 0 : q[op] + p(js, op); }
    int jprev(const M& js, int op) const { return op > js.off[js.job_of[op]] ? op - 1 : -1; }
    int jnext(const M& js, int op) const { return op + 1 < js.off[js.job_of[op] + 1] ? op + 1 : -1; }

    // makespan estimado tras intercambiar u y v, consecutivas en su máquina (u antes que v): Taillard (1994)
    double swap_estimate(const M& js, int u, int v) const {
        int rv = std::max(end(js, jprev(js, v)), end(js, mprev[u]));
        int ru = std::max(end(js, jprev(js, u)), rv + p(js, v));
        int qu = std::max(qp(js, jnext(js, u)), qp(js, mnext[v]));
        int qv = std::max(qp(js, jnext(js, v)), qu + p(js, u));
        return std::max(rv + p(js, v) + qv, ru + p(js, u) + qu);
    }
};

// N5: intercambiar las dos primeras o las dos últimas operaciones de cada bloque crítico. Movimiento (m, a, b).
// Estimación: el makespan de los caminos que pasan por las dos operaciones intercambiadas (cabezas y colas).
struct CriticalSwap : hsf::Neighborhood<M> {
    const M& js;
    HeadsTails ht;
    explicit CriticalSwap(const M& m) : js(m) {}
    bool has_estimate() const override { return true; }
    double estimate(const Sol& s, const Move& mv) override {
        ht.compute(js, s);
        int mm = mv[0], u = js.off[mv[1]] + js.opk[mv[1]][mm], v = js.off[mv[2]] + js.opk[mv[2]][mm];
        if (ht.mnext[u] != v) return delta(s, mv);  // no consecutivas: sin fórmula, el exacto
        return ht.swap_estimate(js, u, v) - ht.makespan;
    }
    void moves(const Sol& s, std::vector<Move>& out) override {
        std::set<Move> seen;
        for (auto& [mm, b] : critical_blocks(js, s)) {
            Move p1{mm, b[0], b[1], 0, 0, 0}, p2{mm, b[b.size() - 2], b.back(), 0, 0, 0};
            for (auto& p : {p1, p2}) if (seen.insert(p).second) out.push_back(p);
        }
    }
    Sol apply(const Sol& s, const Move& mv) override { return swap_jobs(s, mv[0], mv[1], mv[2]); }
    double delta(const Sol& s, const Move& mv) override { return js.objective(apply(s, mv)) - js.objective(s); }
    Move tabu_key(const Move& mv) override { return {mv[0], mv[2], mv[1], 0, 0, 0}; }  // el que lo deshace
};

// Mover un trabajo de un bloque crítico al principio o al final del bloque. Movimiento (m, trabajo, desde, hasta).
struct CriticalInsert : hsf::Neighborhood<M> {
    const M& js;
    explicit CriticalInsert(const M& m) : js(m) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (auto& [mm, b] : critical_blocks(js, s)) {
            int first = index_of(s[mm], b[0]), last = first + (int)b.size() - 1;
            for (int i = first; i <= last; ++i)
                for (int to : {first, last})
                    if (to != i && std::abs(to - i) > 1) out.push_back({mm, s[mm][i], i, to, 0, 0});
        }
    }
    static Sol move_to(const Sol& s, int mm, int job, int to) {
        Sol t = s;
        auto& v = t[mm];
        v.erase(v.begin() + index_of(v, job));
        v.insert(v.begin() + to, job);
        return t;
    }
    Sol apply(const Sol& s, const Move& mv) override { return move_to(s, mv[0], mv[1], mv[3]); }
    double delta(const Sol& s, const Move& mv) override { return js.objective(apply(s, mv)) - js.objective(s); }
    Move tabu_key(const Move& mv) override { return {mv[0], mv[1], mv[3], mv[2], 0, 0}; }
};

struct CriticalKick : hsf::Perturbation<M> {
    const M& js;
    explicit CriticalKick(const M& m) : js(m) {}
    Sol perturb(const Sol& s0, double strength, Rng& rng) override {
        Sol s = s0;
        int times = std::max(1, (int)std::lround(strength));
        std::vector<int> st;
        int mk;
        for (int t = 0; t < times; ++t) {
            js.schedule(s, st, mk);
            auto path = critical_path(js, s, st);
            std::vector<Move> pairs;
            for (size_t i = 0; i + 1 < path.size(); ++i) {
                int ma = js.routes[path[i].first][path[i].second].first;
                int mb = js.routes[path[i + 1].first][path[i + 1].second].first;
                if (ma == mb) pairs.push_back({ma, path[i].first, path[i + 1].first, 0, 0, 0});
            }
            if (pairs.empty()) break;
            auto& p = pairs[rng.below((int)pairs.size())];
            s = swap_jobs(s, p[0], p[1], p[2]);
        }
        return s;
    }
};

inline hsf::Catalog<M> handwritten() {
    hsf::Catalog<M> c;
    c.constructors["job_order"] = [](const M& m, const hsf::Config&) { return std::make_unique<JobOrder>(m); };
    c.scores["earliest_end"] = [](const M&, const hsf::Config&) { return std::make_unique<EarliestEnd>(); };
    c.scores["most_work_remaining"] = [](const M& m, const hsf::Config&) { return std::make_unique<MostWorkRemaining>(m); };
    c.neighborhoods["critical_swap"] = [](const M& m, const hsf::Config&) { return std::make_unique<CriticalSwap>(m); };
    c.neighborhoods["critical_insert"] = [](const M& m, const hsf::Config&) { return std::make_unique<CriticalInsert>(m); };
    c.perturbations["critical_kick"] = [](const M& m, const hsf::Config&) { return std::make_unique<CriticalKick>(m); };
    return c;
}

}  // namespace jobshop
