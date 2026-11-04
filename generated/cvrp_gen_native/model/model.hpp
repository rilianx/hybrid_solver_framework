#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <algorithm>
#include <utility>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;

    int n = 0;
    double capacity = 0.0;
    bool rounded = false;
    std::vector<double> xs, ys, demand;
    std::vector<double> D;      // matriz (n+1)x(n+1) si cabe
    bool useMatrix = true;
    mutable std::vector<int> cnt;

    double rawDist(int i, int j) const {
        double d = std::hypot(xs[i] - xs[j], ys[i] - ys[j]);
        return rounded ? (double)(long long)(d + 0.5) : d;
    }
    double dist(int i, int j) const {
        return useMatrix ? D[(size_t)i * (n + 1) + j] : rawDist(i, j);
    }

    static Model parse(const std::string& text) {
        Model m;
        std::istringstream in(text);
        std::string line;
        // cabecera: primera línea no vacía
        while (std::getline(in, line)) {
            if (line.find_first_not_of(" \t\r\n") != std::string::npos) break;
        }
        {
            std::istringstream h(line);
            std::string a, b, c;
            h >> a >> b;
            m.n = (int)std::stod(a);
            m.capacity = std::stod(b);
            if (h >> c) m.rounded = (c == "round");
        }
        m.xs.assign(m.n + 1, 0.0);
        m.ys.assign(m.n + 1, 0.0);
        m.demand.assign(m.n + 1, 0.0);
        for (int i = 0; i <= m.n; ++i) {
            double x = 0, y = 0, d = 0;
            in >> x >> y >> d;
            m.xs[i] = x; m.ys[i] = y; m.demand[i] = d;
        }
        m.demand[0] = 0.0;
        m.useMatrix = (m.n <= 4000);
        if (m.useMatrix) {
            m.D.assign((size_t)(m.n + 1) * (m.n + 1), 0.0);
            for (int i = 0; i <= m.n; ++i)
                for (int j = 0; j <= m.n; ++j)
                    m.D[(size_t)i * (m.n + 1) + j] = m.rawDist(i, j);
        }
        m.cnt.assign(m.n + 1, 0);
        double triv = m.distanceOf(m.trivial());
        m.penalty = 10.0 * (std::fabs(triv) + 1.0);
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
        for (int i = n - 1; i > 0; --i) std::swap(perm[i], perm[rng.below(i + 1)]);
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

    double distanceOf(const Solution& s) const {
        double tot = 0.0;
        for (const auto& r : s) {
            int prev = 0;
            bool any = false;
            for (int c : r) {
                if (c < 1 || c > n) continue;
                tot += dist(prev, c);
                prev = c;
                any = true;
            }
            if (any) tot += dist(prev, 0);
        }
        return tot;
    }

    double visitViolation(const Solution& s) const {
        std::fill(cnt.begin(), cnt.end(), 0);
        double bad = 0.0;
        for (const auto& r : s)
            for (int c : r) {
                if (c < 1 || c > n) bad += 1.0;
                else cnt[c]++;
            }
        for (int c = 1; c <= n; ++c) bad += std::abs(cnt[c] - 1);
        return bad;
    }

    double capacityViolation(const Solution& s) const {
        double ex = 0.0;
        for (const auto& r : s) {
            double load = 0.0;
            for (int c : r)
                if (c >= 1 && c <= n) load += demand[c];
            if (load > capacity + 1e-9) ex += load - capacity;
        }
        return ex;
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("visita", visitViolation(s));
        out.emplace_back("capacidad", capacityViolation(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("distancia", distanceOf(s));
    }

    double objective(const Solution& s) const {
        return distanceOf(s) + penalty * (visitViolation(s) + capacityViolation(s));
    }

    bool feasible(const Solution& s) const {
        return visitViolation(s) == 0.0 && capacityViolation(s) == 0.0;
    }
};

} // namespace gen
