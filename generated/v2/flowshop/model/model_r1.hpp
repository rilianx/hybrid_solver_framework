#pragma once
#include <hsf/core.hpp>

#include <algorithm>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace gen {

struct Model {
    using Solution = std::vector<std::vector<int>>;

    int n = 0;
    int m = 0;
    std::vector<long long> pj;   // pj[j*m + i] = tiempo del trabajo j en la máquina i
    double penalty = 1.0;

    mutable std::vector<long long> comp;  // tiempos de finalización por máquina
    mutable std::vector<int> cnt;         // conteo de apariciones por trabajo

    static Model parse(const std::string& text) {
        Model md;
        std::istringstream in(text);
        in >> md.n >> md.m;
        if (md.n < 0) md.n = 0;
        if (md.m < 0) md.m = 0;
        md.pj.assign((size_t)md.n * md.m, 0);
        for (int i = 0; i < md.m; ++i)
            for (int j = 0; j < md.n; ++j) {
                long long v = 0;
                in >> v;
                md.pj[(size_t)j * md.m + i] = v;
            }
        md.comp.assign(md.m, 0);
        md.cnt.assign(md.n, 0);
        Solution t = md.trivial();
        double c = md.flowtime(t);
        md.penalty = 10.0 * (std::abs(c) + 1.0);
        return md;
    }

    Solution trivial() const {
        Solution s(1);
        s[0].resize(n);
        for (int j = 0; j < n; ++j) s[0][j] = j;
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

    double flowtime(const Solution& s) const {
        if (s.empty() || m == 0) return 0.0;
        std::fill(comp.begin(), comp.end(), 0LL);
        long long total = 0;
        for (int j : s[0]) {
            if (j < 0 || j >= n) continue;
            const long long* p = &pj[(size_t)j * m];
            long long prev = 0;
            for (int i = 0; i < m; ++i) {
                long long st = comp[i] > prev ? comp[i] : prev;
                prev = st + p[i];
                comp[i] = prev;
            }
            total += prev;
        }
        return (double)total;
    }

    double perm_violation(const Solution& s) const {
        std::fill(cnt.begin(), cnt.end(), 0);
        long long bad = 0;
        if (!s.empty()) {
            for (int j : s[0]) {
                if (j < 0 || j >= n) { ++bad; continue; }
                if (cnt[j] > 0) ++bad;  // repetición de más
                ++cnt[j];
            }
        }
        for (int j = 0; j < n; ++j)
            if (cnt[j] == 0) ++bad;     // falta
        // listas extra (más de una) también se consideran mal formadas
        if (s.size() > 1) {
            for (size_t k = 1; k < s.size(); ++k) bad += (long long)s[k].size();
        }
        return (double)bad;
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
