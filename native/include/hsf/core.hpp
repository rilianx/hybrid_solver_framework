// Núcleo C++ del framework: contratos de los slots y esqueletos de trayectoria.
//
// Es la mitad "ejecución" de la división Python/C++: el validador, el generador y el tuner siguen en
// Python; aquí corre lo que se repite millones de veces (el modelo heurístico, los componentes y el
// bucle de los esqueletos). La semántica de cada esqueleto y sus parámetros son los de `skeletons/`
// en Python (mismos nombres en la configuración), así una configuración afinada en un lado corre
// igual en el otro.
//
// Un problema (un "modelo") es una clase M con:
//   using Solution = ...;            // con ==, copiable
//   double objective(const Solution&) const;   // costo + penalización (se minimiza)
//   bool feasible(const Solution&) const;
// y, si tiene vista constructiva (para el constructor greedy modular):
//   using Partial = ...; using Action = ...;
//   Partial empty() const;
//   void candidates(const Partial&, std::vector<Action>&) const;
//   Partial apply(const Partial&, const Action&) const;
//   bool is_complete(const Partial&) const;
//   Solution to_solution(const Partial&) const;
//   Solution complete(const Partial&, Rng&) const;
#pragma once

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace hsf {

// Un movimiento: hasta 6 enteros (máquina, trabajos, posiciones, ...). Los que sobran quedan en 0.
using Move = std::array<int, 6>;

struct Rng {
    std::mt19937_64 g;
    explicit Rng(uint64_t seed) : g(seed) {}
    double uniform() { return std::uniform_real_distribution<double>(0.0, 1.0)(g); }
    int below(int n) { return std::uniform_int_distribution<int>(0, n - 1)(g); }
};

struct Clock {
    std::chrono::steady_clock::time_point t0 = std::chrono::steady_clock::now();
    double elapsed() const {
        return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    }
};

// La configuración plana del tuner: {"skeleton": "SA", "SA.T0": 31.6, "constructor": "...", ...}.
struct Config {
    std::map<std::string, double> num;
    std::map<std::string, std::string> str;
    double get(const std::string& k) const {
        auto it = num.find(k);
        if (it == num.end()) throw std::invalid_argument("falta el parámetro numérico '" + k + "' en la configuración");
        return it->second;
    }
    double get(const std::string& k, double def) const {
        auto it = num.find(k);
        return it == num.end() ? def : it->second;
    }
    std::string text(const std::string& k) const {
        auto it = str.find(k);
        if (it == str.end()) throw std::invalid_argument("falta '" + k + "' en la configuración");
        return it->second;
    }
    std::string text(const std::string& k, const std::string& def) const {
        auto it = str.find(k);
        return it == str.end() ? def : it->second;
    }
    // los parámetros de un componente: las claves "<nombre>.<param>"
    Config scoped(const std::string& name) const {
        Config out;
        std::string pre = name + ".";
        for (auto& [k, v] : num) if (k.rfind(pre, 0) == 0) out.num[k.substr(pre.size())] = v;
        for (auto& [k, v] : str) if (k.rfind(pre, 0) == 0) out.str[k.substr(pre.size())] = v;
        return out;
    }
};

// ------------------------------------------------------------------ contratos de los slots
template <class M>
struct Constructor {
    using Sol = typename M::Solution;
    virtual ~Constructor() = default;
    virtual Sol build(Rng& rng) = 0;
};

template <class M>
struct Neighborhood {
    using Sol = typename M::Solution;
    virtual ~Neighborhood() = default;
    virtual void moves(const Sol& s, std::vector<Move>& out) = 0;  // agrega a `out` (vacío al llamar)
    virtual Sol apply(const Sol& s, const Move& m) = 0;
    virtual double delta(const Sol& s, const Move& m) = 0;  // objective(apply(s, m)) - objective(s)
    // lo que TS prohíbe tras aplicar `m`: el movimiento que lo deshace (como `inverse` en Python); por
    // defecto el mismo movimiento (correcto para los auto-inversos, p.ej. un flip)
    virtual Move tabu_key(const Move& m) { return m; }
    // aproximación barata de `delta` (opcional, la usa TS para filtrar candidatos); sin ella, el delta exacto
    virtual bool has_estimate() const { return false; }
    virtual double estimate(const Sol& s, const Move& m) { return delta(s, m); }
    // hasta k movimientos distintos al azar; con k o menos, todos en orden sin gastar azar (como en Python)
    virtual void sample(const Sol& s, int k, Rng& rng, std::vector<Move>& out) {
        out.clear();
        moves(s, out);
        if (k >= 0 && (int)out.size() > k) {
            for (int i = 0; i < k; ++i) std::swap(out[i], out[i + rng.below((int)out.size() - i)]);
            out.resize(k);
        }
    }
};

template <class M>
struct Perturbation {
    using Sol = typename M::Solution;
    virtual ~Perturbation() = default;
    virtual Sol perturb(const Sol& s, double strength, Rng& rng) = 0;
};

// Conectar dos soluciones (path relinking): una medida de cuánto difieren y un paso de una hacia la otra.
template <class M>
struct Relink {
    using Sol = typename M::Solution;
    virtual ~Relink() = default;
    // cuántos pasos separan a `a` de `b`; 0 si y solo si son la misma solución
    virtual int distance(const Sol& a, const Sol& b) = 0;
    // una solución más cerca de `guide` que `cur` (distance estrictamente menor); al azar entre las posibles
    virtual Sol step(const Sol& cur, const Sol& guide, Rng& rng) = 0;
};

template <class M>
struct GreedyScore {
    virtual ~GreedyScore() = default;
    virtual double score(const typename M::Partial& p, const typename M::Action& a) = 0;
};

// El constructor greedy modular (`core.construction.GreedyConstructor`): reglas greedy | rcl | roulette.
template <class M>
struct GreedyConstructor : Constructor<M> {
    const M& model;
    std::unique_ptr<GreedyScore<M>> score;
    std::string rule;
    double alpha;
    GreedyConstructor(const M& m, std::unique_ptr<GreedyScore<M>> s, std::string r, double a)
        : model(m), score(std::move(s)), rule(std::move(r)), alpha(a) {
        if (rule != "greedy" && rule != "rcl" && rule != "roulette") throw std::invalid_argument("regla desconocida: " + rule);
    }
    typename M::Solution build(Rng& rng) override {
        auto p = model.empty();
        std::vector<typename M::Action> cands;
        std::vector<double> sc;
        for (int step = 0; step < 10'000'000; ++step) {
            if (model.is_complete(p)) return model.to_solution(p);
            cands.clear();
            model.candidates(p, cands);
            if (cands.empty()) return model.complete(p, rng);
            sc.resize(cands.size());
            for (size_t i = 0; i < cands.size(); ++i) {
                sc[i] = score->score(p, cands[i]);
                if (!std::isfinite(sc[i])) throw std::runtime_error("el puntaje devolvió NaN o infinito");
            }
            p = model.apply(p, cands[pick(sc, rng)]);
        }
        throw std::runtime_error("la construcción no terminó");
    }
    size_t pick(const std::vector<double>& sc, Rng& rng) {
        size_t best = std::min_element(sc.begin(), sc.end()) - sc.begin();
        if (rule == "greedy") return best;
        double lo = sc[best], hi = *std::max_element(sc.begin(), sc.end());
        if (rule == "rcl") {
            double cut = lo + alpha * (hi - lo) + 1e-12;
            std::vector<size_t> pool;
            for (size_t i = 0; i < sc.size(); ++i) if (sc[i] <= cut) pool.push_back(i);
            return pool[rng.below((int)pool.size())];
        }
        double eps = 1e-9 + 1e-6 * (hi - lo), total = 0.0;
        for (double s : sc) total += 1.0 / (s - lo + eps);
        double r = rng.uniform() * total, acc = 0.0;
        for (size_t i = 0; i < sc.size(); ++i) {
            acc += 1.0 / (sc[i] - lo + eps);
            if (acc >= r) return i;
        }
        return sc.size() - 1;
    }
};

// ------------------------------------------------------------------ catálogo
template <class M>
struct Catalog {
    using Params = Config;
    std::map<std::string, std::function<std::unique_ptr<Constructor<M>>(const M&, const Params&)>> constructors;
    std::map<std::string, std::function<std::unique_ptr<GreedyScore<M>>(const M&, const Params&)>> scores;
    std::map<std::string, std::function<std::unique_ptr<Neighborhood<M>>(const M&, const Params&)>> neighborhoods;
    std::map<std::string, std::function<std::unique_ptr<Perturbation<M>>(const M&, const Params&)>> perturbations;
    std::map<std::string, std::function<std::unique_ptr<Relink<M>>(const M&, const Params&)>> relinks;

    // `greedy_<puntaje>` es el constructor greedy con ese puntaje (como en `llm.catalog`)
    std::unique_ptr<Constructor<M>> constructor(const std::string& name, const M& m, const Config& cfg) const {
        Params p = cfg.scoped(name);
        auto it = constructors.find(name);
        if (it != constructors.end()) return it->second(m, p);
        if (name.rfind("greedy_", 0) == 0) {
            auto s = scores.find(name.substr(7));
            if (s != scores.end())
                return std::make_unique<GreedyConstructor<M>>(m, s->second(m, p), p.text("rule", "greedy"), p.get("alpha", 0.2));
        }
        throw std::invalid_argument("constructor desconocido: " + name);
    }
    std::unique_ptr<Neighborhood<M>> neighborhood(const std::string& name, const M& m, const Config& cfg) const {
        auto it = neighborhoods.find(name);
        if (it == neighborhoods.end()) throw std::invalid_argument("vecindario desconocido: " + name);
        return it->second(m, cfg.scoped(name));
    }
    std::unique_ptr<Perturbation<M>> perturbation(const std::string& name, const M& m, const Config& cfg) const {
        auto it = perturbations.find(name);
        if (it == perturbations.end()) throw std::invalid_argument("perturbación desconocida: " + name);
        return it->second(m, cfg.scoped(name));
    }
    std::unique_ptr<Relink<M>> relink(const std::string& name, const M& m, const Config& cfg) const {
        auto it = relinks.find(name);
        if (it == relinks.end()) throw std::invalid_argument("relink desconocido: " + name);
        return it->second(m, cfg.scoped(name));
    }
};

// Las partidas de referencia de todo catálogo (como `llm.cycle._handwritten`): la solución trivial y una al
// azar del modelo (`M::trivial()`, `M::random(rng)`).
template <class M>
struct TrivialConstructor : Constructor<M> {
    const M& model;
    explicit TrivialConstructor(const M& m) : model(m) {}
    typename M::Solution build(Rng&) override { return model.trivial(); }
};
template <class M>
struct RandomConstructor : Constructor<M> {
    const M& model;
    explicit RandomConstructor(const M& m) : model(m) {}
    typename M::Solution build(Rng& rng) override { return model.random(rng); }
};
template <class M>
void add_base_constructors(Catalog<M>& c) {
    c.constructors["trivial"] = [](const M& m, const Config&) { return std::make_unique<TrivialConstructor<M>>(m); };
    c.constructors["random"] = [](const M& m, const Config&) { return std::make_unique<RandomConstructor<M>>(m); };
}

// ------------------------------------------------------------------ esqueletos
template <class M>
struct Result {
    typename M::Solution best;
    double objective;
    long iterations;
    double elapsed;
};

// El bucle genérico (`core.skeleton.TrajectorySkeleton`): candidato, aceptación, mejor, actualización.
template <class M, class Gen, class Accept, class Update>
Result<M> trajectory(const M& model, typename M::Solution sol, double budget, Gen gen, Accept accept, Update update) {
    Clock clock;
    double f = model.objective(sol);
    Result<M> res{sol, f, 0, 0.0};
    double elapsed = 0.0;
    typename M::Solution cand;
    while (elapsed < budget) {
        // el generador puede dar el objetivo del candidato (f + delta exacto) y ahorrar la evaluación completa
        double fc = std::numeric_limits<double>::quiet_NaN();
        if (gen(sol, f, res.objective, elapsed, cand, fc)) {
            if (std::isnan(fc)) fc = model.objective(cand);
            if (accept(f, fc)) {
                sol = cand;
                f = fc;
                if (f < res.objective) res.best = sol, res.objective = f;
            }
        }
        update(elapsed);
        ++res.iterations;
        elapsed = clock.elapsed();
    }
    res.elapsed = elapsed;
    return res;
}

// `skeletons.ils.hill_climb`: mejora (primera o mejor) sobre una muestra de hasta `sample` movimientos.
template <class M>
typename M::Solution hill_climb(Neighborhood<M>& nbh, typename M::Solution cur, bool first, int sample,
                                double max_seconds, Rng& rng) {
    Clock clock;
    std::vector<Move> mv;
    while (true) {
        nbh.sample(cur, sample, rng, mv);
        const Move* best = nullptr;
        double best_d = 0.0;
        bool timeout = false;
        for (const Move& m : mv) {
            if (clock.elapsed() >= max_seconds) { timeout = true; break; }
            double d = nbh.delta(cur, m);
            if (d < best_d) {
                best = &m, best_d = d;
                if (first) break;
            }
        }
        if (!best) break;
        cur = nbh.apply(cur, *best);
        if (timeout || clock.elapsed() >= max_seconds) break;
    }
    return cur;
}

template <class M>
bool random_move(Neighborhood<M>& nbh, const typename M::Solution& s, Rng& rng, std::vector<Move>& buf, Move& out) {
    buf.clear();
    nbh.moves(s, buf);
    if (buf.empty()) return false;
    out = buf[rng.below((int)buf.size())];
    return true;
}

// Un paso de la búsqueda tabú (`skeletons/ts.py`): entre una muestra de `size` movimientos (ordenados por `estimate`
// y con delta exacto solo de los `top` primeros admisibles, si `top` > 0), el mejor no tabú o que mejora `f_best`;
// si todos son tabú, el mejor de ellos (Nowicki y Smutnicki). Lo usan TS y la mejora de PR.
template <class M>
struct TabuStep {
    using Sol = typename M::Solution;
    Neighborhood<M>& nbh;
    size_t tenure;
    int size, top;
    std::map<Move, int> tabu;
    std::vector<Move> queue, buf;
    size_t head = 0;
    std::vector<std::pair<double, size_t>> order;

    TabuStep(Neighborhood<M>& n, size_t ten, int sz, int tp) : nbh(n), tenure(ten), size(sz), top(n.has_estimate() ? tp : 0) {}
    void clear() { tabu.clear(), queue.clear(), head = 0; }
    bool operator()(const Sol& s, double f, double f_best, Rng& rng, Sol& cand, double& fc) {
        nbh.sample(s, size, rng, buf);
        order.clear();
        for (size_t i = 0; i < buf.size(); ++i) order.push_back({top > 0 ? nbh.estimate(s, buf[i]) : 0.0, i});
        if (top > 0) std::stable_sort(order.begin(), order.end(), [](auto& a, auto& b) { return a.first < b.first; });
        const Move* best = nullptr;
        const Move* best_tabu = nullptr;
        double best_d = std::numeric_limits<double>::infinity(), tabu_d = best_d;
        int exact = 0;
        for (auto& [e, i] : order) {
            const Move& m = buf[i];
            double d = nbh.delta(s, m);
            if (tabu.count(m) && !(f + d < f_best)) {
                if (d < tabu_d) best_tabu = &m, tabu_d = d;
                continue;
            }
            if (d < best_d) best = &m, best_d = d;
            if (top > 0 && ++exact >= top) break;
        }
        if (!best) best = best_tabu, best_d = tabu_d;
        if (!best) return false;
        Move key = nbh.tabu_key(*best);
        queue.push_back(key);
        ++tabu[key];
        while (queue.size() - head > tenure) {
            auto it = tabu.find(queue[head++]);
            if (it != tabu.end() && --it->second <= 0) tabu.erase(it);
        }
        cand = nbh.apply(s, *best);
        fc = f + best_d;
        return true;
    }
};

// `skeletons/pr.py`: una población de élite de `PR.pop_size` soluciones mejoradas con tabú; en cada vuelta se eligen dos
// al azar, se recorre el camino de una a la otra con el componente `relink` (en cada paso, la mejor de `PR.path_cands`
// soluciones un paso más cerca) y la mejor solución del tramo central del camino (lejos de las dos, según `PR.band`)
// se mejora con `PR.ts_iters` iteraciones de tabú. El resultado reemplaza a la peor de la población si es mejor que
// ella y no está repetido. La población inicial: la partida y construcciones nuevas, cada una con `PR.init_moves`
// movimientos al azar del vecindario (para que no salgan iguales) y mejorada con tabú.
template <class M>
Result<M> path_relinking(const Catalog<M>& cat, const M& model, const Config& cfg, typename M::Solution start,
                         Constructor<M>& ctor, Rng& rng, double budget) {
    using Sol = typename M::Solution;
    Clock clock;
    auto nbh = cat.neighborhood(cfg.text("neighborhood"), model, cfg);
    auto rel = cat.relink(cfg.text("relink"), model, cfg);
    TabuStep<M> step(*nbh, (size_t)cfg.get("PR.tenure"), (int)cfg.get("PR.candidate_size"), (int)cfg.get("PR.estimate_top", 0));
    size_t pop_size = std::max(2, (int)cfg.get("PR.pop_size"));
    long ts_iters = (long)cfg.get("PR.ts_iters");
    int path_cands = std::max(1, (int)cfg.get("PR.path_cands", 1)), init_moves = (int)cfg.get("PR.init_moves", 20);
    double band = cfg.get("PR.band", 0.25);
    Result<M> res{start, model.objective(start), 0, 0.0};
    auto over = [&] { return clock.elapsed() >= budget; };
    auto improve = [&](Sol s) {
        step.clear();
        double f = model.objective(s), fb = f;
        Sol best = s, cand;
        for (long i = 0; i < ts_iters && !over(); ++i) {
            double fc;
            if (!step(s, f, fb, rng, cand, fc)) break;
            s = std::move(cand), f = fc, ++res.iterations;
            if (f < fb) best = s, fb = f;
        }
        if (fb < res.objective) res.best = best, res.objective = fb;
        return std::make_pair(best, fb);
    };
    std::vector<std::pair<Sol, double>> pop;
    auto repeated = [&](const Sol& s) {
        for (auto& p : pop) if (rel->distance(s, p.first) == 0) return true;
        return false;
    };
    std::vector<Move> buf;
    for (size_t i = 0; i < pop_size && !over(); ++i) {
        Sol s = i == 0 ? start : ctor.build(rng);
        for (int k = 0; k < (i == 0 ? 0 : init_moves); ++k) {
            Move m;
            if (!random_move(*nbh, s, rng, buf, m)) break;
            s = nbh->apply(s, m);
        }
        auto p = improve(s);
        if (!repeated(p.first)) pop.push_back(std::move(p));
    }
    while (!over() && pop.size() >= 2) {
        size_t a = rng.below((int)pop.size()), b = rng.below((int)pop.size() - 1);
        if (b >= a) ++b;
        const Sol& guide = pop[b].first;
        Sol cur = pop[a].first;
        int d0 = rel->distance(cur, guide), d = d0;
        int lo = std::max(1, (int)std::ceil(band * d0)), hi = std::max(lo, d0 - lo);
        Sol pick = cur;
        double f_pick = std::numeric_limits<double>::infinity();
        while (d > 0 && d0 - d < hi && !over()) {
            Sol nxt;
            double f_nxt = std::numeric_limits<double>::infinity();
            for (int c = 0; c < path_cands; ++c) {
                Sol x = rel->step(cur, guide, rng);
                double fx = model.objective(x);
                if (fx < f_nxt) nxt = std::move(x), f_nxt = fx;
            }
            int dn = rel->distance(nxt, guide);
            if (dn >= d) throw std::runtime_error("relink: el paso no acercó la solución a la guía");
            cur = std::move(nxt), d = dn;
            if (d0 - d >= lo && f_nxt < f_pick) pick = cur, f_pick = f_nxt;
        }
        if (over()) break;
        auto p = improve(pick);
        size_t worst = 0;
        for (size_t i = 1; i < pop.size(); ++i) if (pop[i].second > pop[worst].second) worst = i;
        if (p.second < pop[worst].second && !repeated(p.first)) pop[worst] = std::move(p);
    }
    res.elapsed = clock.elapsed();
    return res;
}

// Corre una configuración. `shake` son los vecindarios de VNS después del de la búsqueda local.
template <class M>
Result<M> solve(const Catalog<M>& cat, const M& model, const Config& cfg, const std::vector<std::string>& shake,
                uint64_t seed, double budget) {
    Rng rng(seed);
    std::string sk = cfg.text("skeleton");
    auto ctor = cat.constructor(cfg.text("constructor"), model, cfg);
    auto start = ctor->build(rng);
    auto better = [](double fc, double fn) { return fn < fc; };
    auto none = [](double) {};
    std::vector<Move> buf;
    if (sk == "SA") {
        auto nbh = cat.neighborhood(cfg.text("neighborhood"), model, cfg);
        double T0 = cfg.get("SA.T0"), T = T0;
        bool by_time = cfg.text("SA.cooling") == "time";
        double T_end = cfg.get("SA.T_end"), alpha = cfg.get("SA.alpha");
        int per_T = (int)cfg.get("SA.iters_per_T"), at_T = 0;
        // `SA.eval`: "objective" aplica el movimiento y evalúa el candidato completo; "delta" decide Metropolis con el
        // delta del vecindario (exacto por contrato) y solo aplica el aceptado. Conviene "delta" si es incremental.
        bool by_delta = cfg.text("SA.eval", "objective") == "delta";
        auto gen = [&](const auto& s, double f, double, double, auto& cand, double& fc) {
            Move m;
            if (!random_move(*nbh, s, rng, buf, m)) return false;
            if (!by_delta) {
                cand = nbh->apply(s, m);
                return true;
            }
            double d = nbh->delta(s, m);
            if (d > 0 && !(T > 0 && rng.uniform() < std::exp(-d / T))) return false;
            cand = nbh->apply(s, m);
            fc = f + d;
            return true;
        };
        auto accept = [&](double fc, double fn) {
            double d = fn - fc;
            if (by_delta || d <= 0) return true;  // con delta, Metropolis ya se decidió en el generador
            return T > 0 && rng.uniform() < std::exp(-d / T);
        };
        auto update = [&](double elapsed) {
            if (by_time) T = T0 * std::pow(T_end, std::min(1.0, elapsed / budget));
            else if (++at_T >= per_T) T *= alpha, at_T = 0;
        };
        return trajectory(model, start, budget, gen, accept, update);
    }
    if (sk == "ILS") {
        auto nbh = cat.neighborhood(cfg.text("neighborhood"), model, cfg);
        auto pert = cat.perturbation(cfg.text("perturbation"), model, cfg);
        bool first = cfg.text("ILS.ls_strategy") == "first";
        int sample = (int)cfg.get("ILS.ls_sample");
        double ls_s = budget * cfg.get("ILS.ls_time_share"), strength = cfg.get("ILS.strength");
        bool started = false;
        auto gen = [&](const auto& s, double, double, double, auto& cand, double&) {
            if (!started) {
                started = true;
                cand = hill_climb(*nbh, s, first, sample, ls_s, rng);
            } else {
                cand = hill_climb(*nbh, pert->perturb(s, strength, rng), first, sample, ls_s, rng);
            }
            return true;
        };
        return trajectory(model, start, budget, gen, better, none);
    }
    if (sk == "VNS") {
        std::vector<std::unique_ptr<Neighborhood<M>>> ns;
        ns.push_back(cat.neighborhood(cfg.text("neighborhood"), model, cfg));
        for (auto& n : shake) ns.push_back(cat.neighborhood(n, model, cfg));
        int strength = (int)cfg.get("VNS.shake_strength"), sample = (int)cfg.get("VNS.ls_sample");
        double ls_s = budget * cfg.get("VNS.ls_time_share");
        size_t k = 0;
        auto gen = [&](const auto& s, double f, double, double, auto& cand, double&) {
            auto cur = s;
            for (int i = 0; i < strength; ++i) {
                Move m;
                if (!random_move(*ns[k], cur, rng, buf, m)) break;
                cur = ns[k]->apply(cur, m);
            }
            cand = hill_climb(*ns[0], cur, true, sample, ls_s, rng);
            k = model.objective(cand) < f ? 0 : (k + 1) % ns.size();
            return true;
        };
        return trajectory(model, start, budget, gen, better, none);
    }
    if (sk == "TS") {
        // como `skeletons/ts.py`: filtrado por estimación (`estimate_top`) y saltos atrás a la élite (`elite_size`, `stall`)
        auto nbh = cat.neighborhood(cfg.text("neighborhood"), model, cfg);
        TabuStep<M> step(*nbh, (size_t)cfg.get("TS.tenure"), (int)cfg.get("TS.candidate_size"), (int)cfg.get("TS.estimate_top", 0));
        size_t elite_size = (size_t)cfg.get("TS.elite_size", 0);
        long stall = (long)cfg.get("TS.stall", 500), iter = 0, last_event = 0;
        double track_best = std::numeric_limits<double>::infinity();
        std::vector<typename M::Solution> elites;
        auto gen = [&](const auto& s, double f, double f_best, double, auto& cand, double& fc) {
            ++iter;
            if (elite_size > 0) {
                if (f < track_best) {
                    track_best = f, last_event = iter;
                    elites.push_back(s);
                    if (elites.size() > elite_size) elites.erase(elites.begin());
                } else if (iter - last_event >= stall && !elites.empty()) {
                    last_event = iter;
                    step.clear();
                    cand = elites.back();
                    elites.pop_back();
                    return true;
                }
            }
            return step(s, f, f_best, rng, cand, fc);
        };
        return trajectory(model, start, budget, gen, [](double, double) { return true; }, none);
    }
    if (sk == "PR") return path_relinking(cat, model, cfg, std::move(start), *ctor, rng, budget);
    throw std::invalid_argument("esqueleto sin versión nativa: " + sk);
}

}  // namespace hsf
