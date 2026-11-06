#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <utility>
#include <algorithm>
#include <numeric>
#include <cstdint>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;
    double penalty = 1.0;
    int n = 0, m = 0;
    std::vector<long long> pt;           // pt[j*m + i] = p[i][j]
    mutable std::vector<long long> C;    // tiempos de finalización por máquina
    mutable std::vector<int> cnt;        // conteo de apariciones por trabajo

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        if (md.n < 0) md.n = 0;
        if (md.m < 0) md.m = 0;
        md.pt.assign((size_t)md.n * md.m, 0);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) {
                long long v = 0;
                in >> v;
                md.pt[(size_t)j * md.m + i] = v;
            }
        md.C.assign(md.m, 0);
        md.cnt.assign(md.n, 0);
        Solution t = md.trivial();
        double c = (double)md.makespan(t);
        md.penalty = 10.0 * (std::abs(c) + 1.0);
        return md;
    }

    Solution trivial() const {
        Solution s(1, std::vector<int>(n));
        std::iota(s[0].begin(), s[0].end(), 0);
        return s;
    }

    Solution random(hsf::Rng& rng) const {
        Solution s = trivial();
        auto& v = s[0];
        for (int i = n - 1; i > 0; --i) {
            int k = rng.below(i + 1);
            std::swap(v[i], v[k]);
        }
        return s;
    }

    long long makespan(const Solution& s) const {
        if (m == 0) return 0;
        std::fill(C.begin(), C.end(), 0LL);
        for (const auto& row : s) {
            for (int j : row) {
                if (j < 0 || j >= n) continue;
                const long long* pj = &pt[(size_t)j * m];
                long long prev = C[0] + pj[0];
                C[0] = prev;
                for (int i = 1; i < m; ++i) {
                    long long c = std::max(C[i], prev) + pj[i];
                    C[i] = c;
                    prev = c;
                }
            }
        }
        return C[m - 1];
    }

    double perm_violation(const Solution& s) const {
        std::fill(cnt.begin(), cnt.end(), 0);
        long long invalid = 0, extra = 0, missing = 0;
        for (const auto& row : s)
            for (int j : row) {
                if (j < 0 || j >= n) { ++invalid; continue; }
                if (cnt[j]++ > 0) ++extra;
            }
        for (int j = 0; j < n; ++j) if (cnt[j] == 0) ++missing;
        return (double)(invalid + extra + missing);
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("permutacion", perm_violation(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("makespan", (double)makespan(s));
    }

    double objective(const Solution& s) const {
        return (double)makespan(s) + penalty * perm_violation(s);
    }

    bool feasible(const Solution& s) const {
        return perm_violation(s) == 0.0;
    }
};

} // namespace gen
