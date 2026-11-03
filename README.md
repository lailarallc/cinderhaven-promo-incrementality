# Lift Math

**Live:** https://liftmath.lailarallc.com

Most trade-promotion tools report incremental lift and ask you to trust the
number. There is no way to check: the counterfactual — what would have sold
without the promotion — is unobservable in real scan data. This tool runs on
a dataset where the counterfactual is known and quarantined, so every estimate
it produces is scored against the truth it was blind to.

Three linked views on one promo-event spine. **ROI Scorecard** is the
verdict — portfolio spend, net incremental margin, ROI, and how many of 5,735
estimable promotions lost money. **Event Anatomy** is the explanation — the full
decomposition of any single event, gross promoted through subsidized baseline
to net incremental. **Accuracy** is the proof — how wrong the estimator
actually was, by regime, including where the error is large.

Measured error describes this estimator under a realistic, fully-known
world. It is not a prediction of error on any other dataset.

**Status:** launched. Three views built, audited and deployed; upstream data
package pinned at v0.6.2. The repository keeps its original name,
`cinderhaven-promo-incrementality`; **Lift Math** is the tool's public name.

Roadmap: upstream v0.5.0 calendar density — raising promoted volume from ~1%
to about a third of the book, which moved unit truth and forced a full
re-validation — is done, shipped and re-scored in v0.6.1. Next: observed-only
dip and transfer estimators, which add the waterfall's fourth and fifth bars.
See PLAN.md.

## Cinderhaven context

Built on the Cinderhaven synthetic dataset — a ~$25M specialty food brand,
50 SKUs across 5 product lines and 6 contracted retailers. Data is synthetic;
methodology and deliverables are real.

The promo signal comes from `cinderhaven-promo-response` v0.6.2, an additive,
seed-locked overlay: a curated promo-event calendar, a promo-responsive scan
series, and a quarantined ground-truth table. It never alters canonical.

## What it does

<!-- Filled in as views ship. Do not write claims here ahead of the code. -->

- **ROI Scorecard** — portfolio spend, net incremental margin, return on trade
  spend, and how many promotions did not pay back, under two baseline methods.
- **Event Anatomy** — a deep-linkable page per event with a three-bar volume
  decomposition: gross promoted, subsidized baseline, net incremental.
- **Accuracy** — the estimator's own error against quarantined ground truth,
  by regime, including where the error is large.

Figures in the views are rendered from artifacts the pipeline computes; no number
the tool displays is hand-entered.

## Stack

- **Python** estimation engine, computing at build time —
  `cinderhaven_promo_response.testing.assert_no_truth_access` parses source
  with `ast` and can only audit `.py` files, so estimation code in another
  language would make the blindness claim unenforceable.
- **`cinderhaven-promo-response` v0.6.2** (`820e1935`), pinned by commit SHA, consumed
  through its public API only.
- **SvelteKit + D3**, static via `adapter-static`, on **Cloudflare Pages**.

The pipeline writes small precomputed artifacts; the 1,340,462 scan rows
never reach the browser. There is no server and no client-side query layer.
Observable Framework and Dash were considered and rejected — reasoning in
DECISIONS.md.

## Data contract

**Canonical baseline:** 50 SKUs · 5 product lines (AS·PS·SC·DG·SB) · 6 retailers
(Walmart·Costco·Whole Foods·Sprouts·Kroger·Regional Group) · 10 channels
(6 retail + UNFI·KeHE·DPI + DTC)

This tool reads the promo-response overlay and adds no data of its own. It
never regenerates, modifies, or reads the SSOT scan table.

Observed layer, via `pr.load()`:

- `promo_events` — 5,897 rows
- `promo_scan_delta` — 1,340,462 rows × 8 observed columns

Ground truth reaches one module only — the accuracy view — through
`truth.load_truth()`, guarded by `truth.assert_aligned_with_observed()`.
`assert_no_truth_access` runs in CI over every other estimation module. It is
the package's own gate, imported rather than re-implemented, so the same rule
is enforced on both sides of the boundary.

## Run

Two halves: a Python engine that computes artifacts, and a SvelteKit front end
that renders them as a fully static site.

**Python engine:**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
# .venv/bin/pip install -e ".[dev]"               # macOS / Linux
```

The upstream data package is a private repo pinned by commit SHA, so the
install needs read access to it. In CI that is the `PROMO_RESPONSE_READ`
secret; locally, whatever credentials git already has.

**Front end** (Node 20+; the build imports an artifact the engine writes):

```bash
npm --prefix web ci
```

**Build the static site — one command, engine first:**

```bash
bash scripts/build.sh          # runs the pipeline, then the static build
```

`scripts/build.sh` runs the Python pipeline before the SvelteKit build, because
the front end imports `web/src/lib/data/skeleton.json`, which the pipeline
writes and which is never committed. If the pipeline fails, the build aborts —
no stale artifact ships. Output lands in `web/build/`.

**Tests — one command, nothing skipped:**

```bash
.venv/Scripts/python -m pytest
```

`tests/test_data_contract.py` calls `pr.load()` (~8.5s cold, ~0.6s warm) and
asserts the consumer contract against the pinned upstream version. It has passed
cold since v0.1.1 fixed the v0.1.0 first-call crash (see FAILURES.md); the pin has
since moved to v0.6.2. The truth gate is pure AST parsing over `src/` and needs no
data.

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics
consulting for specialty food brands scaling into national retail.
