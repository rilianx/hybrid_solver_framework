// El MODELO del job shop (makespan) en C++: la vista heurística y constructiva de `model_parts.py`
// (secuencia por máquina, plan semiactivo). Mismas familias, mismo costo y misma penalización que
// `PartsModel(model_parts, inst)`, así que el validador de Python lo prueba con los mismos casos.
// Es lo que ve el LLM cuando genera componentes en C++ (`llm.native_generator`): solo el modelo, sin
// componentes.
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

}  // namespace jobshop
