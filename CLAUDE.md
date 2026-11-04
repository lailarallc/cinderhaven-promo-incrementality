# cinderhaven-promo-incrementality — Project Context for Claude

Tier: Heavy

## What this project is

**Public name: Lift Math**, at `liftmath.lailarallc.com`. The repository keeps
its original name, `cinderhaven-promo-incrementality`; the two are not the same
string and should not be "corrected" into each other. Lailara LLC is the maker,
Lift Math is the tool — that split is what the header, footer and OG tags encode.


A trade-promotion incrementality tool for the Cinderhaven universe: **three
linked views** on one promo-event spine, each with a distinct persuasive job.

1. **ROI Scorecard** — the verdict. Portfolio header (total accrued trade
   spend, net incremental margin, portfolio ROI, N of 131 events that lost
   money) over a ranked event list. First paint must be readable by a CEO or
   CFO in 30 seconds: verdict line, one chart, three numbers. Exploration is
   opt-in depth after the verdict, never a prerequisite for it.
2. **Event Anatomy** — the explanation. Click any event for the full
   decomposition: gross promoted → subsidized baseline → net incremental,
   with the baseline-method toggle inside the view. Dip and transfer are a
   later estimation arc, not shipped bars. This
   answers the objection that actually happens in the room — *"that August
   BOGO was my call, I know it worked, your tool says it lost money"* — which
   accuracy-in-general cannot.
3. **Accuracy** — the proof, and the view no comparable tool can show. An
   **estimate-vs-truth** view scored against quarantined ground truth, error
   reported by regime, seeded stories marked and separated, naive estimator
   shown losing.

It consumes `cinderhaven-promo-response` v0.4.0 and adds no data of its own.

Scope was six views until 2026-08-17. Baseline Builder, Lift Split, Net Lift
and Portfolio were the same decomposition at four zoom levels and collapsed
into Event Anatomy. See DECISIONS.md for the reasoning. **Do not solve "the
tool looks thin" by adding views back** — depth per view beats view count.

The differentiator is not the estimator. It is that the estimator is
**blind and provably so**, and its error is then measured against known
truth. Every real-world incrementality tool asserts accuracy; this one
demonstrates it.

Precision about that claim, because it is load-bearing and easy to
overstate: **"provably blind" applies to the code** — the AST gate plus the
`config` ban. The method-level claim is *"this is the error a standard
method makes under a realistic, fully-known world — measured, by regime,
including where it is large."* It is **not** a claim that measured error on
Cinderhaven predicts error on a client's data. Full reasoning, and the three
structural defenses against human leakage, in the external-validity entry in
DECISIONS.md.

**Business question this project answers:** How wrong is a trade-promotion
incrementality estimate, and can that error be shown rather than claimed?

## Stack and tools

**Settled 2026-08-17.** Python engine computes at build time and writes
precomputed artifacts; **SvelteKit + D3**, static via `adapter-static`,
deployed to **Cloudflare Pages**, renders the three views.

- **The estimation engine is Python.** Not a stylistic choice —
  `cinderhaven_promo_response.testing.assert_no_truth_access` parses source
  with `ast` and can only audit `.py` files. Estimation code in any other
  language makes the project's central credibility claim unenforceable.
- **The data dependency is `cinderhaven-promo-response` v0.4.0**, pinned,
  consumed through its public API only. See "Consumer contract" below.
- **SvelteKit was chosen for one narrow reason:** the requirements are
  router-shaped — persistent cross-view filters, deep-linkable events,
  comparison mode. Observable Framework is a multi-page app with no
  client-side router and no built-in cross-route state, which would put a
  document load on the tool's most-used transition. Dash was rejected as an
  always-on server for data that never changes. Full reasoning and the
  recorded caveat in DECISIONS.md.
- **The 1,340,462 scan rows never reach the browser.** Everything a view
  needs is precomputed. No client-side query layer, no DuckDB-WASM, no
  server.
- **Money is integer cents** through the pipeline, quantized once at the row
  grain with **round-half-even** (banker's). Units are **continuous**, not
  integer — the upstream noise deviate makes `observed_units` fractional on
  every row (corrected 2026-08-19; the earlier "units are integers" premise was
  an eng-review error the schema check caught). The row-level integer-cent
  value is the atomic unit both roll-ups share, so reconciliation asserts
  **equality**, no float tolerance. Round-half-even, not half-up: across
  1,340,462 rows half-up biases totals upward; half-even does not.

## Consumer contract — cinderhaven-promo-response v0.4.0

This is the whole interface. Do not reach around it.

```python
import cinderhaven_promo_response as pr
events, delta = pr.load()   # observed layer only; ~8.5s cold, ~0.6s warm
```

- `promo_events` — 131 rows.
- `promo_scan_delta` — 1,340,462 rows × 8 observed columns:
  `sku`, `store_id`, `week_ending`, `observed_units`, `regular_price`,
  `promoted_price`, `promo_id`, `complied`.
- Truth is **not** returned by `load()`. `truth.load_truth()` is the only
  door, and it lands in `.cache/truth-quarantine/`, never beside the
  observed parquet.
- `truth.assert_aligned_with_observed(delta)` — call before publishing any
  accuracy number. It refuses observed rows from one run scored against
  truth from another. That is the only completely silent failure mode in
  the data package.
- Reconciliation identity, bit-exact per row:
  `observed_units ≡ baseline + lift − dip ± transfer + noise`. Noise is
  stored, never inferred.

The upstream package is additive and never alters canonical. Trailing-52-week
canonical scan revenue ($32,323,139.62) is untouched by construction. All
figures must match CINDERHAVEN_CANONICAL.md.

## Project-specific hard rules

These are the rules that make this tool defensible. Violating any one of
them invalidates the deliverable.

### The truth gate runs in CI from day one

- CI runs `assert_no_truth_access` over **all estimation code**, on every
  push, from the first commit that contains an estimator — not added later
  when convenient.
- The accuracy view is the one module allowed to import truth. It is
  exempted **by name** via `exclude=(...)`, deliberately and in the open.
  A broad glob exemption defeats the gate.
- Do not re-implement the check. Import the package's own gate. A consumer
  re-implementing it is asserting its own good intentions; running the
  same gate on both sides of the boundary is the claim worth making.
- Do not weaken, skip, or mark `xfail` this test. It is the credibility of
  the accuracy view.
- **Truth flows one way. Nothing outside the accuracy module may import it**,
  directly or transitively — asserted by its own test. The gate is per-file:
  an estimator that imports the accuracy module reaches truth at runtime
  while its own AST stays clean and the gate passes. The gate alone does not
  establish blindness.

### Nothing published contains truth — including in its labels

- Artifacts written for the front end may carry **error metrics derived from
  truth**. They may never carry **truth values**. The accuracy artifact's
  schema is asserted by a test.
- `.gitignore` does not cover this. It excludes `.cache/` and `*.parquet`, so
  the quarantined table cannot reach git — but the accuracy module writes an
  artifact into the site's published data directory by design. This repo will
  be public.
- **Regime labels are built from observed features only** — promo type,
  depth, duration, season, product line, calendar position. Truth-derived
  labels leak generator structure even with every value aggregated away:
  "error by actual-compliance band" reveals per-event compliance by
  inspection. A truth-derived cut, if genuinely necessary, aggregates to ≥N
  events per bucket and is labeled truth-derived in the schema.
- The general form, worth remembering: **the gate protects values; structure
  walks out through labels.** Same shape as the transitive-import hole — the
  named defense is narrower than the thing it defends.

### Estimates are blind

- **The allowed surface is exactly three names:** `load()` (the observed
  layer), `economics()` (the product price card — per-SKU COGS and
  per-SKU×retailer wholesale/unit margin; arrives in upstream v0.2.0), and
  `testing` (the truth gate, run against this repo's own code). Everything
  else is banned.
- **Demarcation principle — blindness protects the demand response, not the
  price card.** Lift, dip, transfer, compliance, seasonality, baseline
  velocity: the estimator must never see these. COGS and wholesale price are
  product economics a real client hands a vendor on day one; no vendor
  estimates a client's COGS and no accuracy claim rests on not knowing it.
  `economics()` mirrors the real engagement exactly.
- **Banned: `config`, `constants`, `baseline`, `assortment`, `truth`.** `config`
  holds the response coefficients (`LIFT_CENTERS`, `DIP_FRACTION`). `constants`
  holds the baseline-demand generator (`BASE_UNITS`, `SKU_ARCHETYPES`,
  `ARCHETYPE_VELOCITY_MULT`, `SEASONALITY`, `SEASONAL_PROFILES`) — the true
  baseline by another route; `baseline` builds that series and `assortment`
  (v0.7.0) holds launch velocity, exit fades and sibling cannibalization. All are
  the answer key. The upstream AST gate denies `truth` and, since v0.7.0,
  `response`/`generate` and `build_response`/`load_truth`; `config`,
  `constants`, `baseline` and `assortment` are the "structure walks out past the
  gate" hole and are banned by convention plus this repo's own supplementary
  import check (imports and `pr.<module>` attribute access). If an estimator
  needs a prior, it derives it from observed data
  or cites an external source — never from the generator.
- No `baseline_units`, `lift_units`, or `caused_by_promo_id`, ever.

### Accuracy is reported honestly

- Report the error the estimator actually makes, including where it is
  large. A tool whose accuracy view shows uniformly small error is either
  cheating or not being tested hard enough.
- Do not tune an estimator against the truth table and then present its
  accuracy as an out-of-sample result. If an estimator is fitted against
  truth, say so and label it as an upper bound.
- `pantry_trap`, `hero_cannibal`, `pure_subsidy` and `clean_winner` are
  seeded stories the tool is *supposed* to find. Finding them is a pass.
  Reporting that it found them without showing the background distribution
  is not — the stories are outliers against a realistic mediocre middle
  (71% of US trade promotions don't break even, NIQ15 US cut).

### Canonical is never altered

- This repo reads the data package. It never regenerates, modifies, or
  reads the SSOT scan table, and never writes to the promo-response repo.
- Do not restate canonical figures as this tool's own output.

### Determinism

- Same package version, same seed, same estimator → same numbers. No
  wall-clock, no unseeded randomness in the estimation path.
- Pin the upstream package version. An accuracy number is meaningless
  without knowing which data generation it scored against.

## Project files

- CLAUDE.md (this file) — permanent rules and facts
- DECISIONS.md — durable choices and reasoning
- HANDOFF.md — current session state
- PLAN.md — current work arc
- FAILURES.md — things tried that didn't work

Read PLAN.md and HANDOFF.md at session start. DECISIONS.md and
FAILURES.md as relevant.

## Voice and standards

- Technical and precise. Declarative, data-forward, sober.
- Economist style for written deliverables (README, methodology notes):
  concrete, no throat-clearing.
- No marketing voice or consultant filler ("leverage," "synergy,"
  "best-in-class," "unlock," "drive value")
- No hedging that softens a real finding
- Charts must be readable by a trade-marketing manager, not only by a data
  scientist. A waterfall that needs a paragraph of explanation has failed.

## Rules

### Honesty and judgment

- Say "I don't know" or "I can't verify this" instead of guessing.
  This applies to industry context, technical claims, what code did,
  and anything else.
- Tell me what I need to hear, not what I want to hear. If a decision
  looks wrong, say so. If code I wrote has problems, say so. Honest
  assessment, not validation.
- If a rule in this file is too vague to verify whether you're
  following it, flag it for revision rather than guessing at compliance.

### Building and proposing

- No speculative abstractions. If something isn't needed right now,
  don't build it. Helper functions get added when called by real code,
  not in anticipation. Parameters get added when there's a second use
  case, not the first.
- When proposing a tool, library, or approach, present at least two
  alternatives with tradeoffs, even if one is clearly preferred. Do
  not propose a single solution and move on. The default failure mode
  is taking the route with less friction instead of the route that
  best fits the project — challenge yourself before proposing.
- Tie proposals back to the business question this project is
  answering. If you can't connect a proposal to that question, the
  proposal is probably fluff and should be reconsidered.

### How to work the project

- Work in vertical slices, not horizontal phases. For this tool a
  vertical slice is **one view end-to-end** — estimator, its accuracy
  measurement, the rendered view, and its test — before starting the
  next. Do not build all the estimators and then all the views.
- **Pre-registration ordering is a hard sequencing rule, not a preference.**
  The estimator spec and implementation are committed and tagged *before*
  any code in this repo loads truth. Estimator changes after first scoring
  are logged re-runs in DECISIONS.md with before/after error — never silent
  edits. Git history is the blindness evidence. See PLAN.md.
- **Slice 1 uses Method 0, the naive pre-period average, labeled as such on
  screen.** Baseline estimation is on the critical path of every downstream
  number including ROI. No unlabeled naive figures.
- **Public deploy gate: at least two baseline methods must exist** before
  anything goes to a lailarallc.com subdomain.
- When a feature is working, suggest a simple test to verify it stays
  working: "This works now — want to add a quick test so it doesn't
  break later?" Don't force testing, but make it easy to say yes.
- Do not start tasks outside the current PLAN.md arc without flagging
  it to the user first.
- Do not refactor unrelated code unprompted.
- Do not rename things unless asked.

### Git branching and worktrees

- **Work on main branch by default.** Do not create worktrees or
  separate branches unless the user explicitly asks for one. The
  overhead of merging back constantly is worse than the safety net
  of isolation for a solo developer.
- If you are already in a worktree when a session starts, push the
  work to main or create a PR to merge it — don't leave work
  stranded in a worktree.
- Before risky or experimental changes, suggest creating a branch:
  > "This is a significant change. Want to work on a branch so we
  > can easily undo it if it doesn't work out?"
- What counts as "risky": changing how the project is structured,
  trying a new library, rewriting a working feature, anything where
  you'd say "I'm not sure this will work."
- Keep it simple: `git checkout -b experiment/short-description`
  before the change, merge back to main if it works.
- Don't require branches for small, safe changes. This is about
  protecting against losing work, not adding process.

### Scope creep detection

- Periodically check whether the current work matches PLAN.md.
  If the user has been building something not in the plan for more
  than ~15 minutes, flag it:
  > "We've been working on [thing] but it's not in the current plan.
  > Want to add it to PLAN.md, or should we finish the planned work
  > first?"
- This is a gentle nudge, not a block. The user may have a good
  reason. But new developers often drift without realizing it, and
  drift is how projects never finish.
- Also flag if the user keeps adding tasks to PLAN.md without
  completing existing ones — the plan is growing instead of
  shrinking.
- Specific to this project: **changing the data package is scope creep.**
  `cinderhaven-promo-response` is released at v0.4.0 and is a separate
  repo. If this tool needs something the data doesn't have, that is a
  finding to log here and a release to plan there — not an edit made from
  this session.

## Working with PLAN.md

PLAN.md defines the current arc of work. Read it at session start.

- Mark tasks complete as they're finished, in the same commit as the
  work
- If a task is wrong-sized, in the wrong order, or no longer relevant,
  flag it rather than silently restructuring
- "Out of scope" items are decisions, not suggestions — do not pull
  them into the current arc without explicit user approval

## Session reminders

### Reminding the user to /log

Prompt the user to run /log when:

- A meaningful change just landed (file written, bug fixed, feature
  added, decision made)
- A natural pause point is reached (about to switch tasks, finished a
  chunk of work)
- Roughly 30-45 minutes have passed since the last /log and real work
  has happened since then

Format as a clearly separated note. Do not nag — one suggestion per
trigger.

### Reminding the user to /wrap

Prompt the user to run /wrap when:

- Context usage crosses 65%
- The user says anything that suggests they're stopping
- A natural milestone is reached
- 90+ minutes have passed and work is winding down

Format as a clearly separated note. Do not nag.

### Session start protocol

**CRITICAL: Do this BEFORE doing anything else — even before
responding to the user's first message.** Do not assume no work has
been done. Do not assume this is a new project. Read the files first.

1. Read CLAUDE.md (this file) — understand project rules
2. Read PLAN.md — understand current work arc and task list
3. Read HANDOFF.md — understand where the last session left off
4. Read DECISIONS.md — understand durable choices already made
5. Skim FAILURES.md — know what's already been tried and failed
6. If HANDOFF.md's most recent entry is more than 24 hours old AND
   there are uncommitted changes, flag this — the previous session
   may have ended without /wrap
7. Briefly state the starting point from HANDOFF.md so the user
   confirms you're caught up. Example: "Last session ended with
   [X]. Picking up from [Y]. Sound right?"
8. Confirm the current PLAN.md arc is still active
9. Check the Improvement History section of PLAN.md. If the project
   is overdue for an audit (see frequency guide in /improve), mention
   it: "This project is due for a review — run /improve or
   /improve audit-only when you're ready."
10. Remind the user what commands are available:
    > Quick reminder: type / to see your commands. The main ones are
    > /log (save checkpoint), /wrap (end session), and /improve
    > (review and improve the project). Run /commands for the full list.

**If any of these files don't exist yet, THEN you can assume this is
a fresh project. But if they exist — read them. No exceptions.**

### Suggesting commands during work

Don't wait for the user to remember commands exist. Proactively
suggest the right command at the right moment:

- User just finished a task → "Good time to /log that."
- User seems unsure what to do next → "Want to run /improve to
  see what needs attention?"
- User is about to stop → "Run /wrap before you go so your next
  session picks up here."
- User asks "what can I do?" or "what commands are there?" →
  "Run /commands to see everything available."
- Project is overdue for review → "It's been [X days] since the
  last /improve. Worth a quick /improve audit-only?"
- User just built a UI feature or fixed something visible →
  "Want to run /qa to test that in a browser?"
- User is starting a new project and hasn't challenged the idea →
  "Before building, run /office-hours to stress-test the idea."
- User has a plan but hasn't reviewed it → "Run /plan-ceo-review
  for the product check, then /plan-eng-review for the technical
  check."

Keep suggestions to one line. Don't explain the command every time —
just name it and say why now. If the user ignores the suggestion,
don't repeat it in the same session.

## Defaults

- Default to flagging gaps rather than filling with plausible-sounding
  but unverified content
- Default to short responses unless the task is substantive
- Default to asking before promoting a log entry to a DECISIONS.md
  entry
- Default to answering, not offering to answer
