# cinderhaven-promo-incrementality — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

**This arc (opened 2026-08-22): Event Anatomy + cross-view filters.** The spine —
ROI Scorecard, Accuracy, both baseline methods — is built, audited, and deployed
(see Arc history). This arc adds the second view and the cross-view state the
SvelteKit choice was made for.

The project is **three views** — ROI Scorecard, Event Anatomy, Accuracy. The first
and third are live; this arc builds the second and wires the three together.

## Event Anatomy — the three-bar observed waterfall (DECISIONS 2026-08-22)

Per-event, deep-linkable (`/event/PRE-0002`), **observed + estimated only**. The
waterfall is **gross promoted volume → subsidized baseline (giveaway) → net
incremental lift** — the three bars a blind estimator can defend — with the M0/M1
toggle and margin/accrued cost alongside, in SVG (exploration surface; the DOM-bars
rule was a Scorecard-header responsiveness exception). Dip and transfer are **not**
bars here (protected truth); they are the **next** estimation arc (Option B, tools
1c/1d). The event's truth-scored error appears **only** as a link to `/accuracy`,
never inline. Story/phantom events carry narrative annotations describing **design
intent from public upstream docs — never truth values**.

## Cross-view filters

retailer / product line / promo type / plan status, persistent across the Scorecard
and Anatomy via **URL state** — the SvelteKit rationale cashing in. The 30-second
rule does **not** apply (exploration surface, desktop-first, graceful on mobile).

## Tasks — this arc

- [x] **Anatomy artifact** — `build_anatomy.py` writes `anatomy.json`: per event,
      per method, the volume decomposition (gross / subsidized baseline / net
      incremental) plus margin, accrued cost, ROI, giveaway share, and observed
      meta (weeks, depth, funding, story/phantom). Blind (no truth); schema test;
      wired into `build.sh`.
- [x] **Event Anatomy view** — `/event/[promo_id]` prerendered for all 131
      (`entries()`), the SVG waterfall, M0/M1 toggle, margin/cost, story/phantom
      annotations, and a `/accuracy` link for the error. Linked from the Scorecard
      ranked-list rows.
- [x] **Cross-view filters** — retailer/line/type/status in URL state, shared
      store, applied to the Scorecard ranked list (and the anatomy's event
      navigation). Deep-linkable, persistent across the two views.
- [x] **Copy freezes for audit before deploy** (DoD rule). Commit at boundaries.

## Business question this arc answers

How wrong is a trade-promotion incrementality estimate, and can that error be
shown rather than claimed?

## Requirements — clarified 2026-08-17

Output of `/clarify` and `/office-hours`. Refines the arc goal above; does not
replace it. These are requirements for the stack decision, not the decision
itself — that runs through `/plan-eng-review`.

**Audience and framing**

- Primary audience is **prospective clients** — specialty food brands, trade
  marketing leads. This is a portfolio flagship, not an internal tool.
- **The tool is the product.** No landing page, no narrative wrapper in this
  repo. A case study on `lailarallc.com/work` carries the story separately.
- The front door is **the money, not the method**. Open on the ROI Scorecard;
  the accuracy view sits one click deeper as the proof behind the numbers. It
  closes the sale rather than opening it.

**The 30-second rule — governs arrival**

The ROI Scorecard's first paint must be readable by a CEO or CFO in 30 seconds
or less: **verdict line, one chart, three numbers.** That is the *Question
Engine pattern* — a screen that answers one question outright and explains
itself to an executive in 30 seconds, with no legend-reading, no drill-down
and no prior context required.

Exploration is opt-in depth *after* the verdict, never a prerequisite for it.
The zero-state — before any filter is touched — is a deliverable in its own
right, not a placeholder. "Genuine exploration" must not become "requires
exploration."

**Verification:** this is the only requirement here that cannot be checked by
running a test. It is checked by **one timed session with one person who works
in trade marketing, before public deploy.** Show the first paint, time them,
ask what the tool is telling them. Unverified, it is an assertion.

**Data shape**

- Python computes at **build time** and writes small precomputed artifacts.
- The 1,340,462 scan rows **do not ship to the browser**. DuckDB-WASM is out.
- Anything a view needs is precomputed; a view that wasn't precomputed needs a
  rebuild, and that is an accepted cost.

**Interaction**

Genuine exploration: filters that **persist across views**, deep-linkable URLs,
comparison mode. This is shared client state across routes — an application,
not a set of pages with widgets.

**Constraints**

- Python engine — fixed, see DECISIONS.md. Not revisitable.
- `cinderhaven-promo-response` pinned at v0.4.0 (commit `6399990`), public API only.
- Static hosting. Lailara design system governs all visual output.
- Timeline **open-ended** — done when it's good. The only budget risk is
  stalling out, not overrunning a date.

**Two assumptions surfaced and revised**

1. *Scrollytelling is required.* — **False.** It appears twice in DECISIONS.md
   as a reason to reject Dash and favor SvelteKit, but nothing in CLAUDE.md or
   PLAN.md requires it. Dropped from the stack rationale entirely. This
   **weakens** the SvelteKit case.
2. *All 1.34M rows ship to the browser via DuckDB-WASM.* — **False.** Build-time
   precomputation makes the payload a few hundred KB. This removes the payload
   risk that partly justified Observable Framework's data-loader model.

**What this does to the stack question**

The deciding axis moved from *narrative ambition* to *cross-view state*.
Persistent filters, deep-linkable URLs and comparison mode are the one
requirement set where SvelteKit earns its extra week over Observable Framework —
whose per-page reactive model is least suited to shared cross-route state.
**Unverified:** Framework's actual cross-route state story. Check it at
`/plan-eng-review` rather than assuming.

Dash is now clearly out: an always-on server for data that never changes, and
Plotly defaults fighting the design system.

**Mobile — decided 2026-08-17, split by surface**

- **The 30-second surface is phone-first.** The Scorecard header — verdict
  line, one chart, three numbers — must *fully* work at 375px. That screen is
  the first impression from the `/work` link, and links get opened on phones.
  A 30-second verdict that only works at 1440px fails its own brief.
- **The exploration surfaces are desktop-first.** Ranked-list interactions,
  Event Anatomy, Accuracy: readable and functional on mobile, but comparison
  mode and dense waterfall interactions may degrade gracefully with a "best
  on desktop" note.

This bounds the responsive work to **one** genuinely responsive component
instead of three, and it matches how each surface is actually consumed. Full
entry in DECISIONS.md.

## Tasks

Work in vertical slices — for this tool a slice is one view end-to-end
(estimator → accuracy measurement → rendered view → test), not a horizontal
layer.

- [x] **Stack decision** — done 2026-08-17. **SvelteKit + D3, static, on
      Cloudflare Pages.** Observable Framework and Dash rejected with reasons
      in DECISIONS.md; the PENDING entry is closed, not edited away.
- [x] **Repo skeleton for the chosen stack** — dependency manifest with the
      upstream package pinned, test runner, lint config, `.gitignore`
      additions. Nothing rendering yet.
      **Python side done 2026-08-18** — `pyproject.toml` with the pinned SHA,
      pytest, ruff, `src/incrementality/` package root. **SvelteKit scaffold
      not started**, which is what keeps this unchecked.
- [x] **CI with the truth gate, before any estimator exists** — a workflow
      that runs `assert_no_truth_access` over `src/`. It must be proven to
      *fail*: commit a deliberate violation fixture, watch CI go red, then
      remove it. A gate never shown to fail is not evidence.
      **Split this into two jobs.** The gate is pure AST parsing and needs no
      data; keep it fast and dependency-light so it always runs. `pr.load()`
      is ~8.5s cold with no warm cache in CI, and a gate that goes red for
      unrelated data flakes is a gate people learn to ignore.
      **Written 2026-08-18** — `.github/workflows/ci.yml`, two jobs. The gate
      job installs the package with `--no-deps` (the gate imports only `ast`
      and `pathlib`) and asserts pandas is absent, so "dependency-light" is
      enforced rather than intended. **Proven to fail locally**: a violation
      planted in `src/` turns the gate red naming the file and line, and two
      permanent fixtures in `tests/fixtures/` keep both channels — import and
      string literal — demonstrated on every run. **Still unchecked because the
      CI run itself has not been observed.** Failing locally proves the gate
      function works; it does not prove the workflow wiring, the secret, or the
      `--no-deps` install work on a runner. That needs a push.
- [x] **Re-pin to v0.1.1 once upstream ships the packaging fix.** Done
      2026-08-18 — pinned to 7cfe95c; data-contract job now green cold.  `pr.load()`
      raises `FileNotFoundError` on the first call in any fresh install of
      v0.1.0 — `FIGURES.md` is read at runtime but not packaged into the wheel.
      See FAILURES.md for the reproduction and the defect class. **Consequence
      for this arc: the CI data job is expected red until this lands.** That is
      the correct state — a red job telling the truth beats a green one hiding
      an upstream bug that is already scheduled to be fixed. The truth-gate job
      is unaffected; it is pure AST parsing and needs no data, which is the
      second reason for the split above.
      The fix is an upstream v0.1.1 patch release made in its own session, not
      from this repo. Its acceptance test: **cold-cache `pr.load()` succeeds
      from a wheel install**, plus a release-checklist line for the general
      rule — *every file the package reads at runtime is present in the built
      artifact.* Re-pinning here is then a one-line manifest change, logged in
      DECISIONS.md as a re-run per the pin decision.
      **Do not adopt a local workaround** — not a swallowed exception, not a
      shipped warm cache — without its own DECISIONS.md entry. A consumer that
      silently swallows an exception from its data package is the failure mode
      this project's premise argues against.
- [x] **Dependency-direction test** — **done 2026-08-21**
      (`tests/test_dependency_direction.py`). Asserts no file under `src/` except
      the accuracy module imports it; since a direct-import scan over every file
      leaves no first hop, that covers the transitive case too. Stood up now as a
      forward guard (accuracy module doesn't exist yet), demonstrated-to-fail with
      a permanent fixture (`violation_imports_accuracy.py`) — same discipline as
      the truth gate before the first estimator. The AST gate is per-file; an
      estimator importing the accuracy module reaches truth while its own AST
      stays clean. See DECISIONS.md.
- [x] **Walking skeleton — the stack experiment.** One hardcoded number,
      computed in Python, written as JSON by the real pipeline, rendered by
      the real front end, deployed to a real static host. Hours, not days.
      **This is what actually answers "is this stack right?"** — the question
      slice 1 was carrying. Doing it first means an unfamiliar stack fails
      fast and cheap, before any estimator work is entangled with it. It is
      also the cheapest available insurance against the stall risk.
- [ ] **Artifact contract** — what artifacts exist, their schema, where they
      are written, how the front end consumes them. This is the highest-risk
      integration point in the system and it was previously not a task at all.
      Includes: the build **fails loudly** if the Python step fails — a static
      build that silently ships yesterday's artifact is the worst outcome for
      a tool whose premise is numeric credibility. Includes the accuracy
      artifact's schema assertion (error metrics only, observed-feature regime
      labels only — see DECISIONS.md).
- [ ] **Reproducibility test** — run the pipeline twice, diff the artifacts.
      Determinism is a stated requirement and nothing currently checks it.
- [x] **Deploy pipeline** — build and publish to Cloudflare Pages. Was missing
      from the task list entirely. Gated on the two-method rule below before
      anything is public.
- [x] **Upstream `cinderhaven-promo-response` v0.2.0 — `economics()` accessor.**
      **Done 2026-08-19** — shipped as v0.2.0 and fixed to v0.2.1 (lazy pandas
      import); consumer pinned to v0.2.1 (11caa13). The allowed surface is now
      exactly `load()`, `economics()`, `testing`. `method0.py` consumes
      `economics()` for the manufacturer-margin basis (wholesale − COGS per
      SKU×retailer). See the demarcation entry in DECISIONS.
- [ ] **Slice 1 — ROI Scorecard end-to-end, on Method 0.** Baseline
      estimation is on the critical path of every downstream number,
      including ROI — incremental profit over spend requires incremental
      units, which requires a baseline. Slice 1 therefore uses **Method 0,
      the naive pre-period average, labeled as such on screen.** That is
      not a shortcut; it puts the anti-rigging exhibit first. Deliverable:
      portfolio header (spend, net incremental margin, ROI, N of 131 that
      lost money), ranked event list, filters. First paint must satisfy the
      30-second rule before any filter is touched.
      **Progress:** Spec frozen (`docs/estimators.md`) and the **pipeline +
      artifact now landed** (2026-08-19): `method0.py` (baseline → incremental
      units → manufacturer-margin cents via `economics()` → per-event ROI /
      giveaway share → portfolio roll-up over 129 estimable events) and
      `build_scorecard.py` (deterministic `scorecard/v1` artifact). 40 tests
      green, reconciliation exact (11,820,037 cents both ways), truth gate +
      import ban green, artifact byte-identical. §2.4 corrected to a volume-basis
      giveaway share pre-freeze (DECISIONS). The **SvelteKit Scorecard VIEW now
      landed** (2026-08-21): the 30-second header (verdict, three numbers,
      profit-tier chart) and the ranked event list (129 by net margin, lost-money
      + seeded-story + phantom badges, 2 non-estimable shown unranked), on the
      vendored Lailara brand frame with self-hosted fonts. Verified structurally —
      both fonts load, no page horizontal scroll at 1280 or 375, header collapses
      to one column on mobile, static build bakes real numbers into prerendered
      HTML. **Remaining for this slice:** filters (deferred — cross-view state is
      the Event Anatomy arc), and the one-timed-session 30-second verification with
      a trade-marketing person (a human step, gated with public deploy). **Phone
      look passed 2026-08-21** — the 30-second/375px design gate is met (the Browser
      pane wasn't compositable in-session, so the developer's own phone look stood
      in for the screenshot); the external-ICP timed check remains separate and open.
- [ ] **Upstream `cinderhaven-promo-response` v0.3.0 — `store_card()` accessor.**
      **Blocks Method 1's pipeline.** One row per `store_id`: `retailer_id`,
      `region`, `store_format` — store-master identity, `economics()`'s demarcation
      exactly. Explicitly carries **no** volume/size tier (consumers derive volume
      from observed units). Own module, no demand parameters, AST-clean, demand-free
      import test, wheel-runtime-files rule honored. Consumer then re-pins to v0.3.0
      (logged re-run). Same release dance as v0.2.0. See the store_card demarcation
      entry in DECISIONS. The Method 1 spec (§3) does **not** wait on this and is
      already committed.
- [ ] **Method 1 — comparable-store baseline, end-to-end.** Pulled into this arc
      2026-08-21 by explicit direction (was out-of-scope) because the two-method
      deploy gate needs it. **Commit 1 (spec §3) landed 2026-08-21** — comparable
      pool, per-week comparable-median baseline, `MIN_POOL` +
      `insufficient_comparable_pool` rider, cross-banner justification measured,
      weaknesses stated. **Pipeline blocked on v0.3.0** (`store_card()`). Then:
      `method1.py` (same integer-cent discipline, exact reconciliation, all guards
      green) → re-score the scorecard artifact with **both** methods (logged re-run)
      → Scorecard view gets the **Method 0 / Method 1 toggle with the delta visible**.
      The two-method public-deploy gate clears when both ship behind the toggle.
      `MIN_POOL` and the volume band are set from the matched-pool distribution once
      `store_card()` ships, tuned on pool size not error, logged before first scoring.
- [ ] **Method 2 candidate — indexed diff-in-diff (logged, not scheduled).** Baseline
      = test store's own pre-period × the control pool's during/pre velocity ratio.
      Fully observed, no upstream release. A legitimately different standard method;
      as its own pre-registered method later it strengthens the multi-method accuracy
      story. Not the attribute-matched method §3 registers — parked here so it is a
      candidate, not a rediscovered idea. See DECISIONS.
- [ ] **Accuracy view, first pass** — score slice 1's estimates against
      `truth.load_truth()`, guarded by `assert_aligned_with_observed`. The
      one module that imports truth; exempt it by name in the CI gate.
      Headline error is the full event population; the four seeded stories
      are marked and reported separately.

### Ordering constraints — the pre-registration rule

These are sequencing requirements, not preferences. They are what turns
"trust me" into "check the git log," and they only work if the order is
actually honored. Full reasoning in DECISIONS.md, external-validity entry.

- [ ] The estimator spec and implementation are **committed and tagged
      before any code in this repo loads truth.** The accuracy slice comes
      after, never alongside.
- [ ] **The accuracy view is the repo's single first-contact with truth, and it
      does not begin until EVERY registered baseline method is *implemented and
      frozen* — not merely spec-tagged.** Added 2026-08-21. Spec-tagging bounds
      the argument but does not close it: `MIN_POOL`, band widths, and pool
      mechanics are real degrees of freedom left in a method's *implementation*.
      If truth lands after Method 0 but before Method 1, Method 1's implementation
      choices post-date seeing where Method 0 failed against truth — and a sharp
      evaluator gets to say those choices were tuned to it. So no `truth.load_truth()`
      call, not even to score Method 0 alone, until Method 1 (and any other method
      shipping in the same accuracy pass) is built and frozen behind it. Saving a
      day by scoring early would spend the exact blindness evidence the project
      exists to accumulate.
- [ ] Any estimator change after first scoring is a **logged re-run** — a
      DECISIONS.md entry with before/after error. Never a silent edit.
- [ ] Each new baseline method re-scores the Scorecard as its own logged
      re-run.
- [ ] **Public deploy gate: at least two baseline methods must exist.** A
      scorecard scored only by Method 0 is the anti-rigging exhibit without
      the rigor exhibit. Nothing goes to a lailarallc.com subdomain before
      then.

## Out of scope for this arc

- **Event Anatomy and the third-plus baseline methods.** The scope is now
  three views — ROI Scorecard, Event Anatomy, Accuracy — not six. Baseline
  Builder, Lift Split, Net Lift and Portfolio were collapsed into Event
  Anatomy as segments of one waterfall; see DECISIONS.md. Event Anatomy is
  the next arc. **Method 1 (comparable-store) was pulled into this arc on
  2026-08-21** by explicit direction — the two-method public-deploy gate needs
  a second baseline, so it is now a task above, not out of scope. Method 2
  (indexed diff-in-diff) and beyond remain future work.
- **Editing `cinderhaven-promo-response`.** It is released at v0.4.0 and is
  a separate repo. A data gap found here is logged here and released there.
- **Deployment and the public subdomain.** Nothing deploys until a view is
  worth looking at. The Lailara design system and the deployed-UI gate in
  the global CLAUDE.md apply when it does.
- **Client mode / brand wrapper.** The ~4-day wrapper phase in
  `incrementality-tool-notes.md` comes after the views work.
- **Household-panel integration** for buyer-level pantry-load validation.
  Follow-up once scan-level views are live.

## Definition of done for this arc

- [ ] Stack decision logged in DECISIONS.md, naming the rejected
      alternatives and the reason — not just the winner
- [ ] `assert_no_truth_access` runs in CI over all estimation code, and has
      been **demonstrated to fail** on a deliberate violation
- [ ] ROI Scorecard renders from `pr.load()` with no hand-entered figures
- [ ] Its accuracy panel reports error against `truth.load_truth()`, with
      `assert_aligned_with_observed` called before any number is shown
- [ ] The background distribution is visible alongside the seeded stories —
      finding `clean_winner` is not a result on its own
- [ ] Same package version + same seed reproduces the same numbers
- [ ] Tests run with a single documented command, and none are skipped
- [ ] Every figure on screen from Method 0 is **labeled** as the naive
      pre-period average — no unlabeled naive numbers
- [ ] The portfolio roll-up ties to both the sum of event nets and the
      row-level grain sum, asserted by a test rather than assumed
- [x] Scorecard first paint satisfies the 30-second rule — verdict line, one
      chart, three numbers — with no filter interaction required, and the
      Scorecard header works fully at 375px. **Met 2026-08-21** — phone look
      passed at 375px (the visual gate the DOM checks this session couldn't stand
      in for).
- [x] The 30-second rule has been **verified in one timed session** with one
      person who works in trade marketing — not asserted. **Met 2026-08-23** — one
      trade-marketing person, 30-second comprehension confirmed against the live
      flagship `liftmath.lailarallc.com` (not `.pages.dev`). This clears the arc
      bar (one timed session); the project-level ≥3-ICP bar below was **closed by
      owner decision 2026-08-27** at 1 of 3 (2 waived).
- [ ] **Public-facing copy has had a writing audit before deploy** — every
      on-screen sentence checked against the Economist voice: no overclaim
      ("the most optimistic read there is"), no undefined jargon reaching the
      reader before it is defined ("estimable," "accrued," "naive baseline"),
      no dangling fragments. Sits beside the 30-second check because copy is
      half of what a CEO reads in those thirty seconds. (Logged 2026-08-21
      after a review caught all three failure modes in one pass.)
- [ ] Nothing outside the accuracy module imports it — asserted by a test,
      not by convention
- [ ] No published artifact contains truth values, and every regime label in
      the accuracy artifact is built from observed features only
- [ ] Money is integer cents end to end; the reconciliation asserts equality
      with no float tolerance
- [ ] Running the pipeline twice produces byte-identical artifacts
- [ ] The build fails loudly if the Python step fails — no stale artifact
      ever ships

## Definition of success — project level

Distinct from the arc's definition of done above, which measures whether the
artifact is correct. This measures whether building it was worth it. Horizon:
**three months from public deploy.**

The reason this section exists: the timeline is open-ended and the quality bar
rose during `/office-hours`. A project with no external "done" and a rising
internal bar has one predictable failure mode, and it isn't shipping something
wrong. This is the external done.

**Controlled — these are the bar for "worth building":**

- [x] Case study live on `lailarallc.com/work`, with the tool linked from it. **Live and verified end-to-end 2026-08-26** (case study up for days; the tool now links to it from every page footer and the Scorecard CTA).
- [x] Tool shown live to **≥3 people in the target ICP** — trade marketing or
      finance at specialty food brands — each passing the timed 30-second check.
      **CLOSED by owner decision 2026-08-27 — 1 of 3 passes run (one trade-marketing
      person, 2026-08-23, on the live flagship); the remaining 2 waived by Shawn.
      Recorded as an owner close, not as 3 passes completed.**
- [ ] Tool used as the demo in **every** promo-related sales conversation in
      the window

**Signal — directional, not pass/fail:**

- ≥1 inbound inquiry or pitch conversation that cites the tool

Marketing reach is not this repo's variable, so the signal item does not gate
anything. The controlled items do.

## Risks and external dependencies

**Primary risk: the stall.** Open-ended timeline, a rigor bar that rose during
`/office-hours`, and a deploy gate that pushes launch past this arc. The
failure mode for this project is not shipping something wrong — it is not
shipping. The project-level success definition above is the countermeasure;
it exists to supply an external "done," not to measure marketing.

**External dependency — the case study on `lailarallc.com/work`: RESOLVED 2026-08-26.** It is live and verified end-to-end; the tool links to it from every page footer and the Scorecard CTA. The flagship's narrative wrapper is in place — no longer an open dependency.

**Secondary dependency: a portfolio link.** The tool has to be reachable from
`lailarallc.com` for any of the controlled success items to be achievable.

**Pre-launch upstream dependency: `cinderhaven-promo-response` v0.4.0 — realistic
trade cost. DONE 2026-08-24, and it did not do what this entry predicted.** Shipped
upstream and re-pinned here at commit `6399990`. The release fixed a real defect — the
trade rate was `msrp * depth * DISCOUNT_ABSORPTION * coefficient`, which billed an event
more for being deeply discounted (upstream corr(depth, cost per unit) 0.784 → 0.177) —
and per-event economics are now defensible.

**Both of this entry's predictions were wrong, in opposite directions, and the reason
matters more than the entry did.** It predicted a ~$1–2M promo book and a lost-money
count *rising* toward the 71% anchor. Actual: portfolio spend **$80,448.79** (M0), and the
count **fell**, 64 → 45 of 129. The premise was that per-unit rates were too low. They
were already about right — upstream measured the pre-existing scan rate at a median
$0.76/unit, 19.1% of wholesale, inside the very band this entry proposed. What is short is
**promoted volume**: ~1% of units run on promotion against a real brand's 20–40%. No rate
inside any defensible band closes that — at $1.50 on every promoted unit the ceiling is
0.18% of revenue. The "roughly $1.5M of trade, roughly half wasted" headline this entry
was written to enable **is not reachable by a cost change** and must not be quoted.

**Upstream v0.5.0 (calendar density) — ACTIVE, started 2026-08-27 in the data repo.**
Generating 30–45x more promoted volume changes unit truth, so it invalidates every
accuracy number computed against this generation and is its own re-validation epoch —
deliberately not folded into a rate release. Until it lands, this tool leads with counts
and per-event economics, never portfolio dollars and never a trade-spend-to-revenue ratio
(see DECISIONS).

**This repo's part comes after the data-repo release, as one re-validation arc (see Arc
history):** re-pin to v0.5.0 — full re-score as a **logged re-run** (every headline
number moves) — **copy re-audit** of every surface that quotes a number — **revisit
the no-portfolio-% constraint** once spend-to-revenue is realistic (DECISIONS 2026-08-24;
it holds until then).

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### Arc 1 — Choose the stack and prove the spine (2026-08-17 → 2026-08-22, COMPLETE)

**Outcome:** All three deploy-gated deliverables shipped and live on `.pages.dev`.
ROI Scorecard (Method 0/1 toggle, ranked list), Accuracy view (estimate vs truth,
both methods, audited copy), and both baseline methods (M0 pre-period, M1
comparable-store) behind the two-method public-deploy gate. Blindness ledger closed
and demonstrated: truth gate proven load-bearing, `config`/`constants` import ban,
dependency-direction sink — all green; three pre-registration tags
(`method1-preregistration`, `-r2`, `accuracy-preregistration`) predate the first
`truth.load_truth()`. Stack decided (SvelteKit + static + Cloudflare Pages), §2.4
giveaway share corrected, upstream re-pinned through v0.1.1 → v0.2.1 → v0.3.0
(economics(), store_card()). Copy audit closed. Open human items (ICP timed check)
tracked, not blocking.

### Arc 2 — Event Anatomy + cross-view filters (2026-08-22, COMPLETE build-wise)

**Outcome:** The second view shipped and deployed. Deep-linkable `/event/<id>` with
the three-bar observed waterfall (gross → subsidized baseline → net incremental
lift), M0/M1 toggle, margin/cost, and story/phantom design-intent annotations;
`anatomy/v1` artifact (blind, schema-tested). Cross-view filters
(retailer/line/type/status) **and** the active method carried in URL state, persisting
Scorecard ↔ Anatomy. Two copy audits; the dip/transfer blindness boundary resolved as
Option A (three bars a blind estimator can defend), with Option B logged as the next
arc. Open, non-blocking: the human ICP timed check against the finished tool.

### Arc 3 — v0.6.1 two-epoch re-validation (COMPLETE 2026-09-01)

**Outcome:** Re-pinned to v0.6.1 (v0.5.0 calendar density + v0.6.0 commercial dynamics); Method 1 vectorized (equivalence-gated); Option B prerender/payload split (141 prerendered pages, front door 128KB); full re-score + Max's five audit fixes, all live on liftmath.lailarallc.com. Every headline moved (DECISIONS 2026-08-27). Plan as executed:

Upstream v0.5.0 raises promoted volume ~30–45x, which changes unit truth and invalidates
every accuracy number scored against the current generation — so it is a re-validation
epoch, not a patch. This repo's sequence, once the data repo releases v0.5.0: re-pin —
full re-score as a **logged re-run** (before/after error in DECISIONS; every headline number
moves) — **copy re-audit** (each on-screen figure re-checked against the new artifacts)
— **revisit the no-portfolio-% / trade-spend-to-revenue constraint** now that
spend-to-revenue is realistic (DECISIONS 2026-08-24). **Then Option B.**

### Next arc — Option B estimators: observed-only dip + transfer (tools 1c/1d)

Post-event pantry-load **dip** and sibling-delta **transfer**, estimable from
observed data, each with its own pre-registration tag and accuracy scoring; the
headline moves net → net-of-dip as a logged re-run, and the anatomy waterfall gains
its 4th and 5th bars honestly. See DECISIONS 2026-08-22.

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->

### 2026-09-23 — Audit (health check only)
- **Findings:** 1 critical, 3 important, 2 nice-to-have
- **Top concerns:** (1) CRITICAL — cost/coverage mismatch in `common.assemble`: an event's net margin sums only its estimable store-weeks, but ROI and `lost_money` compare it to the event's FULL `accrued_cost`. Method 1 covers only 74% of promoted units (3,585 of 5,122 estimable events partial; 1,195 under 50% row coverage), so it charges ~26% of spend with zero margin: pro-rating cost by covered units moves M1 lost-money 2,470 -> ~1,491 and portfolio ROI 1.18 -> ~1.58 (M0: 2,170 -> ~2,019, ROI 1.38 -> ~1.43). This skews the live headline ("2,170 of 5,735 lost money") and the M0-vs-M1 toggle; no spec line or test covers it (estimators.md 2.2/2.6). Fix: scale cost to covered volume (or report only fully covered events), log as a re-run, add a test. (2) IMPORTANT — local `.venv` editable install still points at the old `projects/active/...` path, so `pytest` fails to collect 8 test modules (ModuleNotFoundError: incrementality) until `pip install -e ".[dev]"` is re-run; with PYTHONPATH=src all 84 tests pass (5m50s). (3) IMPORTANT — PLAN.md Goal/Tasks still describe Arc 2 (Event Anatomy, "all 131"); Arc 3 is done and the Option B arc is not opened. (4) IMPORTANT — ci.yml's missing-secret error tells you to add PROMO_RESPONSE_READ to this repo's Actions secrets, contradicting the org-level secrets rule. Nice: stale "131 events" comments in common.py / ci.yml; build.sh step labels mix [1/4] and [3/5].
- **Action taken:** Audit only — no fixes this session. Manual security, code-quality and statistics pass replaced the automated /security-review, /ce:review and data-science-reviewer (not available). Live site matches HEAD (CI green 2026-09-05; live headline 2,170 of 5,735 matches local artifact).
- **Next review:** 2026-12-22
