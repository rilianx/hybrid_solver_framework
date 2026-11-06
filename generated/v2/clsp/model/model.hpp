#pragma once
#include <hsf/core.hpp>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>
#include <utility>
#include <cmath>
#include <limits>
#include <functional>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0, P = 0;
    std::vector<std::vector<double>> d;
    std::vector<double> s, h, st, cap;
    double totalDemand = 0.0;
    double infCap = 1.0;

    // working memory for min-cost max-flow
    mutable std::vector<int> eto, enext, head, prevE;
    mutable std::vector<double> ecap, ecost, dist, pot;
    mutable std::vector<std::pair<double,int>> heapv;
    int V = 0;

    static Model parse(const std::string& text) {
        Model m;
        std::istringstream in(text);
        in >> m.n >> m.P;
        m.cap.assign(m.P, 0.0);
        for (int t = 0; t < m.P; ++t) in >> m.cap[t];
        m.d.assign(m.n, std::vector<double>(m.P, 0.0));
        m.s.assign(m.n, 0.0); m.h.assign(m.n, 0.0); m.st.assign(m.n, 0.0);
        m.totalDemand = 0.0;
        for (int i = 0; i < m.n; ++i) {
            in >> m.s[i] >> m.h[i] >> m.st[i];
            for (int t = 0; t < m.P; ++t) { in >> m.d[i][t]; m.totalDemand += m.d[i][t]; }
        }
        double capSum = 0; for (double c : m.cap) capSum += std::max(0.0, c);
        m.infCap = std::max(m.totalDemand, capSum) * 2.0 + 1.0;
        m.V = 2 + m.P + m.n * m.P;
        size_t E = 2 * (size_t)(m.P + m.n * m.P + m.n * std::max(0, m.P - 1) + m.n * m.P) + 4;
        m.eto.reserve(E); m.enext.reserve(E); m.ecap.reserve(E); m.ecost.reserve(E);
        m.head.assign(m.V, -1); m.prevE.assign(m.V, -1);
        m.dist.assign(m.V, 0.0); m.pot.assign(m.V, 0.0);
        m.heapv.reserve(E + m.V + 4);
        m.penalty = 0.0;
        Solution tr = m.trivial();
        double sc, hc, sh;
        m.evaluate(tr, sc, hc, sh);
        m.penalty = 10.0 * (std::fabs(sc + hc) + 1.0);
        return m;
    }

    Solution trivial() const {
        return Solution(n, std::vector<int>(P, 1));
    }

    Solution random(hsf::Rng& rng) const {
        Solution sol(n, std::vector<int>(P, 0));
        for (int i = 0; i < n; ++i)
            for (int t = 0; t < P; ++t) sol[i][t] = rng.below(2);
        return sol;
    }

    void addEdge(int u, int v, double c, double w) const {
        eto.push_back(v); ecap.push_back(c); ecost.push_back(w); enext.push_back(head[u]); head[u] = (int)eto.size() - 1;
        eto.push_back(u); ecap.push_back(0.0); ecost.push_back(-w); enext.push_back(head[v]); head[v] = (int)eto.size() - 1;
    }

    static bool on(const Solution& sol, int i, int t) {
        return i < (int)sol.size() && t < (int)sol[i].size() && sol[i][t] != 0;
    }

    // setup cost, holding cost (optimal), shortfall (min unmet demand)
    void evaluate(const Solution& sol, double& setupC, double& holdC, double& shortfall) const {
        setupC = 0.0;
        eto.clear(); enext.clear(); ecap.clear(); ecost.clear();
        std::fill(head.begin(), head.end(), -1);
        const int S = 0, T = 1;
        for (int t = 0; t < P; ++t) {
            double used = 0.0;
            for (int i = 0; i < n; ++i) if (on(sol, i, t)) { used += st[i]; setupC += s[i]; }
            double ce = cap[t] - used;
            if (ce > 1e-12) addEdge(S, 2 + t, ce, 0.0);
        }
        for (int i = 0; i < n; ++i) {
            for (int t = 0; t < P; ++t) {
                int node = 2 + P + i * P + t;
                if (on(sol, i, t)) addEdge(2 + t, node, infCap, 0.0);
                if (t + 1 < P) addEdge(node, node + 1, infCap, h[i]);
                if (d[i][t] > 0) addEdge(node, T, d[i][t], 0.0);
            }
        }
        const double INF = std::numeric_limits<double>::infinity();
        const double eps = 1e-9;
        std::fill(pot.begin(), pot.end(), 0.0);
        double flow = 0.0, cost = 0.0;
        auto cmp = std::greater<std::pair<double,int>>();
        while (true) {
            std::fill(dist.begin(), dist.end(), INF);
            std::fill(prevE.begin(), prevE.end(), -1);
            dist[S] = 0.0;
            heapv.clear();
            heapv.emplace_back(0.0, S);
            while (!heapv.empty()) {
                std::pop_heap(heapv.begin(), heapv.end(), cmp);
                auto [du, u] = heapv.back(); heapv.pop_back();
                if (du > dist[u] + 1e-12) continue;
                for (int e = head[u]; e != -1; e = enext[e]) {
                    if (ecap[e] <= eps) continue;
                    int v = eto[e];
                    double rc = ecost[e] + pot[u] - pot[v];
                    if (rc < 0) rc = 0;  // numerical guard
                    double nd = dist[u] + rc;
                    if (nd < dist[v] - 1e-12) {
                        dist[v] = nd; prevE[v] = e;
                        heapv.emplace_back(nd, v);
                        std::push_heap(heapv.begin(), heapv.end(), cmp);
                    }
                }
            }
            if (dist[T] == INF) break;
            for (int v = 0; v < V; ++v) if (dist[v] < INF) pot[v] += dist[v];
            double f = INF;
            for (int v = T; v != S; v = eto[prevE[v] ^ 1]) f = std::min(f, ecap[prevE[v]]);
            if (!(f > eps)) break;
            double pc = 0.0;
            for (int v = T; v != S; v = eto[prevE[v] ^ 1]) {
                int e = prevE[v];
                ecap[e] -= f; ecap[e ^ 1] += f; pc += ecost[e];
            }
            flow += f; cost += f * pc;
        }
        shortfall = totalDemand - flow;
        if (shortfall < 1e-6 * (1.0 + totalDemand) ) shortfall = 0.0;
        holdC = cost < 0 ? 0.0 : cost;
    }

    void violations(const Solution& sol, std::vector<std::pair<std::string, double>>& out) const {
        double sc, hc, sh;
        evaluate(sol, sc, hc, sh);
        out.clear();
        out.emplace_back("demanda", sh);
    }

    void cost_terms(const Solution& sol, std::vector<std::pair<std::string, double>>& out) const {
        double sc, hc, sh;
        evaluate(sol, sc, hc, sh);
        out.clear();
        out.emplace_back("setup", sc);
        out.emplace_back("inventario", hc);
    }

    double objective(const Solution& sol) const {
        double sc, hc, sh;
        evaluate(sol, sc, hc, sh);
        return sc + hc + penalty * sh;
    }

    bool feasible(const Solution& sol) const {
        double sc, hc, sh;
        evaluate(sol, sc, hc, sh);
        return sh <= 0.0;
    }
};

} // namespace gen
