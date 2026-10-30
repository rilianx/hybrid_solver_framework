// El job shop (makespan) en C++: la vista heurística y constructiva de `model_parts.py` (secuencia por
// máquina, plan semiactivo) y el catálogo escrito a mano de `components.py`. Mismas familias, mismo
// costo y misma penalización que `PartsModel(model_parts, inst)`, así que el validador de Python lo
// prueba con los mismos casos.
#pragma once

#include <hsf/core.hpp>

#include <set>
#include <sstream>

namespace jobshop {

using hsf::Move;
using hsf::Rng;

struct JobShop {
    using Solution = std::vector<std::vector<int>>;  // seqs[m] = trabajos en el orden de la máquina m

    struct Partial {
        std::vector<std::vector<int>> seqs;
        std::vector<int> nxt, job_ready, mach_ready, order;
    };
    struct Action {
        int job, op, machine, start, end;
    };

    int n = 0, m = 0;
    std::vector<std::vector<std::pair<int, int>>> routes;  // routes[j][k] = (máquina, tiempo)
    std::vector<int> off;                                   // id de la operación (j, k) = off[j] + k
    std::vector<std::vector<int>> opk;                      // opk[j][máquina] = k, o -1
    int n_ops = 0, horizon = 0;
    double penalty = 0.0;

    // memoria de trabajo de `schedule` (un modelo por hilo)
    std::vector<int> job_of;                                // job_of[id] = trabajo de la operación
    mutable std::vector<int> mpred_, msucc_, indeg_, done_, ready_, end_, start_;
    mutable std::vector<char> finished_, seen_;

    static JobShop parse(const std::string& text) {
        std::istringstream in(text);
        JobShop js;
        in >> js.n >> js.m;
        js.routes.resize(js.n);
        std::string line;
        std::getline(in, line);
        for (int j = 0; j < js.n;) {
            if (!std::getline(in, line)) throw std::invalid_argument("faltan líneas de trabajos");
            std::istringstream ls(line);
            int mm, p;
            bool any = false;
            while (ls >> mm >> p) js.routes[j].push_back({mm, p}), any = true;
            if (any) ++j;
        }
        js.init();
        return js;
    }

    void init() {
        off.assign(n + 1, 0);
        opk.assign(n, std::vector<int>(m, -1));
        horizon = 0;
        for (int j = 0; j < n; ++j) {
            off[j + 1] = off[j] + (int)routes[j].size();
            for (int k = 0; k < (int)routes[j].size(); ++k) opk[j][routes[j][k].first] = k, horizon += routes[j][k].second;
        }
        n_ops = off[n];
        job_of.resize(n_ops);
        for (int j = 0; j < n; ++j) for (int op = off[j]; op < off[j + 1]; ++op) job_of[op] = j;
        mpred_.resize(n_ops), msucc_.resize(n_ops), indeg_.resize(n_ops), end_.resize(n_ops), finished_.resize(n_ops);
        done_.resize(n), seen_.resize(n);
        penalty = 10.0 * (makespan(trivial()) + 1.0);
    }

    std::vector<int> jobs_on(int mm) const {
        std::vector<int> out;
        for (int j = 0; j < n; ++j) if (opk[j][mm] >= 0) out.push_back(j);
        return out;
    }

    Solution trivial() const {
        Solution s(m);
        for (int mm = 0; mm < m; ++mm) s[mm] = jobs_on(mm);
        return s;
    }

    Solution random(Rng& rng) const {
        std::vector<int> pending;
        for (int j = 0; j < n; ++j) for (size_t k = 0; k < routes[j].size(); ++k) pending.push_back(j);
        std::shuffle(pending.begin(), pending.end(), rng.g);
        Solution s(m);
        std::vector<int> nxt(n, 0);
        for (int j : pending) s[routes[j][nxt[j]++].first].push_back(j);
        return s;
    }

    // Plan semiactivo (ver `model_parts.schedule`): inicios por operación, makespan y operaciones liberadas
    // (> 0 si y solo si las secuencias forman un ciclo).
    int schedule(const Solution& sol, std::vector<int>& start, int& mk) const {
        std::fill(mpred_.begin(), mpred_.end(), -1);
        std::fill(msucc_.begin(), msucc_.end(), -1);
        for (int mm = 0; mm < m && mm < (int)sol.size(); ++mm) {
            int prev = -1;
            std::fill(seen_.begin(), seen_.end(), 0);
            for (int j : sol[mm]) {
                if (j < 0 || j >= n || seen_[j] || opk[j][mm] < 0) continue;
                seen_[j] = 1;
                int op = off[j] + opk[j][mm];
                if (prev >= 0) mpred_[op] = prev, msucc_[prev] = op;
                prev = op;
            }
        }
        start.assign(n_ops, 0);
        ready_.clear();
        for (int j = 0; j < n; ++j) {
            done_[j] = 0;
            for (int k = 0; k < (int)routes[j].size(); ++k) {
                int op = off[j] + k;
                indeg_[op] = (k > 0) + (mpred_[op] >= 0);
                finished_[op] = 0;
            }
        }
        // mismo orden de despacho que Python: los listos al comienzo ordenados por (j, k), se saca del final
        for (int op = 0; op < n_ops; ++op) if (indeg_[op] == 0) ready_.push_back(op);
        int n_done = 0, released = 0;
        while (n_done < n_ops) {
            if (ready_.empty()) {
                int j = 0;
                while (done_[j] >= (int)routes[j].size()) ++j;
                ready_.push_back(off[j] + done_[j]);
                ++released;
            }
            int op = ready_.back();
            ready_.pop_back();
            if (finished_[op]) continue;
            int j = job_of[op], k = op - off[j];
            int s = k > 0 ? end_[op - 1] : 0;
            if (mpred_[op] >= 0 && finished_[mpred_[op]]) s = std::max(s, end_[mpred_[op]]);
            start[op] = s;
            end_[op] = s + routes[j][k].second;
            finished_[op] = 1;
            ++done_[j];
            ++n_done;
            int nexts[2] = {k + 1 < (int)routes[j].size() ? op + 1 : -1, msucc_[op]};
            for (int nx : nexts)
                if (nx >= 0 && !finished_[nx] && --indeg_[nx] == 0) ready_.push_back(nx);
        }
        mk = 0;
        for (int j = 0; j < n; ++j) if (!routes[j].empty()) mk = std::max(mk, end_[off[j + 1] - 1]);
        return released;
    }

    int makespan(const Solution& s) const {
        int mk;
        schedule(s, start_, mk);
        return mk;
    }

    int sequence_errors(const Solution& sol) const {
        int bad = 0;
        auto& cnt = done_;  // memoria de trabajo (schedule no corre a la vez)
        for (int mm = 0; mm < m; ++mm) {
            std::fill(cnt.begin(), cnt.end(), 0);
            int foreign = 0;
            if (mm < (int)sol.size())
                for (int j : sol[mm]) {
                    if (j >= 0 && j < n && opk[j][mm] >= 0) ++cnt[j];
                    else ++foreign;
                }
            for (int j = 0; j < n; ++j) if (opk[j][mm] >= 0) bad += std::abs(cnt[j] - 1);
            bad += foreign;
        }
        for (size_t mm = m; mm < sol.size(); ++mm) bad += (int)sol[mm].size();
        return bad;
    }

    // {secuencia, orden} y makespan, como `violations` y `cost_terms` de las piezas
    void evaluate(const Solution& s, double& secuencia, double& orden, double& mk) const {
        int ms;
        orden = schedule(s, start_, ms);
        mk = ms;
        secuencia = sequence_errors(s);
    }

    double objective(const Solution& s) const {
        double sq, od, mk;
        evaluate(s, sq, od, mk);
        return mk + penalty * (sq + od);
    }
    bool feasible(const Solution& s) const {
        double sq, od, mk;
        evaluate(s, sq, od, mk);
        return sq == 0 && od == 0;
    }

    // camino crítico (como `model_parts.critical_path`): operaciones (j, k) en orden
    std::vector<std::pair<int, int>> critical_path(const Solution& sol, const std::vector<int>& start) const {
        std::vector<int> pos(n * m, -1);
        for (int mm = 0; mm < (int)sol.size() && mm < m; ++mm)
            for (int i = (int)sol[mm].size() - 1; i >= 0; --i) {
                int j = sol[mm][i];
                if (j >= 0 && j < n) pos[mm * n + j] = i;
            }
        int j = 0, best = -1;
        for (int jj = 0; jj < n; ++jj) {
            int last = off[jj + 1] - 1, e = start[last] + routes[jj].back().second;
            if (e > best) best = e, j = jj;
        }
        std::vector<std::pair<int, int>> path{{j, (int)routes[j].size() - 1}};
        while (true) {
            auto [jj, k] = path.back();
            int s = start[off[jj] + k];
            if (s <= 0) break;
            int mm = routes[jj][k].first, i = pos[mm * n + jj];
            if (i > 0) {
                int pj = sol[mm][i - 1];
                int pk = (pj >= 0 && pj < n) ? opk[pj][mm] : -1;
                if (pk >= 0 && start[off[pj] + pk] + routes[pj][pk].second == s) {
                    path.push_back({pj, pk});
                    continue;
                }
            }
            if (k > 0 && start[off[jj] + k - 1] + routes[jj][k - 1].second == s) {
                path.push_back({jj, k - 1});
                continue;
            }
            break;
        }
        std::reverse(path.begin(), path.end());
        return path;
    }

    // bloques del camino crítico: (máquina, trabajos consecutivos), de 2 o más
    std::vector<std::pair<int, std::vector<int>>> critical_blocks(const Solution& sol) const {
        int mk;
        schedule(sol, start_, mk);
        std::vector<std::pair<int, std::vector<int>>> blocks;
        for (auto [j, k] : critical_path(sol, start_)) {
            int mm = routes[j][k].first;
            if (!blocks.empty() && blocks.back().first == mm) blocks.back().second.push_back(j);
            else blocks.push_back({mm, {j}});
        }
        std::vector<std::pair<int, std::vector<int>>> out;
        for (auto& b : blocks) if (b.second.size() > 1) out.push_back(b);
        return out;
    }

    // ---------------------------------------------------------------- vista constructiva (despacho)
    Partial empty() const {
        return Partial{std::vector<std::vector<int>>(m), std::vector<int>(n, 0), std::vector<int>(n, 0),
                       std::vector<int>(m, 0), {}};
    }
    void candidates(const Partial& p, std::vector<Action>& out) const {
        for (int j = 0; j < n; ++j) {
            int k = p.nxt[j];
            if (k < (int)routes[j].size()) {
                auto [mm, pt] = routes[j][k];
                int s = std::max(p.job_ready[j], p.mach_ready[mm]);
                out.push_back({j, k, mm, s, s + pt});
            }
        }
    }
    Partial apply(const Partial& p, const Action& a) const {
        Partial q = p;
        q.seqs[a.machine].push_back(a.job);
        q.nxt[a.job] = a.op + 1;
        q.job_ready[a.job] = a.end;
        q.mach_ready[a.machine] = a.end;
        q.order.push_back(a.job);
        return q;
    }
    bool is_complete(const Partial& p) const {
        for (int j = 0; j < n; ++j) if (p.nxt[j] < (int)routes[j].size()) return false;
        return true;
    }
    Solution to_solution(const Partial& p) const { return p.seqs; }
    Solution complete(Partial p, Rng&) const {
        std::vector<Action> c;
        while (!is_complete(p)) {
            c.clear();
            candidates(p, c);
            p = apply(p, c[0]);
        }
        return p.seqs;
    }
};

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

// N5: intercambiar las dos primeras o las dos últimas operaciones de cada bloque crítico. Movimiento (m, a, b).
struct CriticalSwap : hsf::Neighborhood<M> {
    const M& js;
    explicit CriticalSwap(const M& m) : js(m) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        std::set<Move> seen;
        for (auto& [mm, b] : js.critical_blocks(s)) {
            Move p1{mm, b[0], b[1], 0, 0, 0}, p2{mm, b[b.size() - 2], b.back(), 0, 0, 0};
            for (auto& p : {p1, p2}) if (seen.insert(p).second) out.push_back(p);
        }
    }
    Sol apply(const Sol& s, const Move& mv) override { return swap_jobs(s, mv[0], mv[1], mv[2]); }
    double delta(const Sol& s, const Move& mv) override { return js.objective(apply(s, mv)) - js.objective(s); }
};

// Mover un trabajo de un bloque crítico al principio o al final del bloque. Movimiento (m, trabajo, desde, hasta).
struct CriticalInsert : hsf::Neighborhood<M> {
    const M& js;
    explicit CriticalInsert(const M& m) : js(m) {}
    void moves(const Sol& s, std::vector<Move>& out) override {
        for (auto& [mm, b] : js.critical_blocks(s)) {
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
            auto path = js.critical_path(s, st);
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
