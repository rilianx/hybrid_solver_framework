#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <utility>
#include <algorithm>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0;
    double capacity = 0.0;
    bool rounded = false;
    std::vector<double> xs, ys, demand;
    std::vector<double> dmat;   // (n+1)x(n+1) si cabe
    bool use_mat = false;
    double penalty = 1.0;
    mutable std::vector<int> cnt;

    double raw_dist(int i, int j) const {
        double d = std::hypot(xs[i] - xs[j], ys[i] - ys[j]);
        return rounded ? std::floor(d + 0.5) : d;
    }
    double dist(int i, int j) const {
        return use_mat ? dmat[(size_t)i * (n + 1) + j] : raw_dist(i, j);
    }

    static Model parse(const std::string& text) {
        Model m;
        std::istringstream in(text);
        std::string first;
        while (std::getline(in, first)) {
            bool blank = true;
            for (char c : first) if (!std::isspace((unsigned char)c)) { blank = false; break; }
            if (!blank) break;
        }
        {
            std::istringstream fl(first);
            fl >> m.n >> m.capacity;
            std::string tok;
            while (fl >> tok) if (tok == "round") m.rounded = true;
        }
        int N = m.n + 1;
        m.xs.assign(N, 0.0); m.ys.assign(N, 0.0); m.demand.assign(N, 0.0);
        for (int i = 0; i < N; ++i) in >> m.xs[i] >> m.ys[i] >> m.demand[i];
        m.demand[0] = 0.0;
        if ((size_t)N * (size_t)N <= (size_t)25000000) {
            m.use_mat = true;
            m.dmat.assign((size_t)N * N, 0.0);
            for (int i = 0; i < N; ++i)
                for (int j = 0; j < N; ++j)
                    m.dmat[(size_t)i * N + j] = m.raw_dist(i, j);
        }
        m.cnt.assign(N, 0);
        Solution t = m.trivial();
        double c = m.distance(t);
        m.penalty = 10.0 * (std::fabs(c) + 1.0);
        return m;
    }

    Solution trivial() const {
        Solution s;
        s.reserve(n);
        for (int c = 1; c <= n; ++c) s.push_back({c});
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> perm(n);
        for (int i = 0; i < n; ++i) perm[i] = i + 1;
        for (int i = n - 1; i > 0; --i) {
            int j = rng.below(i + 1);
            std::swap(perm[i], perm[j]);
        }
        Solution s;
        std::vector<int> cur;
        double load = 0.0;
        for (int c : perm) {
            if (!cur.empty() && load + demand[c] > capacity + 1e-9) {
                s.push_back(cur);
                cur.clear();
                load = 0.0;
            }
            cur.push_back(c);
            load += demand[c];
        }
        if (!cur.empty()) s.push_back(cur);
        return s;
    }

    bool valid(int c) const { return c >= 1 && c <= n; }

    double distance(const Solution& s) const {
        double tot = 0.0;
        for (const auto& r : s) {
            int prev = 0;
            bool any = false;
            for (int c : r) {
                if (!valid(c)) continue;
                tot += dist(prev, c);
                prev = c;
                any = true;
            }
            if (any) tot += dist(prev, 0);
        }
        return tot;
    }

    double visit_viol(const Solution& s) const {
        std::fill(cnt.begin(), cnt.end(), 0);
        double v = 0.0;
        for (const auto& r : s)
            for (int c : r) {
                if (valid(c)) ++cnt[c];
                else v += 1.0;
            }
        for (int c = 1; c <= n; ++c) v += std::abs(cnt[c] - 1);
        return v;
    }

    double cap_viol(const Solution& s) const {
        double v = 0.0;
        for (const auto& r : s) {
            double load = 0.0;
            for (int c : r) if (valid(c)) load += demand[c];
            if (load > capacity) v += load - capacity;
        }
        return v;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("visita", visit_viol(s));
        double cv = cap_viol(s);
        if (cv <= 1e-9) cv = 0.0;
        out.emplace_back("capacidad", cv);
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("distancia", distance(s));
    }

    double objective(const Solution& s) const {
        double cv = cap_viol(s);
        if (cv <= 1e-9) cv = 0.0;
        return distance(s) + penalty * (visit_viol(s) + cv);
    }

    bool feasible(const Solution& s) const {
        for (const auto& r : s) {
            double load = 0.0;
            for (int c : r) {
                if (!valid(c)) return false;
                load += demand[c];
            }
            if (load > capacity + 1e-9) return false;
        }
        return visit_viol(s) == 0.0;
    }
};

} // namespace gen
