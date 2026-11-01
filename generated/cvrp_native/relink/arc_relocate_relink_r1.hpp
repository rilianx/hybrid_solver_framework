// COMPONENT: {"name": "arc_relocate_relink", "slot": "relink", "params": {"strong_prob": {"type": "float", "range": [0.0, 1.0]}, "allow_new_route": {"type": "int", "range": [0, 1]}}}
class ArcRelocateRelink : public hsf::Relink<CVRP> {
public:
    using Sol = CVRP::Solution;
    ArcRelocateRelink(const CVRP& m, double sp, int anr) : m_(m), sp_(sp), anr_(anr) {}

    int distance(const Sol& a, const Sol& b) override {
        build(a, sa_, pa_, false);
        build(b, sb_, pb_, false);
        return count();
    }

    Sol step(const Sol& cur, const Sol& guide, Rng& rng) override {
        int n = m_.n;
        build(guide, sb_, pb_, false);
        build(cur, sa_, pa_, true);
        int d = count();
        if (d == 0) return guide;
        cands_.clear();
        int best = 0;
        for (int v = 1; v <= n; ++v) {
            if (rt_[v] < 0) continue;
            int p = pa_[v], s = sa_[v];
            if (p < 0 || s < 0) continue;
            int pg = pb_[v], sg = sb_[v];
            bool aloneDone = false;
            if (pg >= 0 && pg != p) {
                if (pg == 0) { if (anr_) { tryAlone(v, p, s, best); aloneDone = true; } }
                else if (rt_[pg] >= 0 && sa_[pg] >= 0) tryIns(v, p, s, pg, sa_[pg], 1, pg, best);
            }
            if (sg >= 0 && sg != s) {
                if (sg == 0) { if (anr_ && !aloneDone) tryAlone(v, p, s, best); }
                else if (rt_[sg] >= 0 && pa_[sg] >= 0) tryIns(v, p, s, pa_[sg], sg, 2, sg, best);
            }
        }
        Sol out;
        if (!cands_.empty()) {
            const Cand* ch;
            if (rng.uniform() < sp_) {
                int cnt = 0; ch = &cands_[0];
                for (const auto& c : cands_) if (c.del == best) { ++cnt; if (rng.below(cnt) == 0) ch = &c; }
            } else {
                ch = &cands_[rng.below((int)cands_.size())];
            }
            int v = ch->v, rv = rt_[v], pv = ps_[v];
            out = cur;
            out[rv].erase(out[rv].begin() + pv);
            if (ch->mode == 0) {
                out.push_back({v});
            } else {
                int x = ch->ref, r = rt_[x];
                int idx = ps_[x] - ((r == rv && ps_[x] > pv) ? 1 : 0);
                if (ch->mode == 1) out[r].insert(out[r].begin() + idx + 1, v);
                else out[r].insert(out[r].begin() + idx, v);
            }
            out.erase(std::remove_if(out.begin(), out.end(), [](const std::vector<int>& r) { return r.empty(); }), out.end());
        } else {
            if (!fallback(cur, rng, out)) return guide;
        }
        int dn = distance(out, guide);
        if (dn == 0 || dn >= d) return guide;
        return out;
    }

private:
    struct Cand { int v, mode, ref, del; };

    bool isG(int u, int w) const {
        if (u == 0) return w >= 1 && pb_[w] == 0;
        return sb_[u] == w;
    }
    int remA(int u, int w) const { return isG(u, w) ? 1 : -1; }
    int addA(int u, int w) const { return isG(u, w) ? -1 : 1; }
    int removalDelta(int v, int p, int s) const {
        int del = remA(p, v) + remA(v, s);
        if (!(p == 0 && s == 0)) del += addA(p, s);
        return del;
    }
    void tryAlone(int v, int p, int s, int& best) {
        int del = removalDelta(v, p, s) + addA(0, v) + addA(v, 0);
        if (del < 0) { cands_.push_back({v, 0, 0, del}); best = std::min(best, del); }
    }
    void tryIns(int v, int p, int s, int a, int b, int mode, int ref, int& best) {
        int del = removalDelta(v, p, s) + remA(a, b) + addA(a, v) + addA(v, b);
        if (del < 0) { cands_.push_back({v, mode, ref, del}); best = std::min(best, del); }
    }

    bool fallback(const Sol& cur, Rng& rng, Sol& out) {
        int n = m_.n;
        fb_.clear();
        for (int c = 1; c <= n; ++c) {
            if (sa_[c] == sb_[c] || rt_[c] < 0) continue;
            int t = sb_[c];
            if (t == 0) fb_.push_back(c);
            else if (t >= 1 && t <= n && rt_[t] >= 0 && (rt_[t] != rt_[c] || ps_[t] > ps_[c])) fb_.push_back(c);
        }
        if (fb_.empty()) return false;
        int c = fb_[rng.below((int)fb_.size())], t = sb_[c];
        int r1 = rt_[c], i = ps_[c];
        const auto& R1 = cur[r1];
        int L1 = (int)R1.size();
        out.clear();
        out.reserve(cur.size() + 2);
        if (t == 0) {
            for (int r = 0; r < (int)cur.size(); ++r) if (r != r1 && !cur[r].empty()) out.push_back(cur[r]);
            out.emplace_back(R1.begin(), R1.begin() + i + 1);
            if (i + 1 < L1) out.emplace_back(R1.begin() + i + 1, R1.end());
        } else {
            int r2 = rt_[t], j = ps_[t];
            for (int r = 0; r < (int)cur.size(); ++r)
                if (r != r1 && r != r2 && !cur[r].empty()) out.push_back(cur[r]);
            if (r2 == r1) {
                std::vector<int> h(R1.begin(), R1.begin() + i + 1);
                h.insert(h.end(), R1.begin() + j, R1.end());
                out.push_back(std::move(h));
                if (j > i + 1) out.emplace_back(R1.begin() + i + 1, R1.begin() + j);
            } else {
                const auto& R2 = cur[r2];
                std::vector<int> h(R1.begin(), R1.begin() + i + 1);
                h.insert(h.end(), R2.begin() + j, R2.end());
                out.push_back(std::move(h));
                if (j > 0) out.emplace_back(R2.begin(), R2.begin() + j);
                if (i + 1 < L1) out.emplace_back(R1.begin() + i + 1, R1.end());
            }
        }
        return true;
    }

    int count() const {
        int d = 0;
        for (int c = 1; c <= m_.n; ++c) {
            if (sa_[c] != -1) {
                if (sa_[c] != sb_[c]) ++d;
                if (pa_[c] == 0 && pb_[c] != 0) ++d;
            }
            if (sb_[c] != -1) {
                if (sb_[c] != sa_[c]) ++d;
                if (pb_[c] == 0 && pa_[c] != 0) ++d;
            }
        }
        return d;
    }

    void build(const Sol& s, std::vector<int>& su, std::vector<int>& pr, bool pos) {
        int n = m_.n;
        su.assign(n + 1, -1);
        pr.assign(n + 1, -1);
        if (pos) { rt_.assign(n + 1, -1); ps_.assign(n + 1, -1); }
        for (int r = 0; r < (int)s.size(); ++r) {
            const auto& R = s[r];
            int L = (int)R.size();
            for (int i = 0; i < L; ++i) {
                int c = R[i];
                if (c < 1 || c > n) continue;
                su[c] = (i + 1 < L) ? ((R[i + 1] >= 1 && R[i + 1] <= n) ? R[i + 1] : -2) : 0;
                pr[c] = (i == 0) ? 0 : ((R[i - 1] >= 1 && R[i - 1] <= n) ? R[i - 1] : -2);
                if (pos) { rt_[c] = r; ps_[c] = i; }
            }
        }
    }

    const CVRP& m_;
    double sp_;
    int anr_;
    std::vector<int> sa_, pa_, sb_, pb_, rt_, ps_, fb_;
    std::vector<Cand> cands_;
};

std::unique_ptr<hsf::Relink<CVRP>> make_component(const CVRP& model, const hsf::Config& params) {
    int anr = (int)params.get("allow_new_route", 1.0);
    anr = anr < 0 ? 0 : (anr > 1 ? 1 : anr);
    return std::make_unique<ArcRelocateRelink>(model, params.get("strong_prob", 0.3), anr);
}
