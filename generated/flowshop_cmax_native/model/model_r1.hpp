#pragma once
#include <hsf/core.hpp>
#include <vector>
#include <string>
#include <utility>
#include <sstream>
#include <algorithm>
#include <cstdint>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0, m = 0;
    std::vector<long long> pt;   // pt[j*m + i] = p[i][j]
    double penalty = 1.0;

    mutable std::vector<long long> C;
    mutable std::vector<uint32_t> mark;
    mutable uint32_t stamp = 0;

    static Model parse(const std::string& text) {
        Model M;
        std::istringstream in(text);
        std::vector<long long> nums;
        std::string tok;
        while (in >> tok) nums.push_back((long long)std::stod(tok));
        M.n = (int)nums[0];
        M.m = (int)nums[1];
        M.pt.assign((size_t)M.n * M.m, 0);
        for (int i = 0; i < M.m; ++i)
            for (int j = 0; j < M.n; ++j) {
                size_t k = 2 + (size_t)i * M.n + j;
                M.pt[(size_t)j * M.m + i] = k < nums.size() ? nums[k] : 0;
            }
        M.C.assign(M.m, 0);
        M.mark.assign(M.n, 0);
        M.stamp = 0;
        double triv = M.makespan(M.trivial());
        M.penalty = 10.0 * (std::abs(triv) + 1.0);
        return M;
    }

    Solution trivial() const {
        std::vector<int> v(n);
        for (int j = 0; j < n; ++j) v[j] = j;
        return Solution{v};
    }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> v(n);
        for (int j = 0; j < n; ++j) v[j] = j;
        for (int j = n - 1; j > 0; --j) std::swap(v[j], v[rng.below(j + 1)]);
        return Solution{v};
    }

    double makespan(const Solution& s) const {
        if (m == 0) return 0.0;
        std::fill(C.begin(), C.end(), 0LL);
        if (s.empty()) return 0.0;
        for (int j : s[0]) {
            if (j < 0 || j >= n) continue;
            const long long* pj = &pt[(size_t)j * m];
            long long c = C[0] + pj[0];
            C[0] = c;
            for (int i = 1; i < m; ++i) {
                long long a = C[i];
                c = (a > c ? a : c) + pj[i];
                C[i] = c;
            }
        }
        return (double)C[m - 1];
    }

    double perm_violation(const Solution& s) const {
        if (++stamp == 0) {
            std::fill(mark.begin(), mark.end(), 0u);
            stamp = 1;
        }
        long long invalid = 0, repeats = 0, present = 0;
        if (!s.empty()) {
            for (int j : s[0]) {
                if (j < 0 || j >= n) { ++invalid; continue; }
                if (mark[j] == stamp) { ++repeats; continue; }
                mark[j] = stamp;
                ++present;
            }
        }
        long long missing = n - present;
        return (double)(missing + repeats + invalid);
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("permutacion", perm_violation(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("makespan", makespan(s));
    }

    double objective(const Solution& s) const {
        return makespan(s) + penalty * perm_violation(s);
    }

    bool feasible(const Solution& s) const {
        return perm_violation(s) == 0.0;
    }
};

} // namespace gen
