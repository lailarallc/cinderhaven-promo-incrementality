# cinderhaven-promo-incrementality — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-08-17 — The estimation engine is Python. Not a preference — a constraint.

- **Why:** The project's central claim is that estimates are blind and
  provably so, enforced by `cinderhaven_promo_response.testing.assert_no_truth_access`
  running in CI. That function parses source with `ast` and walks it for
  forbidden imports and string literals. It can audit `.py` files and
  nothing else. Estimation code written in TypeScript, SQL, or R would make
  the gate silently vacuous — it would pass by never being applied.
- **Scope:** global; all estimation code.
- **Do not:** re-implement the gate in another language to work around this.
  A consumer re-implementing the check is asserting its own good intentions;
  importing and running the package's own gate is the claim worth making.

### 2026-08-17 — Consume the data package through its public API only.

- **Why:** `pr.load()`, `truth.load_truth()`, `truth.assert_aligned_with_observed()`
  and `testing.assert_no_truth_access()` are the contract the package
  documents and tests. Reading its `.cache/` parquet directly, or importing
  its internals, bypasses the loader schema gates — including the one that
  hard-fails when a truth column rides along on the observed artifact.
- **Scope:** global.
- **Do not:** call `pd.read_parquet` on anything under the package's
  `.cache/`. Do not import `cinderhaven_promo_response.config` from
  estimation code — the generator's coefficients are the answer key, and
  the AST gate will not catch it because it only denies `truth`.

### ~~2026-08-17 — PENDING: front-end stack. Deferred to the planning process.~~

> **CLOSED 2026-08-17 by `/plan-eng-review`.** Superseded by "Front-end stack:
> SvelteKit" below. Body kept intact as history — the candidate analysis here
> was written against six views, scrollytelling and a 1.34M-row browser
> payload, all three of which turned out to be false. Read it for what was
> considered, not for what is true.

~~**Status: open. This is the first task in PLAN.md.**~~ Recorded here so the
planning process starts from the constraints rather than re-deriving them.

**What is already settled** (see the two decisions above): the engine is
Python, and the data arrives through `pr.load()`. The open question is only
what renders the five views, and whether anything needs a live server.

**The prior question, which should be answered first:** does this tool
compute at request time? Everything upstream is deterministic and seed-locked,
and the estimators are too — 131 events, and no user input changes a result,
only what is displayed. Baseline-method selection is the apparent exception,
but the method space is small (~3), so all methods can be precomputed and
toggled client-side. If that holds, the tool is a **build-time computation
with an interactive front end**, not a query service, and a Python web server
buys nothing while costing hosting, latency, and a cold-start story.

**Candidates evaluated on 2026-08-17, none chosen:**

1. **Python engine + Dash/Plotly on Fly.io** — the fleet default, included
   because it must be beaten on merit rather than skipped. One language end
   to end, a shape already shipped elsewhere, fastest to a working tool.
   Against: the callback model fights scrollytelling and a story-driven
   waterfall, five linked views make the callback graph brittle, and a Dash
   app looks like a Dash app — the flagship bar is exactly what it gives up.
   Always-on server for data that never changes.
2. **Python engine + Observable Framework, static, on Cloudflare Pages** —
   Framework's native model is Python data loaders at build time with
   markdown/D3 pages rendering the outputs, which is the architecture rather
   than a workaround; the Python/JS boundary lands exactly where the CI gate
   needs it. Full control over the waterfall, the cannibalization matrix and
   the type/color system, so the Lailara design system genuinely applies.
   1.34M rows ship as parquet and query client-side via DuckDB-WASM.
   Against: JS/markdown is new ground, Framework is a young project, and
   styling is real CSS work rather than component defaults.
3. **Python engine + SvelteKit + D3, static, on Cloudflare Pages** — highest
   ceiling on the visual result, scrollytelling native, nothing opinionated.
   Against: routing, loading, layout and chart primitives are all bespoke;
   roughly a week added to the estimate and the steepest learning curve.

**Deliberately excluded:** Evidence.dev. Strong at SQL scorecards and weakest
at custom composite charts, which is precisely the waterfall and the
cannibalization matrix.

**What makes this decision low-stakes to get wrong:** the engine is a plain
Python package under every option. If the front end disappoints, it is
replaced and 100% of the estimation code survives. Weigh the front-end
choice accordingly — it is reversible; the engine language is not.

**Do not** close this entry by picking an option in passing. Strike it
through and write a dated replacement naming the rejected alternatives.

**Requirements changed after this entry was written (2026-08-17, `/clarify`
and `/office-hours`).** The candidate analysis above assumed six views,
scrollytelling, and 1.34M rows in the browser. All three are now false. The
comparison must be re-run against the current requirements — three views,
precomputed artifacts, persistent cross-view filters and deep-linkable
events. Candidate 1 (Dash) is eliminated: an always-on server for data that
never changes. Candidates 2 and 3 are both still live, and the margin
between them narrowed when the scope dropped to three views. `/plan-eng-review`
tests them fresh and inherits nothing from the six-view framing.

### 2026-08-17 — Front-end stack: SvelteKit + D3, static, on Cloudflare Pages.

Closes the PENDING entry above. Decided at `/plan-eng-review`.

- **Decision:** Python engine writes precomputed artifacts at build time.
  **SvelteKit** with `adapter-static` renders three views, deployed static to
  Cloudflare Pages. D3 for the composite charts.
- **Why — one reason, narrowly:** the requirements are router-shaped.
  Persistent cross-view filters, deep-linkable events and comparison mode are
  shared client state across routes. SvelteKit provides a client router,
  stores and `searchParams` natively. Nothing else about this project argues
  for it.

**Rejected — Observable Framework, static, on Cloudflare Pages.** The closest
call, and rejected on evidence rather than taste. Framework is a **multi-page
app**: file-based routing, build-time page loaders, parameterized routes, and
— across its routing, page-loaders and params documentation — **no client-side
router and no built-in cross-route state**. The requirements are reachable via
URL search params plus a shared module, but hand-rolled, and a document load
lands on the **primary interaction path**: clicking an event row in the
Scorecard to open Event Anatomy is the most-used transition in the tool and it
would flash. Comparison mode across a page load is worse. *Caveat recorded
honestly: this rests on Framework having no undocumented client router. Three
documentation queries found none. If that is wrong, this decision is worth
revisiting — the rest of Framework's model, especially Python data loaders at
build time, fit this project well.*

**Rejected — Dash/Plotly on Fly.io.** An always-on server for data that never
changes: hosting cost, cold-start story and latency bought nothing. Plotly
defaults fight the Lailara design system, and the flagship bar is exactly what
that gives up.

**Rejected earlier — Evidence.dev.** Strong at SQL scorecards, weakest at
custom composite charts, which is precisely the waterfall.

- **What makes this safe to have gotten wrong:** the engine is a plain Python
  package under every option. A front-end swap costs zero estimation code. The
  decision was made decisively rather than deliberated further, because the
  project's named primary risk is the stall, not a wrong front end.
- **Scope:** everything that renders.
- **Do not:** add a server. Do not introduce a client-side data query layer —
  artifacts are precomputed and small by decision.

### 2026-08-17 — Three views, not six. Scope halved.

- **Decision:** Build **ROI Scorecard**, **Event Anatomy**, **Accuracy**.
  Nothing else.
- **Why:** Baseline Builder, Lift Split, Net Lift and Portfolio were five
  separate tools in the original brainstorm that got inherited as views
  without re-justification. They are the same decomposition at four zoom
  levels. Collapsed into Event Anatomy as segments of one waterfall rather
  than four navigations. Every persuasive job stays assigned: the Scorecard
  is the verdict, Event Anatomy is the explanation, Accuracy is the proof.
- **What Event Anatomy has to answer, and why Accuracy cannot:** the
  objection that actually happens in the room is per-event — *"that August
  BOGO was my call, I know it worked, your tool says it lost money."* The
  trade lead is defending a promo, not auditing an estimator.
  Accuracy-in-general does not defuse that; anatomy-of-this-number does.
  The full chain, for that event: gross → subsidized baseline → dip →
  transfer → net, with the baseline-method toggle and the transfer panel
  inside the view.
- **Scope:** global; supersedes the five-view framing in CLAUDE.md.
- **Do not:** solve "the tool looks thin" by adding views. Depth per view
  beats view count — one anatomy view with a working method toggle is
  deeper than four shallow pages.

### 2026-08-22 — Event Anatomy is a three-bar observed waterfall. Dip and transfer are the NEXT estimation arc, not truth on this page.

- **Decision:** The Event Anatomy waterfall shows **exactly what a blind estimator
  knows**: `gross promoted volume → subsidized baseline (giveaway) → net incremental
  lift` — three bars, from observed + estimated data only, with the M0/M1 toggle and
  margin/accrued cost alongside. **Dip and transfer are NOT bars on this page.** They
  are the demand response an estimator must never see (CLAUDE.md), so putting them on
  an observed-only page would either require truth (a leak) or fabricate them.
- **How the flaw surfaced:** the requested waterfall listed `dip` and `transfer`
  segments; the blindness boundary caught that they are protected truth quantities
  the estimators legitimately do not produce. The discipline working — the anatomy
  view was one step from quietly becoming a truth leak. Showing only what can be
  defended is the house position.
- **Option B is the planned NEXT estimation arc, not a rejection.** Observed-only
  **pantry-load** and **cannibalization** estimators are the original brainstorm
  tools **1c / 1d**. Post-event **dip** (observed shortfall below baseline in the
  weeks *after* the promo) and **sibling-delta transfer** (other SKUs' shortfall
  during the promo) **are estimable from observed data** — no truth needed. They
  will arrive with their **own pre-registration tags**, their **own accuracy
  scoring**, and the headline change (**net → net-of-dip**) recorded as a **logged
  re-run**. A's three-bar waterfall then gains its fourth and fifth segments
  honestly, as estimates that can be scored — not as a fudge.
- **Story-event annotations — the one rule for the anatomy narrative:** they may
  describe the story's **design intent from public upstream documentation** (the
  event is *named* `pantry_trap`, and the package's public docs say what that
  archetype represents), **never truth values** ("the true dip was X units" is
  banned — that is the /accuracy view's job, and even there only as error, never as
  a truth value). Truth stays one click away.
- **Scope:** Event Anatomy view; the anatomy artifact; the next estimation arc.
- **Do not:** put a dip or transfer bar on the anatomy page from truth. Do not quote
  a truth value in a story annotation. Do not change the Scorecard's net number to
  net-of-dip until the dip estimator ships as a logged re-run.

### 2026-08-19 — Blindness protects the demand response, not the price card. Economics via a blessed accessor.

- **Decision:** Estimation code's **allowed surface is exactly** `pr.load()`,
  `pr.economics()`, and `pr.testing`. `economics()` — per-SKU COGS and
  per-SKU×retailer wholesale/unit margin — is added upstream in **v0.2.0** in its
  own module that imports **no demand parameters**. `config`, `constants`, and
  `truth` are all banned.
- **The demarcation principle:** blindness protects the **demand response** —
  lift, dip, transfer, compliance, seasonality, baseline velocity — the things an
  estimator must not see. **COGS and wholesale price are not demand response.**
  They are product economics a real client hands a vendor on day one; no vendor
  estimates a client's COGS, and no accuracy claim rests on not knowing it.
  `economics()` mirrors the real engagement; withholding it would model a world
  no analyst works in.
- **Why a new accessor rather than reading `constants`:** `constants` tangles the
  price card (COGS, wholesale, MSRP — legitimate) with the **baseline-demand
  generator** (`BASE_UNITS`, `SKU_ARCHETYPES`, `ARCHETYPE_VELOCITY_MULT`,
  `SEASONALITY`, `SEASONAL_PROFILES`). Importing it for COGS also hands over the
  true seasonal and velocity structure — the baseline Method 0 is supposed to
  *estimate*. That is a blindness breach the AST gate does **not** catch (it
  denies `truth`, not `constants`) — the same "structure walks out past the gate"
  hole as the `config` ban. The fix is upstream separation, not a consumer
  workaround.
- **Enforcement:** the allowed surface is asserted by this repo's own
  supplementary import check over `src/` (bans `config`/`constants`), on top of
  the upstream `assert_no_truth_access` truth gate. Lands with the pipeline
  commits.
- **Rejected — external cited margin %:** would ship slice 1 without waiting on
  v0.2.0, but folds a margin-assumption error into what the accuracy view later
  presents as *estimation* error — muddying the one attribution the tool exists
  to keep clean. Not worth blurring the thesis exhibit for ship-now.
- **Rejected — revenue-basis ROI (no COGS):** systematically overstates ROI
  (SPEC.md's own msrp-vs-wholesale warning); an ROI that flatters promos is the
  competitor's product, not this one.
- **Scope:** all estimation code; the CI gate; the upstream v0.2.0 release.
- **Do not:** import `constants` or `config` from estimation code. Do not compute
  margin from MSRP — manufacturer margin is wholesale − COGS.

### 2026-08-21 — Method 1 is a cross-banner, identity-matched comparable-store baseline. It needs `store_card()` (v0.3.0).

- **Decision:** Method 1 (spec §3, pre-registered 2026-08-21) is a comparable-store
  baseline: for each promoted store-week, the counterfactual is the **median
  velocity of comparable control stores in that same week**, where comparability is
  defined on **observed store identity** — `region` and `store_format` from a new
  upstream accessor `store_card()`, plus an observed volume band. Controls are drawn
  **cross-banner**. The pipeline is **blocked on upstream v0.3.0** shipping
  `store_card()`, same pattern as Method 0 blocked on `economics()` (v0.2.0).
- **Why cross-banner, and why the store-card is needed — measured, not asserted:**
  same-banner clean control pools are **empty for 40 of 131 events and < 5 for 106
  of 131** (median 2), because promotions in this universe are **banner-wide** — a
  promo covers essentially every store of its retailer carrying the SKU. A
  same-banner comparable method would exclude ~80% of events. Valid cross-banner
  matching requires store identity (region, format) that the observed layer does not
  carry (`store_id` gives only the banner prefix; `economics()` is per SKU×retailer).
  This is the STOP-AND-ASK trigger firing exactly as pre-authorized — improvising an
  observed-only proxy or reaching into `constants` was declined in favor of the
  proper upstream accessor.
- **`store_card()` demarcation, verbatim (governs the v0.3.0 release):** the card
  carries what a client's store master actually contains — geography and format
  identity. **Volume tier is derived by the estimator from observed pre-period
  velocity, never shipped on the card**; anything velocity-shaped stays off it,
  because baseline velocity is on the protected side of the blindness line. That
  keeps `store_card()` unambiguously on the identity side, same as `economics()`.
  Own module, imports no demand parameters, AST-clean, demand-free import test.
  Allowed surface becomes `load()`, `economics()`, `store_card()`, `testing`.
- **Provisional constants, tuned on pool size not error:** `MIN_POOL` (the
  minimum-comparable-pool floor, with exclusion reason `insufficient_comparable_pool`)
  and the volume band cannot be set until `store_card()` ships the identity columns
  to measure the matched-pool distribution. They will be tuned **against observed pool
  size, never against truth/error**, and logged before first scoring — tuning a blind
  estimator against the answer key is the one thing pre-registration forbids.
- **Rejected as Method 1 — the indexed diff-in-diff (a Method 2 candidate, not a
  fallback):** baseline = test store's own pre-period × the control pool's during/pre
  velocity ratio. Fully observed (banner + velocity), no release needed. It is a
  **legitimately different standard method**, and as its own pre-registered method
  later it would strengthen the multi-method accuracy story. Its only sin here is
  that it is not the attribute-matched comparable-store method §3 set out to register.
  **Logged as a future Method 2 candidate**, not a rejected approach.
- **Scope:** `docs/estimators.md` §3; Method 1 estimation code; the CI gate; the
  upstream v0.3.0 release.
- **Do not:** define comparability on same-banner controls only (the pools are
  empty). Do not ship a volume/velocity tier on `store_card()`. Do not tune
  `MIN_POOL` or the band against measured error. Do not implement Method 1 before
  the consumer is pinned to a `store_card()`-bearing release.

### 2026-08-21 — Re-pin to v0.3.0 (store_card()). Logged re-run per the pin decision.

- **Decision:** The consumer is re-pinned from v0.2.1 (`11caa13`) to **v0.3.0**
  (`6556460000d56fd2df1c89c59f592f363b93245c`), which adds `store_card()`. Logged
  as a **re-run** per the pin decision — an accuracy number is meaningless without
  recording which generation it scored against, and the pin is the record.
- **Data-neutral for the observed layer:** `store_card()` is additive; `load()`
  still returns 131 events / 1,340,462 rows / the eight observed columns unchanged.
  No estimate that predates this re-pin changes because of it. Verified: the
  data-contract test asserts v0.3.0 and the unchanged observed shape, plus the new
  `store_card()` contract.
- **What `store_card()` actually ships:** `store_id`, `retailer_id`, `region` —
  and **no `store_format`.** The card is geography + banner identity; format is
  supplied consumer-side by judgment (next entry), and volume is derived by the
  estimator from observed velocity, never on the card.
- **Scope:** `pyproject.toml`; `tests/test_data_contract.py`; every Method 1 figure.
- **Do not:** report a Method 1 accuracy figure without recording the v0.3.0 SHA
  and seed alongside it.

### 2026-08-21 — `store_card().region` is package-assigned, not the SSOT draw. Never join it to platform store data.

- **Decision:** The `region` column from `store_card()` is a value the data
  package **assigns** to each synthetic store. It is **not** a draw from any
  single-source-of-truth store master, and it must **never** be joined to real
  platform store data — the store ids are synthetic and the join would be
  meaningless (and, if it appeared to work, misleading).
- **Why it still earns its place:** region is legitimate comparability identity —
  the estimator matches controls within a region — exactly the day-one store-master
  attribute a real vendor uses. Its being package-assigned is a property of the
  synthetic world, not a defect; the accuracy view measures how well identity-based
  matching recovers truth, and that measurement is honest whether the region labels
  are "real" or assigned, so long as they are never confused for platform data.
- **Scope:** all Method 1 code; any place `store_card()` output is used or displayed.
- **Do not:** join `store_card().region` to platform/real store data. Do not present
  it as a customer's actual region assignment.

### 2026-08-21 — Method 1 format class is a consumer JUDGMENT mapping (retailer → format), because store_card() ships no format.

- **Decision:** `store_card()` carries no `store_format`, so Method 1's match key
  uses a **consumer-side JUDGMENT mapping** from retailer to a coarse **format
  class**, tagged `JUDGMENT` in the estimator spec (§3):

      RET-COSTCO      -> club
      RET-WALMART     -> supercenter
      RET-WHOLEFOODS  -> natural
      RET-SPROUTS     -> natural
      RET-KROGER      -> conventional
      RET-REGIONAL    -> conventional

  The final match key is **region (`store_card()`) + format class (this mapping) +
  observed volume band**.
- **Why format class matters — it is what makes cross-banner matching valid:**
  banner alone leaves 80% of events with no controls (banner-wide promotion). Format
  class is coarser than banner — Whole Foods and Sprouts are both `natural` — so a
  Sprouts promo can borrow Whole Foods controls in the same region and volume band.
  That is the mechanism that turns the empty same-banner pool into a usable one.
- **Why it is JUDGMENT, and honest as such:** the mapping is the estimator author's
  retail knowledge, not read from the generator. It is cited as judgment (like every
  modelling assumption), predates any truth access, and is not tuned against error.
  A different analyst might class Sprouts separately from Whole Foods; that is a
  defensible alternative, logged if changed, never silently.
- **Scope:** `docs/estimators.md` §3; `method1.py`.
- **Do not:** derive format from `constants`/`config` or from truth. Do not change
  the mapping after first scoring without a logged re-run.

### 2026-08-21 — Method 1 matches hierarchically (format where it helps, region+volume where it can't). §3 amended r2, pre-truth.

- **Decision:** Method 1's comparable pool is matched by a **two-stratum hierarchy**,
  tightest stratum that clears `MIN_POOL`: (1) region + format class + volume band;
  (2) if that is `< MIN_POOL`, region + volume band with format class dropped. Below
  the relaxed stratum, `insufficient_comparable_pool`. `MIN_POOL = 5`,
  `VOLUME_BAND_FACTOR = 2`. Replaces the flat "region + format + band" match key of
  the first §3 freeze.
- **Why, measured on observed data before any truth access:** format class as a
  *hard* filter starves the pool, because `club` (Costco) and `supercenter`
  (Walmart) are **single-banner** format classes — "same format" collapses to "same
  banner," the empty pool the whole method exists to route around. Region+format
  clears `MIN_POOL` for only **33%** of the 4,070 store-events; region+volume clears
  it for **95%**. The flat match left **57 of 131** events estimable and dropped
  **all four seeded stories** (three are Walmart/supercenter). The hierarchy keeps
  format where it separates multi-banner classes (`natural` vs `conventional`) and
  degrades to region+volume exactly for the single-banner classes and nowhere else.
- **The relaxation is recorded per store-event in the artifact** (`full` vs
  `relaxed`), rolled up to a per-event relaxed share. It is an **observed** attribute,
  hence a legitimate regime dimension for the Accuracy view — "does error grow where
  matching relaxed?" — costing one boolean now versus an artifact migration later.
- **Pre-registration integrity:** this diverges from the match key frozen at
  `method1-preregistration`, so the amended spec is **re-tagged `method1-preregistration-r2`
  before any Method 1 code that loads truth exists** — no truth has been scored, both
  tags predate first truth access, and the evidence chain now contains the amendment
  and its measured justification. Tuned against **pool size, never error**.
- **Scope:** `docs/estimators.md` §3.3, §3.5; `method1.py`; the Scorecard artifact
  (new relaxed-share field).
- **Do not:** restore the flat format-as-hard-filter match. Do not tune `MIN_POOL`
  or the band against measured error. Do not drop the per-event relaxed share from
  the artifact — ### 2026-08-27 — v0.6.1 re-pin: VOLUME_BAND_FACTOR frozen at 2 (its derivation target is unreachable in the density world). Logged before any truth is scored.

- **Decision:** On the two-epoch re-pin to v0.6.1, hold `VOLUME_BAND_FACTOR = 2` frozen,
  alongside the already-constant `MIN_POOL = 5`. Both are pre-truth constants: the doubling
  band predates this generation and encodes nothing about its truth — exactly the property
  pre-registration wants. This resolves the band question the v0.6.1 re-pin raised, recorded
  **before any truth is scored on v0.6.1.**
- **Why the derivation rule could not be re-run:** the original rule (r2, above) set the band
  from the observed matched-pool distribution so the region+volume stratum clears `MIN_POOL`
  for ~95% of store-events. On v0.6.1 that target is **structurally unreachable** — measured
  on observed data, before truth:

  | band factor | region+volume clears MIN_POOL |
  | --- | --- |
  | 2.0 (held) | 78.8% |
  | 2.5 | 84.8% |
  | 3.0 | 87.3% |
  | 4.0 | 89.5% |

  (171,846 store-events.) Clearance plateaus near ~90%: v0.6.1 puts ~25% of rows on promotion,
  so over a 4-week event window most stores are "dirty" and excluded as controls, and ~10% of
  store-events have no 5 clean same-region controls at any band width. **No factor reaches 95%.**
- **Why freeze, not re-derive to a new target:** every achievable target (a knee, a lower
  coverage number) is a value **chosen after seeing v0.6.1** — tuning a blind estimator's knob
  post-repin, which pre-registration exists to forbid. Freezing the pre-truth doubling band is the
  least-tuning choice; the 95% -> 78.8% clearance drop is a **measured consequence of the density
  epoch, reported as a data fact, not a knob.**
- **What the thinner pools mean, honestly:** more store-events fall to the relaxed stratum or to
  `insufficient_comparable_pool` exclusion, and error is expected to be larger where the matched
  pool is thin. That flows into the relaxed-share regime cut, the exclusion counts, and
  error-by-regime on the Accuracy view — the honest story the denser world tells, not a defect.
- **Scope:** `method1.py` (`VOLUME_BAND_FACTOR`, `MIN_POOL` unchanged); the v0.6.1 re-run.
- **Do not:** re-derive either constant against the v0.6.1 pool distribution or its error — after
  the re-pin that is tuning. ### 2026-08-27 — v0.6.1 two-epoch re-pin (calendar density + commercial dynamics): the logged re-run. Every headline moves.

- **Decision:** Re-pin cinderhaven-promo-response v0.4.0 (6399990) → v0.6.1 (bdb08c6), a
  two-epoch jump: v0.5.0 (calendar density, ~1% to ~34% of volume on promotion, 131 to 5,897
  events on the same 1,340,462-row spine) and v0.6.0 (commercial dynamics). Logged as one
  large re-run. Estimators unchanged and blind; the band-freeze (above) and the metric
  definitions were fixed BEFORE this scoring.

- **Before -> after (v0.4.0 M0/M1 -> v0.6.1 M0/M1):**

  | figure | v0.4.0 | v0.6.1 |
  | --- | --- | --- |
  | events | 131 | 5,897 |
  | estimable | 129 / 129 | 5,735 / 5,122 |
  | lost money | 45 / 48 | 2,170 / 2,470 |
  | portfolio trade spend | $80,449 (M0) | $2,930,338 / $2,728,644 |
  | net incremental margin | $118,200 (M0) | $4,052,667 / $3,221,594 |
  | portfolio ROI | 1.47 (M0) | 1.38 / 1.18 |
  | accuracy median abs error | 26% / 26% | 32.8% / 42.0% |
  | accuracy signed bias | +12% / +22% | +17.5% / +27.2% |

  Unit truth moved in both epochs, so accuracy re-scored for the FIRST time since launch.
  Method 1 error rose to 42% exactly as the band-freeze finding predicted — the density
  epoch thins the comparable pools, so the concurrent baseline is noisier.

- **Method 1 vectorized (equivalence-gated).** The loop is O(events x stores) and took ~9.5
  min at 5,897 events; vectorized it scores in ~47s. Proven bit-identical to the loop on the
  v0.4.0 world (7,440 rows), a v0.6.1 sample + the full portfolio, and a synthetic edge-case
  world — tests/test_method1_equivalence.py, loop kept as the oracle. A refactor that moves
  no number.

- **Option B artifact/prerender split.** Measured build implication: the monolithic build
  would prerender 5,897 pages and ship ~3.75MB (scorecard) + ~5.5MB (anatomy) to the browser.
  So anatomy -> per-event slices + a ~150-event prerender manifest (stories + top |net margin|
  + top spend); scorecard -> summary + first page imported, full events fetched on demand and
  cached; adapter-static fallback for non-prerendered events. Front door 128KB, ~141
  prerendered pages, build 15s.

- **The no-portfolio-% constraint (2026-08-24) is LIFTED** — its own lapse condition (v0.5.0
  calendar density) is met. Portfolio economics are realistic: trade spend ~2.3% of total
  revenue, ~7.7% of promoted revenue (the event-level promotion allowance, not all-in trade).
  Both quotable. tests/test_no_portfolio_spend_ratio.py removed; the scope note states the
  ratios instead of warning them off.

- **Scope:** the whole pipeline + front end; the v0.6.1 generation only.
- **Do not:** present the v0.6.0 price->volume dynamics as a FINDING — it is the generator's
  authored knob (owner, 2026-08-27), presentable only as mechanics, never a discovery. Do not
  re-derive the frozen estimator constants against v0.6.1 (see band-freeze).

### 2026-11-04 — v0.7.0 re-pin (assortment epoch): the logged re-run. Truth and the key universe move.

- **Decision:** Re-pin cinderhaven-promo-response v0.6.2 (820e193) → **v0.7.0 (ff596fe)**,
  the assortment epoch. Logged as a full re-run: scorecard, anatomy and accuracy re-scored;
  estimators unchanged and frozen at their tags. The four upstream-pre-registered error
  regimes (SPEC §4.9.7) are scored as two new observed-only cuts, defined in
  `docs/accuracy-spec.md` §11 and tagged `accuracy-preregistration-v0.7.0` **before** any
  code in this repo read v0.7.0 truth (tag pushed before the scorer ran; git history is the
  evidence).
- **What moved, measured from scan presence (seed 42):** 9 launches, **8** exits (6
  incumbents + 2 launches). The task brief said 12 exits; the observed layer says 8, and the
  measured figure is the one recorded. 59 SKUs; `promo_scan_delta` 1,340,462 → **1,293,126**
  rows; `promo_events` 5,897 → **5,636**. Zero overlapping same sku × retailer events.

- **Before → after (v0.6.2 M0/M1 → v0.7.0 M0/M1):**

  | figure | v0.6.2 | v0.7.0 |
  | --- | --- | --- |
  | events | 5,897 | 5,636 |
  | estimable | 5,735 / 5,122 | 5,484 / 4,818 |
  | lost money | 2,170 / 2,470 | 2,137 / 2,333 |
  | portfolio trade spend | $2,930,338 / $2,728,644 | $2,981,268 / $2,680,543 |
  | net incremental margin | $4,052,666 / $3,221,594 | $4,300,601 / $3,189,052 |
  | portfolio ROI | 1.38 / 1.18 | 1.44 / 1.19 |
  | accuracy median abs error | 32.8% / 42.0% | 33.8% / 41.2% |
  | accuracy signed bias | +17.5% / +27.2% | +17.5% / +27.6% |
  | events scored (% defined) | 5,625 / 4,957 | 5,369 / 4,624 |
  | top-decile share of net margin | 58% / 56% | 59% / 58% |
  | spend / total revenue · / promoted revenue | 2.4% · 7.7% (hand-typed) | 2.4% · 7.7% (computed) |

  Portfolio headlines move modestly; the regime tables move by at most a few points
  (Method 1 Costco 82.3% → 77.6%, Walmart 32.4% → 37.6%, the largest).

- **The stories moved, and one error is now large — reported full-size.** Upstream re-placed
  every story event (v0.7.0 protects story tracks across a full dip tail), so all four are
  different promo_ids. Signed error, M0 / M1:

  | story | v0.6.2 | v0.7.0 |
  | --- | --- | --- |
  | pure_subsidy | PRE-0100: −29.2% / +4.3% | PRE-0098: −23.0% / +12.4% |
  | hero_cannibal | PRE-1985: +11.0% / +6.7% | PRE-1951: +3.8% / +7.2% |
  | pantry_trap | PRE-2568: +1.3% / +3.5% | PRE-2555: +11.4% / +7.0% |
  | clean_winner | PRE-4028: −16.3% / +38.1% | **PRE-3930: +180.1% / +184.5%** |

  `clean_winner` is now a 10%-off `digital_coupon` (Kroger, SB-005, 2023-06-03) with
  same-line sibling promotions at the same retailer around it — the small-denominator coupon
  regime the page already flags (digital_coupon median error 105% / 133%). Both methods
  nearly triple its true lift; it still ranks as a strong winner (ROI 5.74× / 6.67×). A
  measurement fact of the new placement, not a scorer defect (observed context checked
  first, per src/CLAUDE.md). **Not tuned.**

- **The four pre-registered predictions — results, not tuned (5 of 8 checks hit):**

  | prediction (SPEC §4.9.7) | predicted | M0 | M1 |
  | --- | --- | --- | --- |
  | 1 launch, life weeks 1–13 | biased high; early ones inestimable | +64.8% hit (29 of 42 estimable) | +45.4% hit (15 of 42) |
  | 2 exit fade, final 13 weeks | biased low | −15.7% hit | +36.1% **miss** |
  | 3a after same-line launch | biased low | +21.9% **miss** | +28.9% **miss** |
  | 3b after same-line exit | biased high | +13.0% hit | +24.2% hit |
  | 4 launch promos lose ≥ as often | estimated loss rate, launch window vs continuing | 7% vs 39% — **reversed** | 87% vs 48% — kept |

  Reading the misses honestly: prediction 2 is a pre-period mechanism and Method 1 is not a
  pre-period method, so its miss is the mechanism not applying, not the prediction being
  wrong for Method 0 — but it is scored as a miss, as pre-registered. Prediction 3a misses on
  both: the after-launch bucket runs *hotter* than the background (+21.9% vs +18.1% for M0),
  not colder. Prediction 4 is the commercially loud one: **Method 0's ramp-inflated launch
  baseline error (+64.8%) makes launch-window promotions look like near-certain winners (7%
  lost) when the data package's own order-independent ledger says they lose slightly more
  often than continuing ones.** Method 1 keeps the ordering, on 15 events. *(Scoped by the
  2026-11-06 logged correction: upstream compares launched vs **incumbent** SKUs over whole
  life, true ROI; the figures here are estimates on the life-weeks-1–13 slice. Matched truth
  confirms both outcomes.)*

- **Row attribution — the stated rule (accuracy-spec §11.1).** Lift Math **never read
  `caused_by_promo_id`**, before or after this re-pin: a promoted row belongs to the event
  named by its observed `promo_id`, and its truth quantity is the full row-level
  `lift − dip + transfer`, which upstream accumulates additively. So upstream's first-claim,
  SKU-order-dependent cause tag (its audit #9, the defect that moved launch-promo loss rate
  47% → 64% upstream) never reached this tool's numbers. What was missing was the rule being
  *stated and enforced*. Now: `accuracy.assert_one_event_per_row` **refuses to score** if two
  events on one sku × retailer overlap, a test asserts `accuracy.py` never mentions
  `caused_by`, and the rule is in the spec. The brief suggested a tie-break ("earliest event
  by id"); refusing is stricter — a tie-break would silently re-attribute rows the observed
  layer already attributes, and there are zero ties to break.
- **Import ban extended** to the package's `baseline` and `assortment` modules (upstream
  audit #6), plus `pr.<module>` attribute access for all four banned names. Separate commit,
  demonstrated to fire.
- **Scope-note ratios now computed** (`scorecard.summary.spend_context`): spend ÷ observed
  revenue at the price paid (`promoted_price` on complied promo rows, `regular_price`
  otherwise). The prior hand-typed "2.4% / just under 8%" had no recorded derivation; the
  computed definition reproduces it (2.4% / 7.7%, 34.6% of volume on promotion).
- **Scope:** pipeline, accuracy artifact (`accuracy/v2`), Scorecard + Accuracy copy; the
  v0.7.0 generation only.
- **Do not:** re-derive the 13-week life window, or any regime boundary, against the v0.7.0
  errors above — that is tuning. Do not read `caused_by_promo_id` anywhere. Do not present
  the launch-window M0 loss rate as a finding about launches; it is the estimator's error.

### 2026-11-06 — LOGGED CORRECTION (Max's audit blocker): prediction 4 — the page sentence was mis-scoped, not mis-signed. No outcome changes.

- **Decision:** The accuracy-page economics paragraph names the measurement it cites and
  the narrower slice its own figures cover. Prediction 4 stays: **holds in truth**; Method 0's
  estimate **reverses** it; Method 1's estimate **keeps** it. Verified against truth on the
  same buckets, not inferred from a different population.
- **The blocker:** the audit read the package's DECISIONS as recording launch promos losing
  *less* often (47% vs 64%, a logged miss), against this page's "slightly more often". Both
  figures are in the package, but the 47%-vs-64% one is **superseded inside the pinned tag
  itself**. At `ff596fe` (v0.7.0), upstream DECISIONS strikes it through and records the
  2026-11-04 plausibility-audit correction: it came from the order-dependent
  `caused_by_promo_id` ledger (audit #9). On an order-independent ledger (each event's own
  lift minus the dip on its own SKU) launch promos lose **more** often: seed 42, 64% vs 61%;
  seed 43, 65% vs 62%. **Prediction 4 HOLDS** upstream. The page's direction was right.
- **What was wrong — two scope errors, one population/denominator difference:**
  1. The sentence did not name what it cited. Upstream's figure is **true** ROI, all
     promotions on launched SKUs over each item's whole life, against **incumbent** SKUs,
     on upstream's ledger. The page said "continuing ones" and named no ledger.
  2. The figures beside it are a different population and denominator. They are
     **estimated** loss rates for `launch (life weeks 1–13)` against `continuing`
     (which excludes exit-fade and launch-after-week-13 events), counting each method's
     **estimable** events only (M0 29 of 42, M1 15 of 42 launch-window events).
  3. So "M1 keeps the true ordering (87% vs 48%)" (PR body, 2026-11-04 entry above) set an
     estimate on one slice against truth measured on another. It was unverified, not wrong.
- **Verification, on Lift Math's own estimand** (accuracy-spec §2/§11.1: causal
  `lift − dip + transfer` on the event's own promoted rows, attributed by observed
  `promo_id`, margin and cost exactly as `common.assemble`). This was a scratch run, nothing
  added to the artifact, and every bucket is ≥5 events (§6):

  | slice | launch (wk 1–13) | continuing | ordering |
  | --- | --- | --- | --- |
  | truth, all events, all promoted store-weeks | 45.2% (n=42) | 44.2% (n=5,455) | holds, by 1 pt |
  | truth, M0's estimable events at M0's store-weeks | 48.3% (n=29) | 47.1% | holds |
  | **M0 estimate**, same events | **6.9%** | 38.9% | **reversed** |
  | truth, M1's estimable events at M1's store-weeks | 73.3% (n=15) | 62.2% | holds |
  | **M1 estimate**, same events | **86.7%** | 48.1% | **kept** |

  Truth on each method's own scored rows has the same ordering, so "reversed" and "kept"
  are confirmed. Truth's margin is small (1 pt on all events, 1–11 pts on the scored
  subsets), so "slightly" is the correct word. M1 keeps the ordering but overstates the gap.
- **Not added to the artifact.** §11.5 pre-registered `life_stage_economics` as estimates
  and observed counts only. Adding a truth loss rate after scoring would be a post-hoc
  schema change. These figures are verification on record, not page copy. The page states
  the measurement and scope in words and hand-types no upstream number (artifact-fed copy).
- **Decided under the fork policy, flagged for Max:** (a) publish the matched-truth table in
  DECISIONS rather than the artifact; (b) the page names upstream's measurement without
  quoting 64%/61%.
- **Scope:** `web/src/routes/accuracy/+page.svelte` (economics paragraph), PR #1 body. No
  estimator, artifact or outcome change.
- **Do not:** cite the struck 47%-vs-64% figure as upstream's result. Do not compare an
  estimated launch-window rate with upstream's whole-life true rate as if they share a
  population. Do not read `caused_by_promo_id` to reproduce upstream's numbers.

### 2026-11-09 — AUDIT PASSED (Max): v0.7.0 re-run and the Nov 9 relabel are audited and closed.

- **Decision:** The v0.7.0 logged re-run (PR #1, merged a5dc539), the prediction-4 scope
  correction (76aac28), the trade-partner relabel (b0a49f9) and the discount-depth rounding
  (6556270) are audited live and closed. Lift Math has no open audit items.
- **What Max checked, live:** /accuracy — 5 of 8 predictions matches its table; the four
  life-stage rows sum to the 5,484 / 4,818 scored events in the headline; those reconcile
  to the 5,636 events in the data files; package is v0.7.0; live matches the build.
  /event/PRE-0807 — baseline + net = gross under both methods; return on spend = margin ÷
  cost; depth reads 10.98%; retailer reads "National mass retailer". Real names: the label
  map covers all six retailer IDs; the only real-name strings in source are dropdown option
  values (IDs, exempt under the 2026-11-05 ruling).
- **Tool-label gate:** 0 violations on liftmath.lailarallc.com (2026-11-09), down from 124.
- **Not this repo:** the platform label map's RET-REGIONAL reads "Regional Group" and should
  read "regional grocer group". The fix belongs in the platform's
  `retailer_display_labels.json` and reaches every tool that vendors the map; Lift Math picks
  it up on its next re-vendor. No local override.
- **Do not:** patch the label locally in this repo — a local override forks the map the
  label gate reads.

### 2026-11-04 — Truth-moving re-runs freeze on a branch until Max's audit; merge to main deploys.

- **Decision:** The v0.7.0 re-run is pushed to `rerun/v0.7.0` with a PR, not to `main`. Push
  to `main` auto-deploys to liftmath.lailarallc.com (ci.yml `build` → `deploy`), so "frozen
  pending Max's audit" and "work on main" conflict for any re-score. Freezing wins: an
  unaudited truth-moving number going live is a publishing act, which is owner-class.
- **Why it follows from precedent rather than needing a ruling:** the v0.6.1 arc shipped live
  *then* took Max's five fixes — the audit is the gate on "done", and this keeps it the gate
  on "public" too, at the cost of one merge. Flagged for Max's after-the-fact review.
- **Scope:** re-runs that move a published number. Docs-only and copy-only changes stay on main.
- **Do not:** merge the PR before Max's audit, or declare the deploy done before it.

### 2026-11-09: Partner names relabeled at render time in web/ only (owner ruling; lailara-website DECISIONS 2026-11-05). No estimate, artifact, or copy changed. Flagged for Max's next audit.

### 2026-08-21 — Scorecard re-scored with both methods (artifact scorecard/v2). Logged re-run.

- **Decision:** Adding Method 1 re-scores the Scorecard, logged as a re-run per the
  pre-registration rule. The artifact is bumped to **scorecard/v2**: a portfolio
  header per method plus one record per event co-locating both methods' estimates,
  so the front-end toggle and the Method 0 → Method 1 delta are a lookup.
- **Method 0 is unchanged** — the shared-spine refactor was behavior-preserving, so
  the v2 `method0` block reproduces v1's numbers exactly (portfolio ROI 1.132, net
  incremental margin $118,200, 64 of 129 lost money). No before/after error to log:
  no truth was scored, and Method 1 is a *new* method, not an edit to Method 0.
- **Method 1's scorecard figures (blind, v0.3.0):** portfolio ROI **1.041** (vs
  Method 0's 1.132 — less rosy, the comparable baseline captures the concurrent
  trend Method 0 misses), net incremental margin $109,042, 129 estimable (a
  different 129: rescues PRE-0054, drops PRE-0097), 64 lost money. These are the
  numbers the toggle shows; whether either is closer to *truth* is the Accuracy
  view's question, not asserted here.
- **Scope:** `build_scorecard.py`; `tests/test_scorecard.py`; the front-end.
- **Do not:** read the Method 1 vs Method 0 ROI gap as an accuracy result — it is a
  difference between two blind estimates, pending truth scoring.

### 2026-08-17 — Slice 1 ships Method 0, the naive baseline, labeled as such.

- **Decision:** Baseline estimation is on the critical path of **every**
  downstream number, including ROI. Slice 1 uses **Method 0 (pre-period
  average)** explicitly and says so on screen. Comparable-store matching and
  seasonal adjustment arrive as their own later slices. Each method added
  re-scores the Scorecard as a logged re-run.
- **Why:** PLAN justified the ROI Scorecard as the first slice by calling it
  "the shallowest estimator." ROI is incremental profit over spend, and
  incremental units require a baseline — so the hardest statistical problem
  in the project is an input to slice 1, not a later one. Naming Method 0
  makes that honest, and it puts the anti-rigging exhibit first instead of
  last.
- **Deploy gate:** the tool does not go public until **at least two baseline
  methods exist**. A scorecard scored only by the naive method is the
  anti-rigging exhibit without the rigor exhibit.
- **Scope:** PLAN sequencing; every published figure.
- **Do not:** present a Method 0 number without the label. Do not change an
  estimator after first scoring without a DECISIONS entry recording
  before/after.

### 2026-08-17 — Truth flows one way. Nothing may import the accuracy module.

- **Decision:** The accuracy module is a **sink, never a source**. No module
  outside it may import it, directly or transitively. Enforced by a test of
  the dependency direction, not by convention.
- **The hole this closes:** `assert_no_truth_access` parses each file's AST
  for forbidden imports. The accuracy module is exempted **by name**, so it is
  unaudited — deliberately. But an estimation module that imports the accuracy
  module gains runtime access to truth while its *own* AST contains no
  forbidden import. The gate passes and the estimator is no longer blind.
  Whether the package's gate does transitive analysis is **unverified** —
  worth checking upstream. The test is cheap either way, and this is the
  project's central claim.
- **Scope:** all estimation code; the CI gate.
- **Do not:** rely on the AST gate alone for blindness. It protects against
  direct imports of `truth`. It does not protect against reaching truth
  through a module that is allowed to have it.

### 2026-08-19 — §2.4 giveaway share is a volume ratio, not retail-giveaway ÷ accrued-cost. Pre-freeze correction.

- **Decision:** `subsidized_cost_share(E) = Σ baseline_units / Σ observed_units`
  over **complied** promoted rows — the fraction of the volume sold on discount
  that would have sold anyway at baseline. Replaces the frozen §2.4 formula
  `Σ(baseline_units × (regular − promoted)) / accrued_cost`.
- **Why:** the original formula divided a **retail** giveaway (retail-discount
  dollars) by a **manufacturer** figure (`accrued_cost` is only 0.55–0.69× the
  retail discount, and that ratio is stable only for scan_based — billback and
  off_invoice range 0.24–1.75×). Mixed dimensions produced "shares" up to **936%**
  (`clean_winner`). Because discount depth is constant within an event, the
  discount cancels and the honest metric collapses to a plain volume ratio.
- **The equivalence that keeps the CEO copy usable:** for **scan-funded** events
  `accrued_cost = rate × promoted units`, so `baseline_units ÷ promoted_units`
  equals `baseline_dollars ÷ accrued_dollars` identically — there *"X% of trade
  dollars subsidized volume you'd have sold anyway"* is dimensionally true. For
  **fixed-funded** events the fund is not per-unit, so only the volume phrasing
  is honest; the universal on-screen stat is worded in volume.
- **Net-dip annotation:** a share `> 1` means the naive baseline sat above the
  promoted volume (a dip / pull-forward artifact), carried as the flag
  `baseline_exceeds_promoted` rather than shown as a >100% subsidy.
- **Why this is a correction, not a re-run:** caught by the dimension/schema check
  **before any truth was loaded or any accuracy scored** — the pre-registration
  ordering held. The §7 re-run discipline (before/after error, logged) applies to
  changes *after first scoring*; this is a pre-freeze fix. That the mixed-dimension
  bug's most absurd number (936%) landed on the story with the smallest subsidy
  base is confirmation the check caught a real defect, not cosmetics.
- **Scope:** `docs/estimators.md` §2.4; `method0.py`; the Scorecard artifact.
- **Do not:** divide a retail-dollar quantity by `accrued_cost`. Do not present
  the volume share as a dollar share for fixed-funded events.

### 2026-08-19 — Two §2.4-adjacent spec gaps resolved pre-freeze: event estimability and zero accrued cost.

- **Event estimability:** an event is estimable iff **≥1** of its store-events has
  a sufficient pre-period (store-events drop individually; an event is "not
  estimable" only with zero sufficient store-events). Exactly 2 of 131 events
  (`PRE-0048`, `PRE-0054`, both 2023-01-28, three weeks into the series) are not
  estimable → `N_estimable = 129`. The alternative reading (an event is estimable
  only if *all* its store-events are sufficient) was rejected: a single new store
  would knock out an entire event, contradicting the per-store-event exclusion
  language in §2.2.
- **Zero accrued cost:** 3 events accrued `$0.00` (2 phantom, 1 executed).
  `event_ROI = net/cost` is **null** there (division by zero has no honest numeric
  answer — not a sentinel, not a clamp); `event_lost_money` uses `net < cost` and
  stays defined. `portfolio_ROI` divides by the positive sum of estimable costs
  and is always defined.
- **Why logged:** both are gaps in the frozen spec surfaced during implementation.
  Recorded so the resolution is a decision, not a silent choice, per the
  pre-registration discipline.
- **Scope:** `docs/estimators.md` §2.2 and §2.6; `method0.py`.
- **Do not:** filter the two non-estimable events out silently, or emit a numeric
  ROI for a zero-cost event.

---

### 2026-08-19 — Upstream defects are fixed upstream, with their own regression test. No downstream paper-over.

- **Decision:** When a consumer-side gate catches a defect that lives in the
  data package, the fix goes **in the package**, ships as a new pinned version,
  and carries **its own regression test**. The consumer never swallows the
  error, ships a warm-cache workaround, or adapts its gate to tolerate the bug.
- **Why:** The pattern held four-for-four this cycle and before it — the
  FIGURES.md cold-cache crash (v0.1.1), the pandas-eager-import gate break
  (v0.2.1), and, in sibling repos, brand fonts missing from `package-data`. Each
  time a downstream guard surfaced an upstream packaging gap. A downstream
  paper-over (swallowed exception, tolerated import, shipped cache) hides the
  defect for the *next* consumer and rots the guard that caught it. Fixing
  upstream with a regression test means the class cannot recur silently.
- **The general rule it generalizes:** every file a package reads at runtime
  must be present in the built artifact, asserted against the **wheel**, not the
  source tree. Both v0.1.1 (FIGURES.md) and the brand-fonts bug were this exact
  class; both were invisible to a test run from a checkout.
- **Scope:** the consumer↔package boundary; any shared-dependency defect.
- **Do not:** swallow a data-package exception, ship a warm cache to dodge a
  cold-cache bug, or weaken a downstream gate to accommodate an upstream defect.
  Fix the source and add the test that proves it stays fixed.

## Positioning & Claims

Added 2026-08-17 during `/office-hours`. These entries govern what this
tool is allowed to claim and how the claim is worded.

### 2026-08-21 — The better baseline makes the book look worse. Note for the case study.

- **Observation:** Method 0 (naive pre-period) puts portfolio ROI at **1.13×**;
  Method 1 (comparable-store) puts it at **1.04×**. The stricter, more defensible
  baseline makes the promo book look *worse*, not better — because the comparable
  method catches the concurrent seasonal/market trend the naive pre-period average
  credits to the promo.
- **Why it is the thesis proving itself, unprompted:** every improvement in the
  baseline pulls measured incrementality down. That is exactly what a skeptical CFO
  suspects about their trade spend and exactly what no vendor will show — a vendor's
  incentive runs the other way. The tool demonstrates the direction of the bias, on
  data where the truth is knowable, without being asked to.
- **Where it goes:** the case study on `lailarallc.com/work` (external to this repo),
  and it informs the accuracy view's copy — "the naive method visibly losing" is the
  anti-rigging exhibit, and this ROI gap is its portfolio-level headline. Not an
  accuracy *result* yet (that needs truth scoring); it is a difference between two
  blind estimates, and the accuracy view says which direction is right.
- **Scope:** case study; accuracy view copy; positioning.

### 2026-08-17 — Synthetic data is the only publishable option, not a fallback.

- **Decision:** Frame synthetic data as a strength, not an apology. Inherit
  the fleet disclosure verbatim: *"Data is synthetic; methodology and
  deliverables are real."*
- **Why:** Client promo data can never be shown publicly — by any consultant
  or vendor, at any client count. Synthetic is simultaneously the only world
  where truth is **knowable** and the only world that can be **published**.
  The two constraints coincide, which is what makes the accuracy view
  possible at all.
- **The competitive line, which belongs in the accuracy view's copy:**
  anyone claiming to demonstrate accuracy on real client data is either
  breaching confidentiality or making it up.
- **Scope:** README, accuracy view copy, any case study.
- **Do not:** hedge or apologize for synthetic data. Do not bury the
  disclosure.

### 2026-08-17 — External validity: what the accuracy number is allowed to claim.

The objection this answers: *you built the world and you built the
estimator.* The AST gate is airtight against machine leakage and porous
against human leakage — no gate catches the author knowing the shape of her
own generator. Three defenses, at different strengths, against two different
attacks.

**(a) True today — the world is literature-grounded, not invented.** Every
generator coefficient carries CITE/DIRECTION/JUDGMENT; the dip schedule sits
in vHLW00's published band; the loss rate calibrates to Nielsen's US 71%; a
plausibility audit gates the release. **Cite the package for this, never
this repo.**

**(b) True by commitment — enforced structurally, since nothing automated
catches human leakage.**

1. **Estimators are textbook / vendor-standard methods only** — pre-period
   average, comparable-store matching, seasonal adjustment — each cited to
   methodology literature that **predates the generator**. No method may be
   justified by reference to how the generator works. *This is the defense
   against design-time leakage.*
2. **Pre-registration in git.** The estimator spec and implementation are
   committed and tagged **before** any code in this repo loads truth. The
   accuracy slice comes later in PLAN. Estimator changes after first scoring
   are re-runs, logged here with before/after — never silent. Git history is
   the blindness evidence. *This is the defense against post-hoc tuning. It
   does not cover design-time leakage — the generator predates this repo, so
   ordering here cannot speak to it. (b)(1) covers that. State them as
   covering different attacks; they are not redundant.*
3. **Ship the naive estimator alongside the good ones.** If the exercise
   were rigged, naive wouldn't lose. Its worse error is the anti-rigging
   exhibit — same logic as forecast value-add.

**(c) True by reporting rule.** Headline error is the **full event
population**. The four seeded stories — `pantry_trap`, `hero_cannibal`,
`pure_subsidy`, `clean_winner` — are marked and reported separately, never
as the headline. The mediocre middle is the honest denominator.

**Claim language, exactly:**

- *"Provably blind"* applies to **the code** — AST gate plus the `config`
  ban. It is precise there and overclaims if stretched further.
- The **method-level** claim is: *"this is the error a standard method makes
  under a realistic, fully-known world — measured, by regime, including
  where it is large."*

- **Scope:** global; every published accuracy figure and all surrounding copy.
- **Do not:** claim or imply that measured error on Cinderhaven predicts
  error on a client's data. That is a different claim and this tool does not
  support it.

---

### 2026-08-24 — Re-pinned upstream to v0.4.0 (`6399990`). Logged re-run: economics move, accuracy does not.

- **Decision:** pin `cinderhaven-promo-response` at commit
  `6399990fdc4fabb2b21c1c5e84db29b610e7731f` (tag v0.4.0, peeled) and re-score
  all four artifacts. Upstream re-derived the trade rate: it is now drawn per
  event as a negotiated allowance against wholesale instead of
  `msrp * depth * DISCOUNT_ABSORPTION * coefficient`, which billed an event more
  for being deeply discounted (upstream corr(depth, cost per unit) 0.784 → 0.177).

- **What moved.** Portfolio spend $104,425.13 → **$80,448.79** (M0) and
  $104,734.12 → **$80,849.74** (M1). Return on trade spend 1.13× → **1.47×** (M0),
  1.04× → **1.35×** (M1). Lost-money count 64 → **45** of 129 (M0), 64 → **48**
  (M1). Every story ROI moved; `pure_subsidy` flipped `lost_money` **True → False**
  on both methods (M0 0.55× → 1.03×, M1 0.93× → 1.74×), and `clean_winner` fell
  (M0 4.27× → 1.99×) because its coupon rate rose under the new band.

- **What did not move, verified rather than asserted.** The v0.3.0 artifacts were
  snapshotted before installing and diffed after: `accuracy.json` differs in
  **exactly one leaf**, the `package_version` stamp. Every error and bias number
  is byte-identical. `net_incremental_margin_cents` is unchanged in the scorecard
  too, and every `subsidized_cost_share` is unchanged — giveaway share is a volume
  ratio and is independent of cost. Upstream's guarantee (`promo_scan_delta` and
  `promo_scan_truth` bit-identical, asserted by its own test) therefore holds at
  this repo's own artifact level. **No re-scoring of accuracy was required and
  none was done.**

- **Scope:** `pyproject.toml`, `tests/test_data_contract.py`, all four artifacts,
  and the copy amendments below.

- **Do not:** re-score or re-pre-register the Accuracy view on a cost-only
  upstream release. Trade cost feeds no demand term; treating it as if it did
  would invite a re-run that manufactures the appearance of a changed result.

### 2026-08-24 — No portfolio trade-spend-to-revenue ratio on any published surface, enforced by a test.

**SUPERSEDED 2026-08-27** — lifted by the v0.6.1 two-epoch re-run (its own lapse condition, the v0.5.0 calendar-density fix, is met). The test is removed; trade spend is now ~2.3% of total revenue and ~7.7% of promoted revenue, both quotable. Original entry kept below for the history.

- **Decision:** the tool carries no trade-spend-as-percentage-of-revenue claim.
  Upstream pins spend ÷ total revenue at **0.0693%** as a locked figure explicitly
  marked *not a gate*, and spend ÷ promoted revenue at **6.7148%** as the one
  defensible ratio. Neither is quotable here as a headline. Counts and per-event
  economics carry the story until upstream v0.5.0.
- **Why:** only ~1% of the dataset's volume runs on promotion against a real
  brand's 20–40%, so the portfolio total is small by construction. No rate inside
  any defensible band closes that gap — at $1.50 on every promoted unit the
  ceiling is 0.18% of revenue.
- **Enforced, not just logged:** `tests/test_no_portfolio_spend_ratio.py` scans
  every `.svelte`/`.js`/`.ts` under `web/src` plus README.md, and is
  demonstrated-to-fail against the exact sentence that shipped in v0.3.0 copy —
  *"sits far below the 11–20%-of-revenue all-in trade figures cited elsewhere."*
  A note in this file would not have caught that; it survived a full copy audit.
  The scan requires spend vocabulary near the percentage, because an earlier draft
  flagged `width: 100%` three lines from the word "sales".
- **Do not:** add an of-revenue comparison to explain why the number is small.
  That framing was the defect. Explain the scope and the density instead.

### 2026-08-24 — `pure_subsidy` is the profitable-but-wasteful exhibit, stated in this tool's own figures.

- **Decision:** annotate `pure_subsidy` as a promotion a vendor scorecard calls a
  winner while roughly half its trade dollars bought volume that was already
  moving. ROI alone hides the waste; giveaway share exposes it.
- **The numbers are this tool's, not upstream's.** Upstream's amendment quotes
  1.43× / 3.17× and $1,569 vs $24 — those are **5-seed means over ground truth**.
  This tool publishes **seed-42 blind estimates**, and they are method-dependent:
  `pure_subsidy` returns **1.03×** (M0) / **1.74×** (M1) against `clean_winner`'s
  **1.99×** / **3.35×**, and wastes **75×** (M0) / **59×** (M1) more trade spend.
  Quoting the upstream figures on this surface would assert numbers this tool's
  own pipeline contradicts.
- **Withdrawn upstream, and withdrawn here:** `pure_subsidy` is no longer
  described as losing money, worst-ROI, or bottom-two. It scores profitable on
  both methods. Upstream withdrew those claims as artifacts of the old cost
  formula; see its SPEC §7 derivation table.
- **Do not:** copy a figure from the upstream repo's prose into this tool's copy.
  Every number on a published surface is artifact-fed or it does not ship.

### 2026-08-24 — The 2026-08-23 trade-spend scoping decision was superseded, and both its predictions were wrong.

- The entry below (*"Trade spend is the promo-event slice"*) predicted that
  deriving `promo_cost` from per-unit rates would produce a **$1–2M** promo book
  and push the lost-money count **up** toward the 71% anchor. Actual: **$80,448.79**
  and the count **fell**, 64 → 45 of 129.
- **Why it was wrong:** the premise was that per-unit rates were too low. They were
  already about right — upstream measured the pre-existing scan rate at a median
  $0.76/unit, 19.1% of wholesale, inside the very band the entry proposed. The
  shortfall is **promoted volume**, not rate.
- **Consequence:** the *"roughly $1.5M of trade, roughly half wasted"* headline
  that entry was written to enable is unreachable by any cost change and is
  withdrawn. The interim scoping line survives but with its cause corrected — it
  blamed instrument scope (slotting, allowances, deductions) when the dominant
  cause is calendar density, by roughly 30–45x.
- **Do not:** treat the superseded entry as live guidance. It is kept for the
  reasoning trail, not the plan.

## Data & Schema

### 2026-08-17 — Pin the upstream package version.

- **Why:** An accuracy number is meaningless without knowing which data
  generation it scored against. The package is seed-locked, so a version
  bump that changes generation changes every reported error.
- **Scope:** dependency manifest; any published accuracy figure.
- **Do not:** report an accuracy number without recording the
  `cinderhaven-promo-response` version and seed alongside it.

### 2026-08-18 — The upstream package is pinned by commit SHA in the manifest. Never an editable local path.

- **Decision:** `pyproject.toml` declares the dependency as a git URL pinned to
  the **full 40-character commit SHA** of the release:

      cinderhaven-promo-response @ git+https://github.com/MsShawnP/cinderhaven-promo-response@70021d4d472bdf4ab5132778472b4ca8a95fe0e8

  `70021d4` is v0.1.0. The tag name is recorded in a comment for humans; the
  pin is the SHA.
- **Why SHA and not the tag name:** annotated tags are mutable. A tag can be
  moved and the manifest still reads as pinned, which is the worst version of
  a pin — it satisfies review and not reproducibility. The rest of the fleet
  pins SHAs (`0f300ef`, `c4ea09e`); same discipline, same reason.
- **Why the full SHA and not the short form:** a short SHA is a prefix match,
  and prefixes collide as a repo grows.
- **The trap, which cost a wrong pin on 2026-08-18:** `git rev-parse v0.1.0`
  returns the **annotated tag object** (`1d3ec86`), not a commit. Use
  `git rev-parse v0.1.0^{commit}`. The first SHA proposed for this manifest,
  `a237910`, was neither — it was an unrelated ancestor commit dated 75 minutes
  before the release, predating the plausibility audit and the retired-figure
  scan. It resolves, it installs, and every accuracy figure scored against it
  would have been scored against a build that never passed its own release
  gate. **It was caught only because a SHA is checkable**; a tag name would
  have been right by accident and taught nothing.
- **Verification that the pin took effect** — pip records provenance, so this
  is checkable rather than assumed:

      .venv/Lib/site-packages/cinderhaven_promo_response-0.1.0.dist-info/direct_url.json
      → "commit_id": "70021d4d472bdf4ab5132778472b4ca8a95fe0e8"

- **Rejected — editable install from `../cinderhaven-promo-response`.** It
  makes "pinned at v0.1.0" describe a working tree rather than anything CI can
  reproduce, failing the pin decision it appears to satisfy. Local iteration is
  still fine as a **hand-run command** — `pip install -e ../cinderhaven-promo-response` —
  that the manifest never records.
- **Rejected — vendoring a wheel into this repo.** It is a pure-Python package
  that generates its data at first load; a committed binary artifact is just a
  second thing that can drift from the tag.
- **Scope:** the dependency manifest; every published accuracy figure.
- **Do not:** put an editable or local path in the manifest, for any reason,
  including "just while iterating." Do not pin a tag name. Do not pin a short
  SHA. Do not record a SHA without confirming it is the peeled commit of the
  intended tag.

### 2026-08-17 — The portfolio roll-up is a pipeline artifact with a reconciliation test.

- **Decision:** The Scorecard is a portfolio header plus a ranked list. The
  header's three numbers are the CFO answer: **total accrued trade spend,
  portfolio net incremental margin, portfolio ROI** — plus N of 131 events
  that lost money. All of it computed in the pipeline, never in the front end.
- **The test:** the portfolio total must tie to **both** the sum of event
  nets **and** the row-level grain sum. This is the package's reconciliation
  discipline crossing the repo boundary — the same move as the identity
  `observed_units ≡ baseline + lift − dip ± transfer + noise`, applied to
  this tool's own arithmetic.
- **Why it gets an assertion rather than an assumption:** transfer is
  zero-sum, which makes naive summation *look* safe. That is exactly the
  property that hides a double-count or a dropped sign until someone checks.
- **Scope:** pipeline; ROI Scorecard header.
- **Do not:** compute any portfolio figure in the front end. Do not treat
  transfer's zero-sum property as self-evidently safe.

### 2026-08-17 — Money is integer cents. Reconciliation is exact, not tolerant.

- **Decision:** Carry money as **integer cents** through the pipeline,
  quantized once at the row grain with **round-half-even**. The portfolio
  reconciliation asserts **equality**, not approximate equality.
  ~~Units are already integers.~~ **Corrected 2026-08-19:** units are
  *continuous* — see the 2026-08-19 money-grain entry below, which supersedes
  this line. The exactness now rests on the shared row-level atomic integer,
  not on units being whole.
- **Why:** the roll-up ties to a row-level sum over 1,340,462 values. In
  float64, summation order changes the last bits, so the assertion would need
  a tolerance — and a tolerance is a number that only ever gets widened when
  it fails. Integer arithmetic removes the question. This matches the upstream
  package's ethos: the reconciliation identity there is **bit-exact per row**,
  not within epsilon.
- **Scope:** pipeline; every monetary figure and every reconciliation test.
- **Do not:** introduce a float tolerance into a reconciliation assertion. If
  one appears to be necessary, that is a signal the arithmetic is wrong, not
  that the tolerance is too tight.

### 2026-08-19 — Units are continuous; money is integer cents, round-half-even at the row grain.

- **Decision:** `observed_units` is **continuous** — fractional on all 1,340,462
  rows (the upstream noise deviate), range 0.03–396.5. Revenue = units × price is
  therefore inherently fractional-cents. Money is carried as **integer cents**,
  quantized **once at the row grain** with **round-half-even** (banker's). That
  per-row integer is the atomic unit; the event-sum and the row-grain-sum
  aggregate the *same* integers, so the portfolio reconciliation ties **exactly**
  with no float tolerance.
- **Why round-half-even, stated explicitly:** across 1.34M rows, always-round-
  half-up introduces a small systematic upward bias in totals; half-even removes
  it. An unstated rounding mode resurfaces as a one-cent reconciliation mystery
  in an environment with different defaults. Named here, in CLAUDE.md, and pinned
  by a portfolio-total test.
- **What this corrects:** the 2026-08-17 "units are already integers" premise
  (an eng-review assumption) was wrong; the schema check caught it before the
  Method 0 spec froze. Exactness never depended on integer units — it depends on
  the shared row-level atomic integer.
- **Scope:** every monetary figure; every reconciliation test.
- **Do not:** quantize at more than one grain, use half-up, or introduce a float
  tolerance. If a tolerance seems necessary the arithmetic is wrong.

### 2026-08-19 — The portfolio universe is all 131 events; phantom included and marked.

- **Decision:** The ROI Scorecard scores **all 131 events** — 121 `executed`,
  7 `phantom` (planned and funded, ran nowhere), 3 `unplanned` (ran without a
  plan). Phantom and unplanned are **marked** in the artifact, never dropped.
- **Why:** phantom promos accrued $5,277 while producing no real lift — trade-
  spend leakage rendered in ROI form, the clearest loss story the tool exists to
  show. Excluding them would quietly flatter the portfolio number, which is the
  exact sin the tool indicts. Matches CLAUDE.md's "N of 131." Method 0 handles
  them without special-casing: a phantom's promo weeks are `complied=False` with
  no lift, so incremental units ≈ 0 and ROI is deeply negative by construction.
- **Scope:** portfolio roll-up; the ranked event list; the "N lost money" count.
- **Do not:** filter to executed-only for the headline. If a view needs an
  executed-only cut it is an explicit, labeled secondary view, not the default.

### 2026-08-17 — Published artifacts carry error metrics, never truth — including in their labels.

- **Decision:** Artifacts written for the front end may contain **error
  metrics derived from truth**. They may never contain **truth values**. The
  accuracy artifact's schema is asserted by a test.
- **Why `.gitignore` does not cover this:** the ignore file correctly excludes
  `.cache/` and `*.parquet`, so the quarantined truth table cannot reach git.
  But the accuracy module *writes* a precomputed artifact — `accuracy.json` or
  similar — into the site's data directory, which is committed or built and
  published by design. Nothing in the ignore file protects it. This repo will
  be public.
- **The subtler channel — regime labels.** Regime definitions in the accuracy
  artifact must be built from **observed features only**: promo type, depth,
  duration, season, product line, calendar position. Truth-derived regime
  labels — actual compliance draw, actual dip magnitude, actual transfer —
  leak generator structure **even with every truth value aggregated away**.
  "Error by actual-compliance band" reveals per-event compliance by
  inspection. If a truth-derived cut is analytically necessary, it aggregates
  to **≥N events per bucket** and is labeled truth-derived in the artifact
  schema. Default is observed-features-only.
- **The general form, worth carrying:** the gate protects **values**;
  structure can walk out through **labels**. Same class of hole as the
  transitive-import entry above — the named defense is narrower than the thing
  it is defending.
- **Scope:** every artifact written for the front end.
- **Do not:** cut error by any truth-derived feature without the aggregation
  floor and the schema label.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices. The Lailara
design system at `~/projects/reference/lailara-design-system/LAILARA_DESIGN_SYSTEM.md`
governs colors, typography and chart rules; entries here record only
project-specific choices on top of it.]

### 2026-08-17 — Mobile responsibility splits by surface, not by view.

- **Decision:** The **30-second surface** — the Scorecard header: verdict
  line, one chart, three numbers — is **phone-first** and must fully work at
  375px. The **exploration surfaces** — ranked-list interactions, Event
  Anatomy, Accuracy — are **desktop-first**: readable and functional on
  mobile, but comparison mode and dense waterfall interactions may degrade
  gracefully with a "best on desktop" note.
- **Why:** Distribution is a link from `lailarallc.com/work`, and links get
  opened on phones. The first impression is therefore a phone impression, and
  a 30-second verdict that only works at 1440px fails its own brief. The
  exploration surfaces are consumed differently — nobody runs a comparison
  across 131 events on a phone.
- **What this buys:** the responsive work is bounded to **one** genuinely
  responsive component instead of three. The global deployed-UI gate still
  requires checking every surface at 1440px and 375px; this decision sets
  what "passing" means at 375px for each.
- **Scope:** all three views; the deployed-UI gate.
- **Do not:** treat "responsive" as a uniform requirement across surfaces, and
  do not let the Scorecard header inherit the exploration surfaces' mobile
  allowances. It is the one component with no degradation budget.

### 2026-08-22 — Frozen prose never quotes a number that toggles.

- **Decision:** Any static on-screen text (story annotations, captions, framing
  paragraphs) must read true under **every** interactive state — method toggle,
  filter, method-dependent stat. Where a design fact wants a number, either the
  number is invariant across states, or the prose describes the intent qualitatively
  and points at the live figure ("the giveaway figure above is what the selected
  method estimates").
- **Why:** the anatomy story annotations quoted `subsidized_cost_share`, which
  toggles M0↔M1 (e.g. 63% vs 40% for the same event) and clashed with the fixed
  wording ("most" beside "40%"). Frozen prose plus a toggling number is a guaranteed
  contradiction on screen — the copy audit caught it. Prose that reads its numbers
  from the artifact can't drift; prose that hard-codes them lies the moment the state
  changes.
- **Scope:** all view copy; every page with a toggle or filter.
- **Do not:** interpolate a method-dependent (or filter-dependent) figure into text
  that is meant to be a fixed statement. Verify each annotation under both toggles.

### 2026-08-22 — On a prerendered page, the query string is client-only state; path carries server-rendered state.

- **Decision:** With `adapter-static` (`prerender = true`), a component must **not**
  read `url.searchParams` / `url.search` server-side — SvelteKit throws at build. Read
  the query in `onMount` (client) only, default to the unfiltered state in the
  prerendered HTML, and write back with `replaceState`. State that must render
  server-side goes in the **route path**, not the query.
- **Why:** the prerendered HTML is one static file served for every query, so it
  cannot depend on the query. This is why per-event pages are `/event/[promo_id]`
  (path — prerenderable via `entries()`) while cross-view filters and the active
  method are query params (client-only). See FAILURES.md 2026-08-22.
- **Scope:** all prerendered routes; any cross-view URL state.
- **Do not:** access `$page.url.searchParams` in a component on a prerendered route.
  Do not put prerender-visible content behind a query param.

### 2026-08-23 — Trade spend is the promo-event slice, not all-in trade; realistic scaling is an upstream release.

- **Decision:** The Scorecard's "Trade spend" is the **scan-promoted event slice** of
  the trade book — accrued cost on promo events only. It excludes slotting, off-invoice
  allowances, and deductions, so it sits far below the 11–20%-of-revenue all-in trade
  figures cited in industry sources. A scoping line on the Scorecard now says so.
- **Follow-up — upstream v0.4.0, before public launch (decided 2026-08-23):** the
  scoping line explains the small number; it does not fix that the flagship's headline
  stake is ~$100K on a ~$40M brand — a figure a CEO shrugs at. The real fix is a data
  package release: derive `promo_cost` from **realistic per-unit trade rates** (order
  $0.50–$1.50/unit scan-backs, drawn by funding mechanism) instead of the original
  $200–$5K flat draw. Against these same volumes that puts the two-year promo book
  around **$1–2M**, and the demo reads "≈$1.5M of trade, roughly half wasted" — a number
  that books a call.
- **Scope of the upstream release (a `cinderhaven-promo-response` session, NOT this repo):**
  per-unit rate draws by funding mechanism; **recalibrate plausibility criterion 6
  against the 71%-don't-break-even anchor** (realistic rates should land near it
  naturally — a synergy, since higher costs push more events below break-even toward the
  NIQ anchor CLAUDE.md already cites); canonical-figure updates; tag v0.4.0. Then here:
  re-pin (logged re-run) and **re-score every artifact** — Scorecard, Anatomy, Accuracy.
- **What the re-run does and doesn't move:** `promo_cost` is observed accrued cost, not a
  demand-response parameter, so **unit truth is unchanged** — the Accuracy view's unit
  error (≈26% median, the biases) does not move. Only the economics rescale: ROI,
  net-margin-vs-spend, scan-funded giveaway base, and the lost-money count (which rises
  toward ~71%). No estimator change, no new pre-registration, blindness ledger untouched.
  A clean logged re-run with before/after in this file.
- **Sequencing (important):** the re-score must land **before** the final copy audit and
  before public launch — every headline number changes, so auditing copy first means
  auditing it twice. The interim scoping line ships now; it is superseded by the v0.4.0
  numbers, not additive to them.
- **Open caveat:** the $0.50–$1.50/unit range is a modeling assumption. The upstream
  release must **cite it** (trade-rate source), per the package's plausibility
  discipline — not assert it.
- **Do not:** rescale `promo_cost` / accrued cost in THIS repo to "look realistic."
  The fix is upstream; here it is only ever a re-pin + logged re-run.

### 2026-08-24 — Every stat shown on two views is one value in the artifact; rounding lives at the display layer only.

- **Decision:** A figure the front end renders on more than one surface (roi,
  giveaway share, margin, cost — Scorecard *and* Anatomy) is carried at **full
  precision** in the artifacts and rounded **once**, at display time, by the shared
  `format.js` helpers. An artifact writer must not pre-round a cross-view stat. Any
  intentional artifact-level rounding (the anatomy waterfall bars, where net is
  derived from the rounded pair to reconcile on screen) uses a **separate** converter
  (`_units`) and applies only to fields with no second surface.
- **Why:** the two views read the same value through the same formatters; if one
  artifact pre-rounds and another doesn't, the same event renders different numbers on
  different pages — fatal for a tool whose entire thesis is measuring when two numbers
  that should agree don't. See FAILURES.md 2026-08-24.
- **Scope:** every artifact writer (`build_scorecard`, `build_anatomy`, any future
  one) and every stat with more than one render site.
- **Enforcement:** `tests/test_cross_view_consistency.py` — every event × method ×
  shared-stat, anatomy value ≡ scorecard emitted value, exact; the stat set is derived
  live from the artifacts so a newly shared field is checked automatically.
- **Do not:** round a cross-view stat inside an artifact writer. Do not compare
  estimator outputs to prove consistency — compare the **emitted artifact values**,
  the only thing that catches converter drift.

### 2026-08-26 - Consume the Lailara frame via tagged re-vendor; table alignment is tool-local.

- **Decision:** Lift Math vendors `lailara-frame.css` + fonts **from a git tag** of
  the `lailara-frame` repo (v1.5.0), byte-for-byte - never hand-edited in place.
  Measure adopts the canonical `.ll-column` wrapper + `--ll-content-measure` (720px)
  so a heading and its lede share one right edge. Table-header alignment is
  **tool-local** (`col-num` / `col-rank` / `col-promo` here): the frame ships no
  table utility classes, so each tool owns its own alignment (numeric right, text
  left, no centered headers).
- **Why:** an earlier pass added ad-hoc `.ll-num` / `.ll-text` to the vendored frame
  and a local `--content-measure` alias. That is drift - the vendored file no longer
  matched any release. The fix for drift is to make the edit official upstream (frame
  v1.5.0) and re-vendor against the tag, not to keep local edits. Sourcing from the
  tag (never a working tree) means the vendored copy is provably a release.
- **Scope:** `web/static/lailara/` and every page's measure/table CSS.
- **Do not:** hand-edit the vendored frame CSS, alias `--content-measure` locally, or
  invent `.ll-num`/`.ll-text`-style frame table classes. If the frame needs a change,
  ship it upstream, tag it, and re-vendor. See the lailara-frame repo's
  MEASURE_TABLE_RETROFIT.md.

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
