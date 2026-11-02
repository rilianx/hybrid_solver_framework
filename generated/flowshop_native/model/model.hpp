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

    int n = 0, m = 0;
    std::vector<long long> pj;  // pj[j*m + i]
    double penalty = 1.0;

    mutable std::vector<long long> C;
    mutable std::vector<uint32_t> mark;
    mutable uint32_t stamp = 0;

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        std::vector<long long> nums;
        std::string tok;
        while (in >> tok) nums.push_back((long long)std::stod(tok));
        md.n = nums.size() > 0 ? (int)nums[0] : 0;
        md.m = nums.size() > 1 ? (int)nums[1] : 0;
        md.pj.assign((size_t)md.n * md.m, 0);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) {
                size_t idx = 2 + (size_t)i * md.n + j;
                md.pj[(size_t)j * md.m + i] = idx < nums.size() ? nums[idx] : 0;
            }
        md.C.assign(md.m, 0);
        md.mark.assign(md.n, 0);
        md.stamp = 0;
        md.penalty = 10.0 * (std::abs(md.flowtime(md.trivial())) + 1.0);
        return md;
    }

    Solution trivial() const {
        std::vector<int> v(n);
        std::iota(v.begin(), v.end(), 0);
        return Solution{v};
    }

    Solution random(hsf::Rng& rng) const {
        std::vector<int> v(n);
        std::iota(v.begin(), v.end(), 0);
        for (int i = n - 1; i > 0; --i) std::swap(v[i], v[rng.below(i + 1)]);
        return Solution{v};
    }

    double flowtime(const Solution& s) const {
        if (s.empty() || m == 0) return 0.0;
        std::fill(C.begin(), C.end(), 0LL);
        long long sum = 0;
        for (int j : s[0]) {
            if (j < 0 || j >= n) continue;
            const long long* p = &pj[(size_t)j * m];
            C[0] += p[0];
            for (int i = 1; i < m; ++i) C[i] = std::max(C[i], C[i - 1]) + p[i];
            sum += C[m - 1];
        }
        return (double)sum;
    }

    double perm_violation(const Solution& s) const {
        if (s.empty()) return (double)n;
        if (++stamp == 0) { std::fill(mark.begin(), mark.end(), 0u); stamp = 1; }
        long long bad = 0, rep = 0, distinct = 0;
        for (int j : s[0]) {
            if (j < 0 || j >= n) { ++bad; continue; }
            if (mark[j] == stamp) ++rep;
            else { mark[j] = stamp; ++distinct; }
        }
        return (double)((n - distinct) + rep + bad);
    }

    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("permutacion", perm_violation(s));
    }

    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        out.clear();
        out.emplace_back("flowtime", flowtime(s));
    }

    double objective(const Solution& s) const {
        return flowtime(s) + penalty * perm_violation(s);
    }

    bool feasible(const Solution& s) const {
        return perm_violation(s) == 0.0;
    }
};

}  // namespace gen
