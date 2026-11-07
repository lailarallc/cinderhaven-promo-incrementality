# Accuracy scoring specification — pre-registration

**This document is committed and tagged (`accuracy-preregistration`) before any
scoring runs — before `accuracy.py` exists, before a single call to
`truth.load_truth()`.** Metric-shopping after seeing results is the same sin as
tuning an estimator after seeing truth: both let the answer choose the question.
Pre-registering the metrics closes it. The git history is the evidence — this file,
and both estimator tags (`method1-preregistration`, `method1-preregistration-r2`),
predate the repo's first truth access.

The estimators are frozen. Nothing below changes them; if a metric here proved
impossible to compute, that is a finding to log, not a licence to touch an
estimator.

---

## 1. The single contact with truth

`src/incrementality/accuracy.py` is the **one** module allowed to import
`cinderhaven_promo_response.truth`. It is exempt from the CI truth gate **by name**
(`tests/test_truth_gate.py`), and by name only. Its **first action** before any
scoring is:

    truth.assert_aligned_with_observed(delta)

— the guard against scoring observed rows from one generation against truth from
another, the one completely silent failure in this pipeline. Nothing else in the
repo imports `truth`, and nothing imports `accuracy` (the dependency-direction guard,
which now earns its keep). `accuracy.py` writes its own artifact from its own
`main()`; no other module reaches through it to truth.

## 2. The estimand — net incremental units, on the rows the method scored

The quantity scored is **net incremental units** per event, for **each method
separately**, and scored **only over the store-weeks that method actually estimated**
— so error measures *estimation accuracy*, not *coverage* (the two methods estimate
slightly different row sets; comparing each to truth on its own rows is the fair test;
coverage is reported separately as `n_estimable`).

For method `M` and event `E`, over `M`'s estimable rows `R(M, E)`:

    est_incremental(M, E)  = sum over r in R(M,E) of ( observed_units(r) - baseline_units_M(r) )
    true_incremental(M, E) = sum over r in R(M,E) of ( causal incremental units(r) )

`causal incremental units(r)` is the generator's **causal** effect of the promotion
in the reconciliation identity `observed = baseline + lift - dip ± transfer + noise`
— i.e. `lift - dip ± transfer`, **excluding noise** (noise is not caused by the
promotion). The exact column arithmetic against `truth.load_truth()` is recorded in
`accuracy.py`; it does not change this definition.

## 3. The metrics — frozen here

Per event, per method:

    signed_pct_error(M, E) = 100 × ( est_incremental(M,E) − true_incremental(M,E) )
                                   / true_incremental(M,E)

**Headline (per method), over the full estimable population — not the stories:**

- **Median absolute percentage error** — `median( |signed_pct_error| )`. The
  mediocre middle is the honest denominator.
- **Median signed percentage error** — the **bias**, i.e. which direction the method
  is wrong. A method that systematically over-credits promotions has a positive bias;
  that is the finding a CFO cares about.

Both methods are reported **side by side, everywhere**. Method 0 (naive) appearing
beside Method 1 — and, where it does, visibly losing — is the anti-rigging exhibit.
No method is shown alone.

## 4. Zero-denominator rule (metric domain, disclosed — not a truth cut)

A percentage of near-zero is meaningless. Events whose `|true_incremental(M,E)|` is
below a fixed floor of **1.0 unit** are **excluded from the percentage headline** and
reported **separately with absolute unit error** (`est_incremental − true_incremental`).
This is a rule about where a percentage is *defined*, fixed in advance, **not tuned to
results** and **not a truth-derived regime cut**. Phantom events (identifiable by the
**observed** `plan_status`) have ~0 true incremental by construction and fall here.

## 5. The seeded stories — marked, separated, never the headline

`pantry_trap`, `hero_cannibal`, `pure_subsidy`, `clean_winner` are the four events the
tool is *supposed* to surface. They are **marked and reported separately**, never
folded into the headline median. Finding them is not a result on its own — they are
outliers shown **against the full-population background**, which is the honest
denominator. Whether Method 1 recovers a story that Method 0 misses is shown per
story, per method, with both errors visible.

## 6. Regime cuts — observed features only

Error is cut by regime for display. **Every regime label is built from OBSERVED
features only:**

- `promo_type`, discount-**depth band**, **duration** band, **season**, **product
  line**, **retailer**, and — Method 1 only — **`match_relaxed_share`** band (an
  observed attribute of the match, §3.3).

**No truth-derived regime labels.** "Error by actual-compliance band" reveals
per-event compliance by inspection; "error by actual-dip magnitude" leaks the
generator. The gate protects *values*; structure must not walk out through *labels*.
If a truth-derived cut ever becomes genuinely necessary, it aggregates to **≥5 events
per bucket** AND is **labeled `truth_derived` in the artifact schema**. The default,
and the whole of this view's first pass, is observed-only.

**Every bucket carries ≥5 events.** Smaller buckets are merged or suppressed, so no
bucket's error can be read back to an individual event.

## 7. The artifact — error metrics only, never truth

The accuracy artifact carries **error metrics derived from truth**. It **never**
carries:

- a truth **value** (a true baseline, lift, dip, transfer, compliance, or unit count),
- **per-row** truth of any kind,
- anything from which a truth value is **reconstructable** (e.g. both an estimate and
  its exact error at a grain fine enough to invert to the truth).

Only aggregated error statistics, per method, per regime bucket (≥5 events), plus the
per-story lines. **The schema is asserted by a test** — this repo will be public, and
`.gitignore` does not protect an artifact written into the site's data directory by
design.

## 8. Claim language — verbatim from the external-validity decision

- **"Provably blind" is scoped to the CODE** — the AST truth gate, the
  `config`/`constants` import ban, and the git history in which both estimators are
  spec-tagged *and* implemented-and-frozen before this file loads truth. It is precise
  there and overclaims if stretched further.
- **The method-level claim, exactly:** *"this is the error a standard method makes
  under a realistic, fully-known world — measured, by regime, including where it is
  large."* It is **not** a claim that measured error on Cinderhaven predicts error on
  a client's data.
- **Synthetic is the only honest testbed:** it is simultaneously the only world where
  truth is *knowable* and the only world that can be *published*. The two constraints
  coincide, which is what makes this view possible at all. **Anyone claiming to
  demonstrate accuracy on real client data is either breaching confidentiality or
  making it up.**
- **Large error is the product.** Where a method is very wrong, the view **displays**
  it — by regime, at full size. Softening it would be the competitor's move.

## 9. The view

One click from the Scorecard — the proof behind the numbers, not a front door. It
carries the claim language above verbatim. Method 0 sits beside Method 1 in every
figure. The four stories are a marked, separate panel over the background
distribution. The naive method losing is the exhibit.

## 10. Determinism, guards, change control

- Same package version + seed + code → identical error numbers. No wall-clock, no
  unseeded value in the scoring path.
- All guards stay green: the truth gate (accuracy exempt by name), the
  `config`/`constants` import ban, and the dependency-direction sink (nothing imports
  `accuracy`).
- These metrics are **frozen at `accuracy-preregistration`**. Any change after first
  scoring is a **logged re-run** in DECISIONS.md with before/after — never a silent
  edit. That is the whole point of tagging this before the scoring runs.

## 11. Amendment — v0.7.0 assortment epoch (pre-registered 2026-11-04, before first v0.7.0 scoring)

Committed and tagged `accuracy-preregistration-v0.7.0` **before** `accuracy.py` runs
against v0.7.0 truth. The v0.7.0 pin was installed and `pr.load()` (observed layer
only) was run to count launches and exits; no code in this repo has read v0.7.0
truth. §§1–10 are unchanged except §2's attribution, made explicit in §11.1. The
estimators are unchanged and stay frozen at their tags.

### 11.1 Row attribution — the stated rule (clarifies §2; no metric changes)

A promoted row belongs to **the event named by its observed `promo_id`**. Its
`causal incremental units(r)` is the full row-level `lift − dip + transfer`, whatever
event caused each term. **`caused_by_promo_id` is never read.** Upstream it is
first-claim and assigned in SKU processing order (upstream plausibility audit
2026-11-04 #9), so a per-event ledger built on it moves when event order moves; a
ledger built on the observed `promo_id` cannot, because it is a function of the
observed layer alone. The row-level unit values themselves accumulate additively
upstream.

- **Precondition, asserted at scoring time:** no two events on the same
  `sku × retailer_id` overlap in time, so every promoted row has exactly one scheduled
  event. A generation that breaks it makes scoring **refuse** — no tie-break rule is
  applied silently. (v0.7.0 seed 42, observed: zero overlapping pairs.)
- **Outside the estimand, as before:** an event's post-event dip on non-promoted weeks
  and its drain on siblings' rows. The estimand is net incremental on the event's own
  promoted rows (§2), the same quantity the estimator's `observed − baseline` measures
  on those rows. Dip and transfer are the next estimation arc.

### 11.2 Item life — observed definitions

From the observed key universe (`promo_scan_delta` rows), per SKU `s`:
`F(s)` = first `week_ending` with a row, `L(s)` = last; `W0`/`W1` = the window's first
and last `week_ending`. `s` is a **launch** iff `F(s) > W0`; it **exits** iff
`L(s) < W1`. Per `(s, retailer)`, `F(s, r)` and `L(s, r)` are the same over that
retailer's stores. Observed scan presence, not a truth label: a real client's scan
data shows exactly this.

### 11.3 Regime `life_stage` (SPEC §4.9.7 predictions 1, 2, 4)

For an event on `s` starting `S`:

| label | rule | upstream prediction |
| --- | --- | --- |
| `exit fade (final 13 weeks)` | `s` exits and `S > L(s) − 13 weeks` | lift biased **low** (pre-period sits above the fading counterfactual) |
| `launch (life weeks 1–13)` | `s` is a launch and `S ≤ F(s) + 12 weeks` | early ones inestimable; those that clear `MIN_PRE_PERIOD_WEEKS` biased **high** (pre-period on the ramp) |
| `launch (after week 13)` | `s` is a launch, otherwise | — |
| `continuing` | everything else | background |

Precedence: fade, then launch window. 13 weeks is upstream's own launch-promo and fade
window (SPEC §4.9.2 A3, §4.9.3 exit shape); chosen for that reason, before scoring.

### 11.4 Regime `sibling_assortment` (SPEC §4.9.7 prediction 3)

For an event on `s` in line `ℓ` at retailer `r`, starting `S`, against every other
SKU `s'` in `ℓ` carried at `r`:

| label | rule | upstream prediction |
| --- | --- | --- |
| `after same-line launch` | some launch `s'` has `S − 13 weeks < F(s', r) ≤ S` | baseline step-down; lift biased **low** |
| `after same-line exit` | some exiting `s'` has `S − 13 weeks ≤ L(s', r) < S` | baseline step-up; lift biased **high** |
| `after both` | both hold | — |
| `none` | neither | background |

Same 13-week window, same reason.

### 11.5 Prediction 4 — launch-promo economics, as this tool estimates them

Per method and `life_stage`: `n_events`, `n_estimable`, and the **estimated** loss
rate (`n_lost_money / n_estimable`). These are estimates and observed counts, not
truth, and are published as such. The prediction itself is about true ROI and is the
data package's to measure (upstream reports 64% vs 61%, launch vs incumbent, seed 42,
on an order-independent ledger). This view shows whether each method's estimate
preserves or hides that ordering, and its signed bias on the same buckets (§11.3)
says in which direction.

### 11.6 Suppression and reporting

§6's ≥5-event rule applies to every bucket. A predicted regime suppressed for size is
**reported as suppressed with its count**, not dropped silently. Each prediction is
scored hit or miss against the sign of the bucket's median signed error. A miss is
reported as a miss.
