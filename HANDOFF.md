# cinderhaven-promo-incrementality — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-08-17 — Project initialized

**Started from:** `cinderhaven-promo-response` v0.1.0, shipped and tagged.
Its HANDOFF.md carries the consumer contract this project builds on. Nothing
existed here before this session.

**Did:**
- Scaffolded the repo: CLAUDE.md, PLAN.md, HANDOFF.md, DECISIONS.md,
  FAILURES.md, README.md, `src/CLAUDE.md`, `tests/CLAUDE.md`, `.gitignore`.
- Recorded the consumer contract in CLAUDE.md so it survives without
  re-reading the other repo.
- Logged three settled decisions and one open one.

**The finding that shaped the scaffold:** `assert_no_truth_access` parses
source with `ast`. It can audit `.py` files and nothing else. So the hard
requirement — CI runs that gate on all estimation code — **forces the
estimation engine to be Python**. That is a constraint, not a preference,
and it narrows the stack question to the front end alone. Logged in
DECISIONS.md.

**A second leak the gate does not catch, worth knowing before any estimator
is written:** the gate denies `truth`. It does not deny
`cinderhaven_promo_response.config`, which holds the generator's own
coefficients — the answer key by another route. CLAUDE.md prohibits it
explicitly because nothing automated will.

**State:** Scaffold only. No stack, no dependency manifest, no CI, no code.
Three candidate stacks are written up in DECISIONS.md as a pending decision,
with the constraints and the "does this compute at request time?" prior
question stated, so the planning process starts from there rather than cold.

**Next:** Run the planning process to settle the stack — `/clarify`, then
`/office-hours`, then `/plan-ceo-review` and `/plan-eng-review`. Log the
outcome in DECISIONS.md naming the rejected alternatives, not just the
winner. Then the repo skeleton, then CI with the truth gate proven to fail
before any estimator exists.

---

## 2026-08-17 15:52

**What changed:** `/clarify` run on the stack decision; requirements appended
to PLAN.md as `## Goal — clarified 2026-08-17`.

**Why:** DECISIONS.md framed the stack question around scrollytelling and a
1.34M-row browser payload. Both turned out to be assumptions, not requirements,
and the real deciding constraint — persistent cross-view filter state — wasn't
recorded at all.

**State:** Requirements settled: client-facing flagship, no landing page in
this repo, build-time precomputed artifacts only (DuckDB-WASM out), 30-second
verdict on first paint, cross-view filters with deep-linkable URLs, open-ended
timeline. Dash eliminated. Stack still unchosen — DECISIONS.md entry remains
open and untouched, correctly. No code, no manifest, no CI.

**Next:** Run `/office-hours` to stress-test the concept, carrying two items:
the recommendation now points at SvelteKit (cross-view state, not narrative),
and mobile is still undecided — the 375px cannibalization matrix is unresolved.

---
## 2026-08-17 16:51 — backfill (session ended without /wrap)

**What changed:** `/office-hours`, `/plan-ceo-review` and `/plan-eng-review`
run; scope collapsed to three views; stack decided.

**Why:** Entry written 2026-08-18 to close a hole — three commits landed
after the 15:52 entry and none were logged. No work was lost; the decisions
are all in DECISIONS.md. The log just didn't record them.

**State:** Stack settled — SvelteKit + D3, static, Cloudflare Pages; the
PENDING entry is struck through, not deleted. Scope is three views, not six.
Positioning, external-validity, mobile-split, integer-cents, artifact-label
and dependency-direction decisions all logged. Still docs-only: no manifest,
no CI, no code.

**Next:** Repo skeleton — task 2 in PLAN.md.

---

## 2026-08-18 09:45

**What changed:** Settled how the upstream package is installed: git URL
pinned to a commit SHA, not an editable local path and not a vendored wheel.

**Why:** An editable install off `../cinderhaven-promo-response` would make
"pinned at v0.1.0" describe the working tree rather than anything CI can
reproduce — it fails the pin decision it appears to satisfy. SHA over tag
name because annotated tags are mutable; the fleet pins SHAs everywhere else.

**State:** Nothing written yet. The SHA supplied in session, `a237910`, was
checked and is **wrong** — it is an ancestor of `v0.1.0` dated 75 minutes
before it, predating the plausibility audit and the retired-figure scan. The
v0.1.0 commit is `70021d4d472bdf4ab5132778472b4ca8a95fe0e8`. Still docs-only:
no manifest, no CI, no code. `cinderhaven_promo_response` is not importable
here — no venv exists yet.

**Next:** Write `pyproject.toml` pinning
`cinderhaven-promo-response @ git+https://github.com/MsShawnP/cinderhaven-promo-response@70021d4`,
plus pytest and ruff. Then create `.venv` and confirm `pr.load()` runs.

---

## 2026-08-18 13:31

**What changed:** Task 3 done — two-job CI live, truth gate proven green and
the data contract proven red for the documented reason, with real runner
evidence.

**Why:** Local green proved the gate function; only a push proves the workflow
wiring, the secret, and the `--no-deps` install work on a runner. It took three
runs to get clean evidence — each failure was a real setup defect the CI caught.

**State:** Green — `truth-gate` (AST over `src/`, `--no-deps`, pandas-absent
asserted; demonstrated to fail via a planted `src/` violation plus two permanent
fixtures covering both channels). Red by design — `data-contract`, failing only
at the test step on the upstream `FIGURES.md` cold-cache defect, after auth +
install + pin-verification all pass. Three setup bugs found and fixed along the
way: secret on the wrong repo (upstream, not consumer) → added a token preflight;
secret name mismatch (`PROMO_RESPONSE_READ` vs `..._TOKEN`) → aligned code to the
existing name; token regenerated and re-verified on a runner. Exemption list is
now a named file (`src/incrementality/accuracy.py`), not a directory, with an
invariant test. 10 tests pass locally, ruff clean. Untouched: SvelteKit scaffold,
any estimator, the walking skeleton.

**Next:** Task 5 — the walking skeleton. One Python-computed number → JSON →
rendered by the real front end → deployed to a real static host. This is what
actually answers "is this stack right?" and is the cheapest insurance against
the stall risk. Scaffold SvelteKit + adapter-static first.

---

## 2026-08-18 14:40

**What changed:** Re-pinned the upstream package to v0.1.1 (7cfe95c); the
data-contract CI job is now green cold. CI is fully green.

**Why:** Upstream v0.1.1 fixed the FIGURES.md cold-cache crash that made the
data job red by design. Moving the pin closes the loop the red job held open.

**State:** pyproject.toml pins 7cfe95c (v0.1.1, peeled commit) with updated
human comments; test_data_contract.py asserts 0.1.1 and its docstring records
the fix; CI job comments no longer say "expected red". Full consumer suite: 10
passed on a cold cache — every pr.load() test included. Truth gate still green.
Repo skeleton, CI, and the re-pin are all done. Untouched: SvelteKit scaffold,
any estimator, the walking skeleton.

**Next:** Task 5 — the walking skeleton. One Python-computed number → JSON →
SvelteKit (adapter-static) → Cloudflare Pages. Scaffold the front end first.

## 2026-08-19 11:40

**What changed:** Walking skeleton built end to end — Python computes observed
facts → deterministic JSON → SvelteKit adapter-static prerenders them to static
HTML. Both halves pushed (e3d2bd4, 58f3be9). Deploy is the only remaining step.

**Why:** Task 5 is the arc's real "is this stack right?" test and the cheapest
insurance against the stall. Proving the pipe before any estimator means the
stack fails fast and cheap if it's going to.

**State:** Working — full pipe verified: real numbers (13,838,493 units, 131
events, 1,340,462 rows, v0.1.1) baked into static build/index.html at prerender
time, not fetched at runtime. `scripts/build.sh` runs pipeline-first with set -e
so no stale artifact ships. 16 Python tests green, ruff clean, front-end build
green. Two determinism bugs caught by tests, not shipped (CRLF translation;
redundant int cast). No D3 yet (renders one number; dep arrives with first
chart). Untouched: any estimator, Method 0, ROI Scorecard, accuracy view.
Pending on Shawn: (1) platform paste push — committed 421beef in the platform
repo, held; (2) Cloudflare deploy creds.

**Next:** Deploy via Path B — build in GitHub Actions, `wrangler pages deploy
web/build`. Blocked until Shawn creates a Cloudflare API token + account ID and
adds them as CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID repo secrets, plus a
Direct-Upload Pages project named cinderhaven-promo-incrementality. Then write
the deploy job (folding in the Node-20 action-version bump).

## 2026-08-19 13:27

**What changed:** Walking skeleton deployed and verified live — CI's deploy job
builds and ships to Cloudflare Pages; the served HTML carries the pipeline's
prerendered numbers. Task 5 done, deploy included.

**Why:** Closes the arc's real "is this stack right?" question with a live URL,
not an assertion. Biggest cut yet to the named stall risk.

**State:** Green end to end. https://cinderhaven-promo-incrementality.pages.dev
returns 200 with 131 / 1,340,462 / 13,838,493 / 0.1.1 baked into static HTML at
prerender. CI three jobs green (truth-gate, data-contract, deploy). Deploy job
gated needs:[truth-gate,data-contract] + push-to-main; preflights now name every
credential failure (wrong-repo PAT → empty token → malformed account id, each
caught with a clear message). Platform paste pushed (421beef). This .pages.dev
is the unstyled plumbing check — NOT the flagship; Lailara design system + the
two-method public-deploy gate apply before any lailarallc.com subdomain.
Untouched: any estimator, ROI numbers, truth, the accuracy view.

**Next:** Slice 1 — ROI Scorecard on Method 0. Pre-registration rule governs
commit order: Commit 1 is docs/estimators.md (Method 0 spec, cited, no code),
committed before any code loads truth. Then observed-only estimation pipeline
with the exact portfolio reconciliation test, then the Scorecard view. Truth
gate stays green throughout; no accuracy numbers in this slice.

## 2026-08-19 17:07

**What changed:** Slice 1 spec frozen — ROI framing A confirmed (#7), giveaway
share added; upstream shipped economics() (v0.2.0 → v0.2.1 fix), consumer pinned
to v0.2.1, CI fully green. Ready to write Method 0 pipeline code.

**Why:** #7 was the last open modeling fork (manufacturer margin vs retail);
confirming it froze the pre-registration spec so the estimator can be built and
tagged as blindness evidence. economics() is the demand-free margin basis.

**State:** Frozen spec at docs/estimators.md (framing A: numerator = mfr margin
wholesale−COGS on incremental units; giveaway = decomposition of accrued_cost,
displayed as % of trade dollars). Upstream v0.2.1 (economics() + lazy-pandas fix
+ regression test, 254 tests). Consumer pinned 11caa13, all 3 CI jobs green.
Commits 1–2 of slice 1 are spec-only, no estimation code yet. Untouched: the
Method 0 pipeline, the import-ban check, the Scorecard view.

**Next:** Method 0 pipeline. First land the supplementary import-ban check
(bans config/constants in src/, alongside the truth gate), then the estimation
module: baseline → incremental units → margin (via economics()) → ROI →
portfolio roll-up with the exact reconciliation test. Then the artifact writer.

## 2026-08-19 17:22 — /wrap

**Started from:** Docs-only repo, stack decided; task 2 (skeleton) next.

**Did:** Skeleton (task 2), two-job CI with truth gate proven-to-fail (task 3),
walking skeleton deployed live to Cloudflare Pages (task 5). Three upstream
releases — v0.1.1 (FIGURES.md cold-cache fix), v0.2.0 (economics() accessor),
v0.2.1 (pandas-eager-import regression fix) — consumer re-pinned through each.
Slice 1 pre-registration: froze docs/estimators.md (Method 0), resolved 3
modeling forks (continuous units + integer-cent round-half-even; all-131 with
phantom marked; economics() margin basis), confirmed ROI framing A (#7), landed
the generator-import ban. Platform canonical paragraph pushed at v0.1.1 SHA.

**State:** Consumer pinned upstream v0.2.1, all 3 CI jobs green, skeleton live.
Slice 1 spec frozen + import-ban guardrail in. Upstream v0.2.1, 254 tests.
Untouched: the Method 0 estimation module, the Scorecard view.

**Next:** Write src/incrementality/method0.py — baseline (8-wk pre-period,
promo weeks excluded, insufficiency flag) → incremental units → margin via
economics() → integer-cent round-half-even at row grain → portfolio roll-up
with the EXACT reconciliation test + property tests (sign, phantom→~0 lift,
estimable-count labeling) + giveaway-share per event. Then artifact writer,
then Scorecard view. Tracked guard-gap: deploy token value-validity is only
checkable at runtime (wrangler), not preflighted — acceptable, noted.

## 2026-08-19 (later) — Method 0 pipeline + Scorecard artifact landed

**What changed:** The Method 0 estimation module and the ROI Scorecard artifact
writer are built, tested, and committed (3 commits: 33d59f2 spec correction,
e08532c estimator+tests, 9ee2b84 writer+wiring). Slice 1's pipeline is done end
to end; only the SvelteKit view remains.

**Why:** Slice 1's pipeline — the frozen spec made real. Implemented cold from
`docs/estimators.md` (the spec's own completeness test). One genuine spec bug
surfaced during implementation and was corrected pre-freeze (see below).

**The spec bug — §2.4 giveaway share (asked, user chose volume share).** The
frozen formula divided a *retail* giveaway (`baseline×(regular−promoted)`) by the
*manufacturer* `accrued_cost` — mixed dimensions, "shares" to 936% (clean_winner,
smallest subsidy base). Corrected to `Σ baseline_units / Σ observed_units` over
complied rows (discount is constant within an event, so it cancels). Scan-funded
events keep the "% of trade dollars" copy (accrued = rate×promoted units makes it
exact); fixed-funded are volume-only; net-dip events (share>1) flagged. Logged as
a **pre-freeze correction, not a re-run** (no truth loaded yet). DECISIONS +
FAILURES entries written. Two adjacent gaps also clarified pre-freeze: event
estimability (≥1 sufficient store-event → N_estimable=129) and zero accrued cost
(3 events → ROI null, lost_money still defined).

**State — Method 0 numbers (v0.2.1, this generation):** portfolio ROI 1.132
(naive, expected rosy), net incremental margin $118,200.37, accrued spend
$104,425.13, **64 of 129 estimable events lost money**, 2 of 131 not estimable
(PRE-0048/PRE-0054, series-start). Reconciliation ties exactly (11,820,037 cents,
event-grain == row-grain). **40 tests pass, ruff clean, truth gate + import ban
green over all of src/, artifact byte-identical across builds.** scorecard.json
(scorecard/v1) written to web/src/lib/data/ (gitignored), wired into build.sh as
a pipeline-first step. NOT pushed — CI has not run these commits.

**Untouched:** the SvelteKit Scorecard view (deliberately stopped before it), the
dependency-direction test (PLAN, still `[ ]`), Method 1 (deploy gate needs two
baseline methods), the accuracy view.

**Next:** The ROI Scorecard **view** — SvelteKit consuming scorecard.json. First
paint must satisfy the 30-second rule (verdict line, one chart, three numbers)
before any filter, and the header must fully work at 375px. Ranking is a view
choice (artifact is in canonical promo_id order); non-estimable events shown
unranked and marked; every portfolio figure labeled "of 129 estimable events".
Then the dependency-direction test, then Method 1 (comparable-store) to clear the
two-method public-deploy gate.

## 2026-08-21 — Scorecard view landed (header + ranked list); all pushed, CI green

**What changed:** Built the SvelteKit ROI Scorecard view end to end and pushed
everything. Method 0 pipeline (33d59f2/e08532c/9ee2b84) plus the view: a9fc411
(header) and b2e3c4d (ranked list). All on main, CI green including the Cloudflare
Pages deploy.

**Why:** Closes slice 1's user-visible half — the 30-second verdict front door on
the Method 0 artifact — on the vendored Lailara brand frame. "go — Scorecard view
per PLAN."

**State — the view (web/src/routes/+page.svelte):**
- **Header (30-second surface):** eyebrow "ROI Scorecard · Method 0"; verdict
  "64 of 129 promotions lost money."; three numbers (trade spend $104,425, net
  incremental margin $118,200, portfolio ROI 1.13×); one chart — the 129 estimable
  events by return tier, a red Tokyo "lost money" bar (64) against three teal
  Hong-Kong profit tiers (39/17/9). DOM bars, not SVG (vector-crisp for print,
  natively responsive — deviation from the SVG-charts rule, noted, to meet the
  hard 375px constraint).
- **Ranked list:** 129 estimable events by net margin; net/spend/ROI/giveaway per
  row; lost-money rows carry a Tokyo leading rule + red ROI; the 4 seeded stories
  and phantom/unplanned events badged (marked, NOT claimed "found"); 2 non-estimable
  events listed unranked beneath. Filters DEFERRED (cross-view state = Event Anatomy
  arc).
- **Frame:** vendored lailara-frame.css + 8 self-hosted woff2 into web/static/lailara/;
  brand header/footer in +layout.svelte; canvas on body. Skeleton demo moved to
  /skeleton. Shared formatters in web/src/lib/format.js.
- **Verified (DOM, not screenshot — see limitation):** both fonts load, palette
  correct, no page horizontal scroll at 1280 or 375, header collapses to one column
  on mobile, table scrolls inside its own container, production build bakes all real
  numbers + 129 rows into prerendered HTML.

**Limitation:** the Browser pane was not displayable this session (0-width /
non-compositing), so no screenshot was captured. Everything was verified through
read_page + computed styles + build output. **A human visual review at 1440 and
375 is still owed** before this counts as design-gate-passed. Dev server: `web-dev`
in .claude/launch.json → http://localhost:5173.

**Untouched:** filters, the dependency-direction test (PLAN `[ ]`), Method 1
(deploy gate needs two baseline methods), the accuracy view, the one-timed-session
30-second verification with a trade-marketing person.

**Next:** pick one — (a) the dependency-direction test (small, closes a PLAN item
and a blindness guarantee), (b) Method 1 comparable-store baseline (unblocks the
two-method public-deploy gate), or (c) a human design pass on the Scorecard once
the Browser pane is viewable. Event Anatomy + filters are the following arc.

## 2026-08-21 — Dependency-direction guard + Method 1 pre-registration (§3); blocked on store_card() v0.3.0

**What changed:** Two things. (1) Dependency-direction guard landed (90d0eda):
`tests/test_dependency_direction.py` asserts nothing under `src/` except the
accuracy module imports it — closing the transitive-import hole in the per-file
truth gate, forward-guarding before `accuracy.py` exists, demonstrated-to-fail
with a permanent fixture. (2) Method 1 pre-registered (624d376, tagged
`method1-preregistration`): spec §3 committed before any Method 1 code.

**Why blocked:** Before writing §3 I measured comparable-pool availability
(observed-only). **Same-banner clean control pools are empty for 40/131 events,
<5 for 106/131 (median 2)** — promotions here are banner-wide, so a same-banner
comparable method would exclude ~80% of events. Valid matching must go
cross-banner on store identity (region, format) the observed layer does not carry.
That fired the pre-authorized STOP-AND-ASK; user chose to add an upstream
`store_card()` accessor rather than improvise. Method 1's pipeline is blocked on it.

**State:** §3 registers a comparable-store baseline — per-week comparable-median
counterfactual, matched on region + store_format (`store_card()`) + observed volume
band, cross-banner, `MIN_POOL` + `insufficient_comparable_pool` rider, weaknesses
stated (banner-wide finding included). Money/reconciliation/determinism unchanged
from Method 0. Spec §§3–6 renumbered → 4–7; 4 code/test cross-refs fixed. 43 tests
green, ruff clean, all pushed. DECISIONS logs the `store_card()` demarcation
(identity only; volume tier derived from observed velocity, never on the card) and
parks the indexed diff-in-diff as a **Method 2 candidate**, not a rejected fallback.
`MIN_POOL` + volume band are provisional — set from the matched-pool distribution
once `store_card()` ships, tuned on pool size not error, logged before first scoring.

**Blocking dependency — upstream v0.3.0 (a data-repo session, not this repo):**
`store_card()` — one row per `store_id`: `retailer_id`, `region`, `store_format`.
Pure store-master identity, `economics()`'s demarcation; explicitly **no**
volume/size tier (consumers derive volume from observed units). Own module, no
demand parameters, AST-clean, demand-free import test, wheel-runtime-files rule,
CHANGELOG, full suite, tag v0.3.0, push with tag, report peeled commit SHA for the
consumer re-pin. Then here: re-pin (logged re-run) → `method1.py` → re-score
scorecard with both methods → Method 0/1 toggle with delta → two-method deploy gate
clears.

**Untouched:** `method1.py` (blocked on v0.3.0), the scorecard method toggle, the
accuracy view, filters, Event Anatomy, the human 375px design look (still owed).

**Next:** run the upstream `store_card()` v0.3.0 release in the data-repo session,
then re-pin here and build `method1.py`. Or, in parallel, the accuracy view can
start on Method 0 alone (it only needs one method to score) — but the two-method
deploy gate still holds public launch until Method 1 ships.

## 2026-08-21 — Method 1 shipped end-to-end; two-method deploy gate cleared

**What changed:** The whole Method 1 slice, in order. (1) Re-pin to v0.3.0
(`6556460`, adds `store_card()`); logged re-run; data-contract test asserts v0.3.0
+ the store_card shape. (2) Discovered `store_card()` ships `region` only (no
`store_format`), so §3's match key routes format through a consumer JUDGMENT map
(retailer→class). (3) STOP-AND-ASK: measured that a flat region+format+band match
starves pools (club=Costco, supercenter=Walmart are single-banner classes) — only
57/131 estimable, all four stories dropped. User chose **hierarchical** matching;
amended §3, tagged `method1-preregistration-r2` before writing code. (4) Extracted
the shared roll-up/reconciliation into `common.py` (behavior-preserving; Method 0
numbers unchanged). (5) `method1.py`: per-week comparable-median baseline, region +
format-class + volume band relaxing to region + band, MIN_POOL=5, band [v/2,2v],
`insufficient_comparable_pool` visible exclusions, per-event `match_relaxed_share`
regime dimension. (6) Re-scored the artifact to **scorecard/v2** carrying both
methods. (7) **Method 0 / Method 1 toggle** on the Scorecard with the delta visible.

**Why:** clears the two-method public-deploy gate and builds the "compare the
methods" demo — the setup the accuracy view pays off.

**State — all green, all pushed (commits a182318 … 877a31a; tags
method1-preregistration, method1-preregistration-r2).** Method 1 (blind, v0.3.0):
129/131 estimable (rescues series-start PRE-0054, drops thin-pool PRE-0097),
reconciliation exact, portfolio ROI **1.04** vs Method 0's **1.13** — less rosy, the
comparable baseline catches the concurrent trend. All four seeded stories estimable.
58 Python tests + full front-end build green; truth gate, import ban,
dependency-direction all green; artifact byte-identical. Toggle verified in the DOM
(flips every surface; no page h-scroll at 1280/375; full-width toggle + stacked
stats on mobile). CI watched on push (deploy included).

**Blindness ledger — still airtight:** no `truth.load_truth()` anywhere in the repo.
Both methods are spec-tagged AND implemented-and-frozen before any truth access, per
the ordering constraint added this session. `store_card().region` is package-assigned
(never join to platform data — DECISIONS).

**Untouched:** the accuracy view (the single first-contact with truth — deliberately
not started), filters, Event Anatomy, the human 375px/30-second timed check with a
trade-marketing person.

**Next — the accuracy view.** Now unblocked and correctly sequenced: both methods
are frozen behind it, so it is the repo's single clean first truth access. Score
Method 0 and Method 1 against `truth.load_truth()` (guarded by
`assert_aligned_with_observed`), in the one module exempt from the truth gate by
name (`src/incrementality/accuracy.py`). Headline error over the full population;
the four seeded stories marked and reported separately; the background distribution
shown alongside them; `match_relaxed_share` available as a Method 1 regime cut. The
dependency-direction guard fires the moment that module lands.

## 2026-08-21 — Accuracy view shipped: the repo's first and only truth contact

**What changed:** The accuracy view, end to end, as the single clean first-contact
with truth — both methods frozen behind it. (1) Pre-registered the scoring metrics
in `docs/accuracy-spec.md` and tagged `accuracy-preregistration` **before**
`accuracy.py` existed (metric-shopping after seeing results is the same sin as
tuning after seeing truth). (2) `accuracy.py` — the one by-name-exempt module that
imports `truth`; `assert_aligned_with_observed` first, then scores Method 0 and
Method 1 against `truth.load_truth()`. (3) Both estimators now carry `week_ending`
(additive, no estimate change) so scoring joins each scored store-week to truth at
the same grain — error measures accuracy, not coverage. (4) `accuracy/v1` artifact
(error metrics only, schema-tested). (5) The `/accuracy` view, one click from the
Scorecard, both methods side by side, claim language verbatim.

**The findings (honest, non-trivial):** both methods ~**26% median absolute error**
on incremental units. Method 1 is **more** upward-biased (**+22%**) than Method 0
(**+12%**) — the better baseline does not dominate on this metric, the most credible
possible result (a rigged demo would show the naive method losing badly). The
match-relaxation regime pays off: **fully-relaxed +22.6% bias vs mixed +15.7%** —
error grows where the match relaxed. Retailer error spans **14%–39%**. The four
stories are scored separately (pure_subsidy M0 −36%/M1 +9%; clean_winner M0 −15%/M1
+25%).

**Blindness ledger — closed and demonstrated.** The truth gate PASSES with
`accuracy.py` exempt by name and FAILS without the exemption (proving the exemption
is load-bearing, not vacuous). Import ban and dependency-direction green (nothing
imports `accuracy`). Git history: `method1-preregistration`,
`method1-preregistration-r2`, `accuracy-preregistration` all predate the first
`truth.load_truth()` call. The artifact carries no truth token (raw-bytes test) and
no reconstructable value.

**State — all pushed (a182318 … 5ac9d81), 68 Python tests + front-end build green,
ruff clean, artifacts byte-identical.** CI watched on the accuracy-view push (the
deploy job runs the accuracy build, so CI loads truth cold for the first time).
Three views now live behind the two-method gate: Scorecard (toggle), and Accuracy
(one click deep). `accuracy.json` gitignored, wired into `build.sh` step [3/4].

**Owed before "done" (DoD): the copy audit.** Stopping here per instruction — the
accuracy view's copy (and the Scorecard copy) freezes for the writing audit before
this counts as deploy-ready. Also still open: the human 375px/30-second timed check
with a trade-marketing person, and the external platform session (stale `421beef`,
v0.3.0 canonical paragraph) — both yours.

**Next:** the copy audit (freeze + your review), then — if wanted — Event Anatomy
(the next arc: per-event waterfall, the baseline-method toggle inside the view), and
filters (cross-view state). The estimator/accuracy spine is complete.

## 2026-08-22 — Arc complete: spine deployed with audited copy

**What changed:** Copy audit closed (5f6a00f) and deployed green — four fixes plus
the coupon footnote: bias paragraph de-conflated (ROI story separated from the
per-event bias story), exclusion accounting stated on-page (scored = estimable −
below-floor near-zero-lift events; stories included and also broken out), the
match-relaxation intro corrected to match its own table (median holds ~26%, only
bias worsens: +22.6% fully-relaxed vs +15.7% mixed), decimals standardized to one
place everywhere (`toFixed(1)` in the view, `round(...,1)` in the artifact), and a
digital_coupon footnote (small true lifts → stressed denominator, not a broken
method). Prose reads its numbers from the artifact so copy can't drift from data.

**State — the three-view spine is DONE and deployed on `.pages.dev`:** ROI Scorecard
(Method 0/1 toggle, delta visible), Event-anatomy-of-the-portfolio ranked list, and
the Accuracy proof page (estimate vs truth, both methods side by side, audited copy).
Blindness ledger closed and demonstrated: truth gate proven load-bearing, import ban,
dependency-direction all green; three pre-registration tags predate the first
`truth.load_truth()`. 68 Python tests + front-end build green, artifacts byte-identical.

**Open — all on Shawn's plate, none blocking:** (1) the platform session (push
`421beef`, paste the v0.3.0 canonical paragraph — a separate repo / outward publish,
oldest open item); (2) the human 375px/30-second phone look at `/accuracy`; (3) the
ICP timed check against the finished tool.

**Next arc (prompt staged by Shawn):** Event Anatomy — deep-linkable per-event page
(`/event/PRE-0002`), full waterfall (gross → subsidized baseline → dip → transfer →
net lift) with margin/cost alongside, M0/M1 toggle inside the view, observed-only
(truth error appears ONLY as a link to `/accuracy`, never inline), waterfall in
SVG/D3 per the DOM-bars boundary, story/phantom annotations inline (Clean winner's
91%-giveaway paradox gets its explanation here). Plus cross-view filters
(retailer/line/type/status) persistent via URL state — the SvelteKit rationale
cashing in. 30-second rule does not apply (exploration surface, desktop-first).
Copy freezes for audit before deploy.

## 2026-08-22 — /accuracy 375px gate met; Event Anatomy arc opened (blocked on a data-boundary question)

**Gate:** The `/accuracy` phone look passed — 375px gate met (Shawn, human check).
Both deployed surfaces (Scorecard header + Accuracy) now clear the 375px bar.

**New arc requested:** Event Anatomy (deep-linkable `/event/<promo_id>`, waterfall,
M0/M1 toggle inside, story/phantom annotations) + cross-view filters (URL state).
Before building I flagged a data-boundary question — see the session log — because
the requested waterfall lists `dip` and `transfer` segments, which are
blindness-protected truth quantities the estimators are forbidden to see and the
current Method 0/1 do not produce. Resolution pending Shawn's answer.

## 2026-08-22 — Event Anatomy + cross-view filters built (Option A); frozen for copy audit

**What changed:** The second view and the cross-view state, three boundaries, all
pushed. (1) `build_anatomy.py` → `anatomy/v1` artifact: per event, per method, the
three-bar volume decomposition (gross promoted → subsidized baseline → net
incremental lift, net derived from the rounded pair so it reconciles on screen) plus
margin/cost/ROI/giveaway and observed meta. Blind (truth gate passes over it), schema
test forbids truth tokens, wired into build.sh. (2) `/event/[promo_id]` view —
prerendered for all 131 via entries(), SVG waterfall, M0/M1 toggle updating the bars,
margin/cost alongside, story/phantom annotations describing DESIGN INTENT from public
upstream docs (never truth values), and a `/accuracy` link for the error (never
inline). Scorecard rows link to event pages. (3) Cross-view filters
(retailer/line/type/status) in URL state — narrow the list only, not the verdict;
read client-side (a prerendered page can't depend on url.search) and synced via
replaceState; event links + the event back-link carry the filter.

**Design boundary that shaped it (DECISIONS 2026-08-22):** the requested waterfall
listed dip and transfer segments — protected truth the blind estimators don't
produce. Option A ships the three bars the estimator can defend; dip/transfer are the
NEXT estimation arc (Option B, tools 1c/1d), logged with their own pre-registration +
accuracy scoring and a net→net-of-dip re-run.

**State — all pushed, 75 Python tests + front-end build green, ruff clean, artifacts
byte-identical, no console errors, no page h-scroll.** Verified live: toggle
reactivity, clean_winner's 91%-giveaway paradox, phantom-as-noise ($0 cost, null
ROI), non-estimable paths, filter 129→19 + deep-link + clear, cross-view back-link
persistence, all 131 event pages prerender. CI deploy watched (build.sh now runs
build_anatomy; prerenders 131 event pages — first time in CI).

**Owed before "done" (DoD): the copy audit.** Stopping here per instruction. New copy
to freeze: the anatomy narrative (story/phantom annotations, waterfall caption/
footnote, the /accuracy link copy) and the filter labels. Also still open (Shawn):
the ICP timed check against the finished tool.

**Next arc:** Option B — observed-only dip + transfer estimators (tools 1c/1d), each
pre-registered and accuracy-scored; the anatomy waterfall then gains its 4th and 5th
bars honestly.

## 2026-08-23 21:55 — /wrap

**Started from:** Method 0 spine frozen; session opened on the Method 0 module and
grew to the full three-view tool.

**Did:** Method 1 comparable-store baseline (store_card() v0.3.0, §3 pre-registered
with the format-class JUDGMENT mapping, M0/M1 toggle). Accuracy view — metrics
pre-registered before the repo's first truth access; accuracy.py the single
by-name-exempt truth door; error-only artifact; /accuracy view. Platform canon
bumped to v0.3.0. Event Anatomy — three-bar observed waterfall, deep-linkable
/event/<id>, M0/M1 toggle, story/phantom annotations; cross-view filters carrying
BOTH filters and active method in URL state. Two copy audits; all fixes deployed.

**State:** All three views live + audited on .pages.dev, wired with URL-persistent
filters + method. 75 Python tests + front-end build green, ruff clean, all
blindness guards green, three pre-registration tags predate first truth. Tree
clean, all pushed.

**Next:** Option B — observed-only dip + transfer estimators (tools 1c/1d), each
pre-registered with its own tag and accuracy scoring; the waterfall gains its 4th
and 5th bars and the headline moves net → net-of-dip as a logged re-run. Plus the
human ICP timed check (Shawn's).

## 2026-08-24 15:32

**What changed:** Marked the arc DoD item "30-second rule verified in one timed
session with a trade-marketing person" as **met** (PLAN.md); project-level ≥3-ICP
bar updated to **1 of 3**.

**Why:** ICP timed check passed — one trade-marketing person, 30-second
comprehension confirmed against the live flagship `liftmath.lailarallc.com`.

**State:** Arc DoD 30-second-timed item cleared; project-level success item stands
at 1/3 (two more ICP passes owed). Precedes this session's two shipped changes,
both pushed and deploying: the cross-view consistency fix (in wrap commit 96a3a07)
and the trade-spend scoping line + v0.4.0 follow-up decision (fbea78c). Tree
otherwise clean.

**Next:** two more ICP timed passes for the project-level bar; and — before the
final copy audit and public relaunch — the upstream v0.4.0 realistic-cost release
(DECISIONS 2026-08-23), which re-scores every headline number as a logged re-run.

## 2026-08-25 17:24 — /wrap

**Started from:** Three-view spine complete/deployed; a re-audit had caught Anatomy
and Scorecard disagreeing on the same event+method (PRE-0002 M0 0.55×/63% vs
0.60×/60%).

**Did:**
- Fixed the cross-view consistency bug: `build_anatomy._float` pre-rounded `roi` and
  `subsidized_cost_share` to one decimal while the Scorecard carries them full
  precision → different numbers on two pages, and Anatomy self-contradicting its own
  exact margin/cost. Split the converter (`_units` rounds the bars only; `_float`
  full precision for stats).
- Added `test_cross_view_consistency.py` — every event × method × shared-stat,
  anatomy ≡ scorecard emitted value, exact.
- Added the Scorecard trade-spend scoping line (promo-event slice, not all-in trade);
  logged the v0.4.0 realistic-cost follow-up (DECISIONS + PLAN).
- Marked the ICP 30-second DoD item met (project-level 1 of 3).

**Sibling surfaces:** anatomy float rounding — reassigned all per-method float stats
(`gross`/`baseline`→`_units`, `net`→derived, `roi`/`subsidized_cost_share`→full
precision, `discount_depth_pct`→full precision); all shared stats now enforced
exhaustively by the new test (131×2×stats), so future drift fails CI. Scorecard scope
line — single surface; Anatomy has its own give-note, unaffected.

**State:** 78 Python tests + front-end build green, ruff clean, blindness guards
green. All pushed; `origin/main` at `c0ffeef` (fixes in `96a3a07` + `fbea78c`, ICP
log `c0ffeef`). **Project moved `active/` → `published/` this session** (publish flow,
concurrent session) — same repo, tree clean. This wrap commit adds FAILURES/DECISIONS/
HANDOFF only.

**Next:** two more ICP timed passes; then the upstream **v0.4.0 realistic-cost
release** (separate `cinderhaven-promo-response` session) sequenced before the final
copy audit and public relaunch. Also open: Option B dip/transfer estimators (next
estimation arc). **Watch:** a second live session shares this checkout — close it
before more work to avoid muddy commits.

## 2026-08-24 — Launched as Lift Math; upstream v0.4.0 re-pin + copy audit + social card

**Started from:** Three views live on `.pages.dev`, pinned to upstream v0.3.0
(`6556460`).

**Did:**
- **Re-pinned to v0.4.0** (`6399990`) and logged the re-run. Economics moved:
  portfolio spend $104,425.13 → **$80,448.79** (M0), return 1.13x → **1.47x**,
  lost-money **64 → 45** of 129 (M0) / 48 (M1). `pure_subsidy` flipped to
  profitable on both methods.
- **Verified the accuracy invariant rather than citing it:** snapshotted the
  v0.3.0 artifacts before installing and diffed after. `accuracy.json` differs
  in **exactly one leaf**, the `package_version` stamp. No re-score done or
  needed.
- **Copy audit** — 4-surface adversarial sweep, 55 raw → **35 confirmed, 20
  refuted**, all 35 fixed. Added `tests/test_no_portfolio_spend_ratio.py`,
  demonstrated-to-fail against the exact banned sentence that had shipped.
- **Launched as Lift Math** — per-route titles, meta/OG block, custom domain
  `liftmath.lailarallc.com` attached via API, README to launched state.
- **Social card** — 1200x630 `og-card.png` rendered by headless Chrome from
  `web/card-source/card.html` against the real vendored brand fonts and palette.
  No new dependency (Pillow and Playwright both rejected).

**State:** Launched and live at https://liftmath.lailarallc.com — card serving,
`summary_large_image`, 92 tests, ruff clean, all my work pushed.

**Not mine, left alone:** the working tree carries another session's uncommitted
cross-view-consistency work (DECISIONS +22, FAILURES +38, HANDOFF +36) plus
commit `c0ffeef`. I appended this entry but did **not** commit — committing
another session's in-flight state under my message would mix the two.

**Next:** Platform repo — push `421beef`, paste the v0.4.0 canonical paragraph.
Then upstream **v0.5.0 (calendar density)** *before* Option B, so dip/transfer
estimators pre-register against the final generation instead of re-scoring
twice. Before posting anywhere: run the URL through LinkedIn Post Inspector and
X's card validator once — they cache hard on first fetch.

## 2026-08-26 15:35

**What changed:** Shipped three UI batches live and closed the case-study PLAN dependency: (1) measure unify + table-header alignment, (2) "so what" bridge + footer case-study link, (3) re-vendor frame v1.5.0 with the canonical .ll-column measure and tool-local table classes.

**Why:** Heading and lede now share one right edge, table headers align to their columns, a cold visitor has a path from tool to narrative, and the ad-hoc vendored-frame drift is erased against the released v1.5.0 tag.

**State:** Live + verified on liftmath.lailarallc.com (origin main a8eeea6): hero heading==lede edge, --ll-content-measure 720px, wordmark 26/20px, real bold, tables aligned (numeric right / text left / none centered), bridge + footer case-study link on all pages, zero drift tokens. CI green (truth-gate, data-contract, Cloudflare deploy). /work/lift-math live (200) so the case-study external dependency is RESOLVED in PLAN. Untouched: estimators, accuracy scoring, Option B.

**Next:** Two more ICP timed passes (project bar 1 of 3); then upstream v0.5.0 (calendar density) before Option B dip/transfer, per PLAN.

## 2026-08-26 17:41 — /wrap

**Started from:** Three-view tool live on frame v1.1.0; a complaint that display headings and prose wrapped at different widths.

**Did:** Shipped three UI batches live and verified on liftmath.lailarallc.com — (1) measure unify + table-header alignment; (2) "so what" bridge + footer case-study link; (3) re-vendor frame v1.5.0 (canonical .ll-column / --ll-content-measure; tool-local table classes; drops the ad-hoc .ll-num/.ll-text and local --content-measure alias). Deploy went out even though GitHub's status page still showed an Actions outage — the runs API was the real signal. Closed the now-live /work/lift-math PLAN dependency; /log checkpoint (bc98d27).

**State:** Live + verified (origin main a8eeea6, plus local docs commits): hero heading==lede edge, --ll-content-measure 720px, wordmark 26/20px, real bold, tables aligned (numeric right / text left / none centered), bridge + footer link on all pages, zero drift tokens. CI green (truth-gate, data-contract, deploy). Untouched: estimators, accuracy scoring, Option B.

**Next:** Separate note-to-self runs tomorrow as written — verify the 0.6356 truth loss rate + 48/129 M1 lost-money against the truth artifacts before restoring, not from prose. Project: two more ICP timed passes (bar 1/3), then upstream v0.5.0 (calendar density) before Option B dip/transfer.

## 2026-08-27 14:03 — org migration close-out

**What changed:** Repo transferred MsShawnP -> lailarallc org (fleet personal->org migration, run by the migration session); local git remote repointed to lailarallc/cinderhaven-promo-incrementality.

**Why:** The freshly-rolled Cloudflare token is org-level only — every repo-level CF copy is dead, which is what broke the deploy on the personal repo (auth 9109). Org ownership lets CI use the org CLOUDFLARE_API_TOKEN + org-level PROMO_RESPONSE_READ.

**State:** origin -> org (fetch+push), org/main == local 185b39f, liftmath.lailarallc.com 200. Migration session re-ran ci.yml green (promo read 6399990 via org PAT; CF deploy on org token). Deploy pipeline healthy under the org. Doctrine: never create repo-level Actions secrets — if a secret is missing the repo is not in the org yet.

**Next:** Nothing blocking. Resume project work — two more ICP timed passes (bar 1/3), then upstream v0.5.0 (calendar density) before Option B dip/transfer.

## 2026-08-27 16:24 — owner decisions: ICP bar closed, v0.5.0 roadmap active

**What changed:** Recorded two owner decisions in PLAN. (1) The project-level >=3-ICP success bar is CLOSED as an **owner close** — 1 of 3 passes run (2026-08-23), remaining 2 waived by Shawn; recorded as an owner close, NOT 3/3 completed. (2) v0.5.0 (calendar-density epoch) is now ACTIVE (started today in the data repo); this repo's part follows as one re-validation arc.

**Why:** Owner set the roadmap. v0.5.0 changes unit truth (~30–45x promoted volume), so it re-validates every headline number.

**State:** PLAN updated — ICP item + arc cross-ref closed; v0.5.0 dependency marked active with this repo's task list; Arc history re-sequenced to v0.5.0 re-validation then Option B. No code touched. The prior HANDOFF "two more ICP passes" Next line is superseded by this.

**Next (this repo, after the data-repo v0.5.0 release):** re-pin → full re-score as a logged re-run (before/after error in DECISIONS; every headline number moves) → copy re-audit → revisit the no-portfolio-% constraint once spend-to-revenue is realistic → then Option B.

## 2026-09-01 15:04 — /wrap

**Started from:** Owner decisions logged (ICP owner-closed, v0.5.0 roadmap active); the v0.6.1 re-validation arc queued.

**Did:** Executed the **v0.6.1 two-epoch re-pin** (calendar density + commercial dynamics) as one logged re-run — every headline moved (estimable 5,735/5,122, lost 2,170/2,470, spend $2.93M/$2.73M, ROI 1.38/1.18, accuracy 32.8%/42.0% median, +17.5%/+27.2% bias; accuracy re-scored for the first time since launch). Vectorized Method 1 (equivalence-gated, ~9.5min → ~47s, loop kept as the oracle). Band-freeze pre-registered before any truth (VOLUME_BAND_FACTOR=2 held; its 95%-clearance derivation target is unreachable in the density world). Option B split: anatomy → per-event slices + a 141-event prerender manifest; scorecard → summary+first-page imported, full events fetched-on-touch; adapter fallback. Front door 3.75MB → 128KB. Copy consequences + Max's five audit fixes, all live-verified. Fixed a real Cloudflare defect: the /event/* _redirects rewrite shadowed the prerendered files (direct hits 308'd to /200); dropped it, fallback → 404.html.

**State:** v0.6.1 live on liftmath.lailarallc.com, CI green (truth-gate / data-contract / build / Cloudflare deploy), 84 tests green, ruff clean, tree clean, all pushed (10cf2d0). DECISIONS carries the band-freeze entry + the full before/after re-run table. Untouched: Option B dip/transfer estimators; two more ICP passes were owner-waived.

**Next:** **Option B — observed-only dip + transfer estimators (tools 1c/1d)**, each pre-registered with its own tag and accuracy-scored; the anatomy waterfall then gains its 4th/5th bars and the headline moves net → net-of-dip as a logged re-run. Nothing blocking or broken.

## 2026-09-02 — /wrap (README refresh)

**Started from:** v0.6.1 live and audited; Max flagged one last stale surface — README.md still read v0.4.0.

**Did:** Refreshed README.md to v0.6.1 reality (0b650f3): intro "5,735 estimable promotions" (was 131), Status/Stack pinned v0.6.1 (`bdb08c69`, both places), `promo_events` 5,897 rows, roadmap entry marked done ("~1%" → "about a third of the book"; next = dip/transfer estimators), and scoped the README's own "no number is hand-entered" promise to **the views** (the README carries hand-entered figures from the artifacts; the tool's displayed numbers don't). Zero v0.4.0 references remain.

**State:** Tree clean, 0 unpushed, CI green through 0b650f3 (redeploys an identical site — README isn't in `web/`, so no user-visible change). Tool is closed for this arc per Max's audit. 84 tests / ruff / blindness guards unchanged (no code touched). Nothing broken.

**Next:** Unchanged — **Option B: observed-only dip + transfer estimators (tools 1c/1d)**, pre-registered + accuracy-scored, when the next arc opens. Nothing blocking.

## 2026-11-04 — v0.7.0 assortment re-pin: logged re-run, frozen pending Max's audit

**Started from:** v0.6.2 live (c4aaa44). Upstream released v0.7.0 (launches/exits),
truth-moving.

**Did:**
- Extended the generator import ban to `baseline` + `assortment`, plus `pr.<module>`
  attribute access (ee88809).
- Pre-registered accuracy-spec §11 — life_stage + sibling_assortment regimes, the
  prediction-4 economics block, and the row-attribution rule — tagged
  `accuracy-preregistration-v0.7.0` and pushed before any v0.7.0 truth was read (de3c710).
- Re-pinned to v0.7.0 (ff596fe), re-ran the pipeline, logged before/after in DECISIONS.
  Headlines move modestly (M0 2,137 of 5,484 lost, ROI 1.44; accuracy 33.8% / 41.2%).
  Predictions: 5 of 8 hit. Method 0 reverses the launch-promo loss ordering (7% vs 39%).
  `clean_winner` error is now +180% / +185% (re-placed upstream onto a 10% digital coupon).
- Copy: new Accuracy section (predictions, life stage, sibling, launch economics), Scorecard
  scope ratios computed (`spend_context`) — all artifact-fed. README to v0.7.0.

**State:** On branch `rerun/v0.7.0`, pushed, PR open. **Not merged, not deployed** — merge
to main auto-deploys, so the branch is the freeze. Live site is still v0.6.2.

**Next:** Max audits the PR. After it passes, merge (deploys) and verify live matches HEAD.
Open, not touched: the 2026-09-23 audit's CRITICAL cost/coverage mismatch in
`common.assemble` (partial-coverage events charged full cost) still skews lost-money and
ROI, Method 1 most; DECISIONS.md has two entries fused onto earlier "Do not" lines (~L396,
~L429) — formatting only.
