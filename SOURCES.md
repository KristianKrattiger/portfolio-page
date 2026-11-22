# SOURCES.md — every file consulted (walk of 2026-11-20, extended 2026-11-22)

Git sources were read with `git show <sha>:<path>` / `git log` at the recorded SHA. For a git
file, "mtime" means the commit date of the snapshot, since a committed file has no filesystem
mtime of its own. Non-git files show their filesystem mtime. Paths are relative to `~` (the
user's home folder).

## Repo snapshots (branch, SHA, dirty state recorded before reading)
| Repo | Branch @ SHA | Commit date | Working tree |
|---|---|---|---|
| ~/Projects/GIN | main @ 84abb9a | 2026-10-04 | clean |
| ~/Projects/GIN | docs/gin-15-clean-answer @ 20e6372 (worktree .worktrees/gin-15) | 2026-10-03 | not inspected; read via git show |
| ~/orca/workspaces/GIN/wobbegong | gin-project-review @ 84abb9a | same commit | clean; nothing read here beyond `ls` |
| ~/Projects/receipts | main @ 9a0eeb8 | 2026-10-01 | dirty: untracked frontier.txt, small.txt (NOT read) |
| ~/Projects/assay | main @ 2b6878e | 2026-10-03 | clean; no git remote |
| ~/Projects/sear-demo | main @ 730ad1d | 2026-10-09 | dirty: untracked .claude/ (not read), runs/ (read 2 logs) |
| ~/Projects/Latch | main @ 3a76b7b | 2026-11-09 | clean |
| ~/orca/workspaces/GIN/Additonal-testing (added 2026-11-22) | alewife @ bc5b455 (2 commits after 84abb9a; on no remote) | 2026-11-22 | clean; read via git show from ~/Projects/GIN |
| ~/Projects/PriceRiot (added 2026-11-22) | main @ 2870b22 | 2026-07-23 | clean |
| ~/orca/workspaces/ISDS454_QSR_ERP/ideas (added 2026-11-22) | checkout on extensions-plan @ 35eec27; main @ 72a912e read via git show | 2026-11-16 / 2026-11-11 | clean |
| ~/Projects/ISDS309_TunedIn (added 2026-11-22) | not a git repo (git resolves to the home-folder repo, which has no commits) | — | n/a |
| ~/orca/workspaces/Latch/G2-GPU-Testing | study3-agent-gate @ cdcd512 | 2026-11-17 | DIRTY: modified OPERATORS.md, data/finqa_coverage_results.json, docs/POSTMORTEM.md, gate.py, harness.py, study2 files, study3/analysis/dryrun_report.txt, test_gate.py; untracked paper/. Only committed content was used (git show cdcd512:...). |

## Files consulted
| Path | mtime / snapshot | Supported |
|---|---|---|
| GIN README.md | 84abb9a | gin-sear-decode-constraint, gin-nc-baseline notes, gin-federation, gin-tailscale-mesh, gin-judge-capability context, gin-phase4 |
| GIN sear/processor.py (docstring, class and cursor logic, grep) | 84abb9a | gin-sear-decode-constraint |
| GIN gin/bookkeeper/bookkeeper.py, __init__.py; tests listing | 84abb9a | gin-bookkeeper |
| GIN data/eval_runs/20260702T012203Z/meta.json, metrics.json | 84abb9a | gin-nc-baseline |
| GIN data/eval_runs/20260705T043114Z/meta.json, metrics.json | 84abb9a | gin-divergence-realtext |
| GIN data/eval_runs/20260705T211452Z/meta.json, metrics.json | 84abb9a | gin-divergence-realtext |
| GIN corpus_node1/2/3.json (headers only) | 84abb9a | dataset provenance for federation/divergence |
| GIN data/eval_runs/20260714T175645Z/federation_metrics.json | 84abb9a | gin-federation |
| GIN data/eval_runs/20260716T095519Z, 095704Z peer_selection_metrics.json | 84abb9a | gin-federation |
| GIN data/eval_runs/20260713T092010Z, 190431Z, 192930Z, 223653Z escalation_judge_metrics.json | 84abb9a | gin-judge-capability |
| GIN data/frames/encoder_sweep.json | 84abb9a (added 22a16a9, 2026-07-25) | gin-encoder-sweep |
| GIN data/eval_runs/20260725T093515Z/frame_detector_metrics.json | 84abb9a | gin-frame-detector-leak |
| GIN docs/superpowers/specs/2026-07-26-same-story-stance-channel-design.md | 84abb9a | gin-cartographer-stance |
| GIN docs/superpowers/specs/2026-07-27-quantity-hedge-word-stopword-design.md | 84abb9a | gin-cartographer-stance |
| GIN docs/superpowers/specs/2026-07-24-bi-encoder-frame-detector-design.md | 84abb9a | gin-frame-detector-leak, gin-framing-curator |
| GIN docs/superpowers/specs/2026-10-04-sear-relation-decline-design.md | 84abb9a | gin-decline-eval |
| GIN docs/node6-collaborator-setup.md | 84abb9a (9d6b6af, 2026-07-28) | gin-node6 |
| GIN docs/curator-labeling-guide.md (grep) | 84abb9a | gin-framing-curator |
| GIN docs/GIN_10_Epistemic_Council.md (front matter) | 84abb9a | gin-epistemic-council |
| GIN docs/GIN_15_Clean_Answer.md (front matter, abstract) | docs/gin-15-clean-answer @ 20e6372 | gin-15-clean-answer |
| GIN data/curator/node5_events.yaml (head) | 84abb9a | synthetic status of node5 |
| receipts README.md | 9a0eeb8 | receipts-pipeline, receipts-tesla-ledger, receipts-source-refusals, receipts-tests |
| receipts reports/tesla-fsd.json | 9a0eeb8 | receipts-tesla-ledger (row counts, DISPUTED row quotes) |
| receipts docs/superpowers/specs/2026-09-25-relation-measure-check-design.md | 9a0eeb8 | receipts-relation-check |
| assay README.md, CHANGELOG.md, tree listing | 2b6878e | assay-library, assay-testing |
| sear-demo README.md | 730ad1d | sear-demo-pipeline, sear-demo-results, sear-poisoned-fork, sear-conflict-fork |
| sear-demo config/default.yaml | 730ad1d | sear-demo-pipeline (models) |
| sear-demo runs/8a165f6-base/corpus_stdout.txt | 2026-10-07 10:09 (untracked) | sear-demo-results |
| sear-demo runs/8a165f6-base/poisoned_stdout.txt | 2026-10-07 10:20 (untracked) | sear-poisoned-fork |
| Latch README.md, docs/HISTORY.md | 3a76b7b (identical at cdcd512) | latch-gated-slm-chain |
| Latch docs/POSTMORTEM.md | cdcd512 | latch-pilot-killed |
| Latch PREREG.md | cdcd512 (unchanged since 37b8a9c) | latch-pilot-killed criterion, latch-gated-slm-chain |
| Latch paper.tex (title, abstract) | cdcd512 (added 745d691) | latch-paper, McNemar disagreement |
| Latch study2/phase2/analysis/phase2_report.txt, study2/PREREG-2.md | cdcd512 | latch-study2-agreement |
| Latch study3/RESULTS.md | cdcd512 | latch-study3-agent-gate |
| Latch git log --all | — | commit dates, 4adbb01 G3 KILL |
| ~/Monolith/AGENTS.md | 2026-10-28 17:52 | vault house rules (read-only behavior) |
| ~/Monolith/_meta/REGISTRY.md (grep "sprawl") | 2026-10-28 15:19 | sprawl concept exists |
| ~/Monolith/CALICHE/Projects/GIN/GIN.md | 2026-10-24 04:50 | gin-phase4 (closed 2026-10-23), slice list for home paragraph |
| ~/Monolith/CALICHE/Projects/GIN/SEAR.md, Assay.md, Cartographer-Bookkeeper Gate.md, IDF Divergence Gate.md, Typed Refusal.md | 2026-10-24 12:13 | orientation only; no entry relies on them alone |
| ~/Monolith/CALICHE/Projects/Latch/Latch.md | 2026-11-11 16:39 | cross-check of G3 numbers, McNemar 0.167 |
| ~/Monolith/CALICHE/Projects/receipts/receipts.md | 2026-10-24 04:50 | receipts-tests (846) disagreement |
| ~/Monolith/CALICHE/Projects/sear-demo/sear-demo.md | 2026-10-24 01:46 | sear-demo-status (tests not run per author) |
| ~/Monolith/CALICHE/Projects/PROJECTS_INDEX.md | 2026-10-23 00:44 | orientation only |
| PriceRiot README.md, IMPLEMENTATION_STATUS.md, requirements.txt | 2870b22 | priceriot-engine, priceriot-pos-etl, priceriot-analysis-apps, priceriot-not-built; skills (analytics stack, Streamlit) |
| PriceRiot tree listing (cxx/bindings, python/ingestion, python/dashboard, python/webapp, notebooks, tests); grep of python/webapp/app.py for "workers"; git log | 2870b22 | same entries; no workers route |
| PriceRiot data/runs/sanity_13day/aggregate_summary.json (opened, not used: a 3-run sanity check, not a measurement) | 2870b22 | nothing |
| QSR ERP README.md | 35eec27 (checkout) and 72a912e | qsr-erp-database, qsr-erp-framework |
| QSR ERP docs/superpowers/specs/2026-10-07-qsr-erp-database-design.md (head) | 72a912e | qsr-erp-database |
| QSR ERP tree listing (db/, scripts/, app/framework/, app/screens/README.md, tests/); git log main (authorship counted, names not recorded) | 72a912e | qsr-erp-database, qsr-erp-framework, qsr-erp-role |
| QSR ERP docs/superpowers/specs/2026-11-16-extensions-plan.md (head) | extensions-plan @ 35eec27 | qsr-erp-extensions |
| Author's statement of QSR ERP role, in conversation | 2026-11-22 | qsr-erp-role (teammates' names given but deliberately not recorded anywhere) |
| ~/Projects/ISDS309_TunedIn/README.md; ISDS309.Core listing | mtime 2026-09-15 / 2026-10-20 | tunedin-app, tunedin-gaps |
| GIN data/eval_runs/portfolio_stress*/report.md (4 runs) and metrics.json (first and general runs; live_windows_llm rows) | alewife @ bc5b455 | gin-stress-first-run, gin-stress-patched, gin-stress-sear-decode, gin-stress-verifier-probes, gin-stress-live-llm |
| GIN gin/eval/stress_corpora.py (docstring) | alewife @ bc5b455 | benchmark origin, 'blind-style' disagreement |
| GIN scripts/eval_portfolio_stress.py (function list, decode loop seed) | alewife @ bc5b455 | gin-stress-sear-decode (stand-in tokenizer, hash() seed) |
| GIN git diff 84abb9a..bc5b455 -- gin/cartographer/quantity.py (added lines grep); git show --stat of both commits | alewife @ bc5b455 | gin-stress-patched (units tailored to the set) |
| ~/OneDrive/Desktop/Orca Workspaces/Sprawl/ | dir mtime 2026-11-11 00:14 | EMPTY; seed entry 17's note not found |

## Searches run (grep only, results not otherwise read)
- "smuggl|6 of 21|6/21" over GIN docs and ~/Monolith/Sessions: no hits (gin-smuggled-pairs stays UNKNOWN evidence).
- "three-arm|token budget|gated chain|SLM" over vault projects/ideas/sessions, Latch, GIN docs: hits only in Latch docs and one GIN plan.
- "sprawl" over the vault: hit file names in Journey/, Inbox/, Career/, Polymathy/, Ideas/: **skipped unread** (personal or job-search material).

## Skipped without reading (recorded only)
- ~/Monolith/Career/ (including a file about job openings), CSUF/, CALICHE/Journey/, Frameworks/ (one line seen in a grep hit for "sprawl", not used), Inbox/, Polymathy/, Ideas/ (titles listed only).
- Distilled session files whose titles mention team roles/outreach or internship: not opened.
- ~/Projects/attest, backstop, backstop-diagnosis, intake, claim-record-master(.zip), RestaurantDatabaseProject: not opened (outside scope; may touch excluded topics).
- ~/exopere: folder name seen in a home-directory listing; not opened.
- receipts untracked frontier.txt, small.txt; sear-demo .claude/; Latch worktree paper/ and uncommitted diffs.
