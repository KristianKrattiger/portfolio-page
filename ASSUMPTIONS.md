# ASSUMPTIONS.md — calls made without asking

1. **~/portfolio = C:\Users\krist\portfolio.** The session's working directory was an Orca worktree
   (orca/workspaces/portfolio-page/capricorn). The brief says "write only under ~/portfolio", so
   everything is there. The worktree was left untouched. ~/portfolio is its own git repo with local
   commits only and no remote.
2. **Ledger format.** `content/ledger.yaml` is YAML 1.2 written in its JSON-compatible subset so the
   stdlib parses it with zero dependencies. Full-line `#` comments are allowed.
3. **One state per entry.** Seed entry 8 ("IN-PROGRESS + BLOCKED") became BLOCKED.
4. **Seed entries split or merged.** Seed 6 was split into gin-encoder-sweep and gin-judge-capability,
   because they are two experiments. Seed 1's reported numbers became gin-nc-baseline. The
   "model-independent" claim moved to gin-divergence-realtext, where the repo actually makes it.
5. **Seed 16 = Latch study 3.** I read the "SLM reasoning-gate arm for tool calling / parameter
   verification" as the preregistered BFCL provenance-gate study on branch study3-agent-gate. Its
   committed null result (2026-11-17) supersedes "no results reported". If that is wrong, the entry
   needs splitting.
6. **sear-demo numbers stay BUILT, not MEASURED.** All seven fields are known, but the README calls
   every number "a smoke test, not a measurement", and the primary logs are untracked by git. I
   followed the author's own framing.
7. **Spec "Results" sections are tier 2.** Numbers recorded in a spec's Results section (stance
   channel, decline eval, relation check, frame detector leak) are AUTHOR-REPORTED, even with full
   detail, because I did not open a committed eval output containing them.
8. **as_of** is the date of the evidence snapshot: the commit, run date or note date. For seed-only
   entries it is the date the seed was received (2026-11-20), and that is labeled. Month-precision
   dates count from the 1st for STALE (conservative).
9. **Pinetree.** I kept only the README's own wording ("Written for the Pinetree Research challenge").
   The submission stays AUTHOR-REPORTED. I avoided the word "internship" as job-search adjacent.
10. **attest / claim-record / "business plan".** The compliance-venture idea is excluded, and I could
    not rule out that these are it. They are never named on the site; the verifier enforces this.
11. **Public links.** I link to GitHub only for GIN and receipts (the seed and vault call them public)
    and only at SHAs found on a remote-tracking branch. sear-demo, Latch and assay are shown as
    path + SHA text, and their visibility is marked UNKNOWN.
12. **Hidden entries** (surfboards, 280Z) are in the ledger with visibility hidden. They are excluded
    from every page and from ledger.json, and their count is shown.
13. **Hosting.** The machine is Windows 11, so there is no systemd or launchd. Persistence uses a
    user-level Startup-folder launcher (no admin). Tailscale is not installed, so the site binds
    127.0.0.1 only. Port 8787.
14. **Name/line/education** come from the brief (the author's own framing). Contact and "what I'm
    looking at next" are UNKNOWN.
15. **JS-off check.** This Edge build ignores JS-disable switches for --dump-dom, so the check renders
    a copy of dist/ with every `<script>` removed. The site has no `<noscript>` content, so this is
    equivalent.
16. **Process.** The brief's own process (SPEC, PLAN, tests first, review, live check) was followed
    instead of an interactive brainstorming round, because the brief says not to block on questions.
17. **Restyle (2026-11-22).** Direction chosen by the author from mockups: concrete wall, punched
    tags, label tape; colour = family (done / failed / unfinished). Agent's calls: Barlow Condensed,
    TTF served as-is, grain removed, square punch hole (keeps the no-rounded-corners rule), numbers
    and evidence folded under each tag on the ledger (open on project pages).
18. **Tagline** is option 2 as picked by the author. "Business technologist" was dropped at the
    author's request.
19. **QSR ERP role** comes from the author's own statement (AUTHOR-REPORTED). The commit log
    supports authorship of main only. Teammates' names were given in conversation and are kept
    out of every file; the verifier checks for them by hash.
20. **QSR ERP evidence** is pinned to main @ 72a912e (on origin/main), not the checked-out
    extensions-plan branch, except for the extensions spec, which exists only there.
21. **Skills** list is the author's; a skill links to a ledger entry only where that entry's evidence
    shows it in use. "Analytics stack" was read as the Python libraries in PriceRiot's requirements.
22. **PriceRiot's sanity-run numbers** (3 seeded runs) were not added: a sanity check, not a
    measurement, and the author did not report them as results.
