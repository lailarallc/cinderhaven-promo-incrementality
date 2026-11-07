"""The accuracy view — the repo's single, by-name-exempt contact with truth.

This is the ONE module allowed to import ``cinderhaven_promo_response.truth``. It is
exempt from the CI truth gate by name (``tests/test_truth_gate.py``) and by name only,
and nothing imports it (the dependency-direction guard). It scores the two frozen,
blind estimators against quarantined ground truth, following the metrics
pre-registered in ``docs/accuracy-spec.md`` and tagged ``accuracy-preregistration``
before this file existed.

What it publishes is **error metrics derived from truth — never truth values, never
per-row truth, nothing reconstructable** (spec accuracy §7). The artifact's schema is
asserted by a test, because this repo is public and ``.gitignore`` does not protect an
artifact written into the site's data directory by design.
"""

import json
from pathlib import Path

import cinderhaven_promo_response as pr
import numpy as np
import pandas as pd
from cinderhaven_promo_response import truth

from incrementality import method0, method1

SCHEMA = "accuracy/v2"  # v2 (2026-11-04): adds the §11 assortment regimes

# A percentage of near-zero is meaningless: events whose |true incremental| is below
# this fixed floor are excluded from the % headline and reported with absolute unit
# error (spec accuracy §4). Fixed in advance, not tuned to results.
FLOOR_UNITS = 1.0

# The four seeded stories: marked and reported separately, never the headline (§5).
STORY_TAGS = ("pantry_trap", "hero_cannibal", "pure_subsidy", "clean_winner")

# Buckets smaller than this are suppressed, so no bucket's error reads back to an
# individual event (spec accuracy §6, §7).
MIN_BUCKET = 5

# Item-life window for the §11 assortment regimes: upstream's own launch-promo and
# exit-fade window (SPEC §4.9.2 A3, §4.9.3). Fixed in accuracy-spec §11 before any
# v0.7.0 scoring — not tuned to results.
LIFE_WINDOW = pd.Timedelta(weeks=13)

# The pre-registered direction of each §4.9.7 prediction, as the sign of the median
# signed error (accuracy-spec §11.3, §11.4). +1 = estimate biased high.
PREDICTIONS = (
    ("life_stage", "launch (life weeks 1–13)", +1),
    ("life_stage", "exit fade (final 13 weeks)", -1),
    ("sibling_assortment", "after same-line launch", -1),
    ("sibling_assortment", "after same-line exit", +1),
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = _REPO_ROOT / "web" / "src" / "lib" / "data" / "accuracy.json"


# --- truth-side quantity ----------------------------------------------------


def _truth_causal_per_row(truth_df):
    """Per (sku, store_id, week_ending): the promotion's causal incremental units.

    ``lift - dip + transfer`` in the identity observed = baseline + lift - dip +
    transfer + noise. Noise is excluded — it is not caused by the promotion (spec §2).
    This is the only place a truth column is read; only the aggregated *error* leaves
    this module.
    """
    causal = truth_df["lift_units"] - truth_df["dip_units"] + truth_df["transfer_units"]
    return pd.DataFrame(
        {
            "sku": truth_df["sku"],
            "store_id": truth_df["store_id"],
            "week_ending": truth_df["week_ending"],
            "causal_units": causal,
        }
    )


# --- observed regime features (never truth-derived, spec §6) -----------------


def _depth_band(depth):
    if depth < 0.10:
        return "shallow (<10%)"
    if depth < 0.20:
        return "moderate (10–20%)"
    if depth < 0.30:
        return "deep (20–30%)"
    return "very deep (≥30%)"


def _duration_band(weeks):
    if weeks <= 1:
        return "1 week"
    if weeks == 2:
        return "2 weeks"
    return "3+ weeks"


def _season(month):
    return {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"}[month]


def _relaxed_band(share):
    if pd.isna(share):
        return None
    if share == 0:
        return "full stratum"
    if share >= 1:
        return "fully relaxed"
    return "mixed"


def _observed_features(events):
    """Observed regime labels, one row per event. No truth touched here."""
    duration_weeks = ((events["end_week"] - events["start_week"]).dt.days // 7) + 1
    return pd.DataFrame(
        {
            "promo_id": events["promo_id"],
            "promo_type": events["promo_type"],
            "retailer": events["retailer_id"],
            "product_line": events["sku"].str.split("-").str[1],
            "depth_band": events["discount_depth_pct"].map(_depth_band),
            "duration_band": duration_weeks.map(_duration_band),
            "season": events["start_week"].dt.month.map(_season),
        }
    )


# --- row attribution precondition (accuracy-spec §11.1) -----------------------


def assert_one_event_per_row(events):
    """Refuse to score if two events on one sku × retailer overlap in time.

    Rows are attributed to the event named by their OBSERVED ``promo_id``; the
    upstream per-row cause tag is first-claim and SKU-order dependent and is never
    read here. That attribution is unambiguous only if each promoted row has exactly
    one scheduled event. If a generation breaks it, scoring stops — no tie-break is
    applied silently.
    """
    ordered = events.sort_values(["sku", "retailer_id", "start_week", "promo_id"], kind="stable")
    previous_end = ordered.groupby(["sku", "retailer_id"])["end_week"].shift()
    overlapping = ordered[ordered["start_week"] <= previous_end]
    if len(overlapping):
        raise ValueError(
            f"{len(overlapping)} events overlap an earlier event on the same sku x retailer "
            f"(first: {overlapping['promo_id'].iloc[0]}); row attribution by observed "
            "promo_id would be ambiguous. Refusing to score (accuracy-spec §11.1)."
        )


# --- assortment regimes from the observed key universe (accuracy-spec §11) ----


def _assortment_features(events, delta):
    """``life_stage`` and ``sibling_assortment`` per event, from scan presence only.

    A SKU's first and last observed week are facts of the observed layer — a real
    client's scan data shows exactly this. No truth, no generator module.
    """
    window_start, window_end = delta["week_ending"].min(), delta["week_ending"].max()
    presence = delta[["sku", "store_id", "week_ending"]].copy()
    presence["retailer_id"] = presence["store_id"].str.rsplit("-S", n=1).str[0]

    span = presence.groupby("sku")["week_ending"].agg(first_week="min", last_week="max")
    span["is_launch"] = span["first_week"] > window_start
    span["is_exit"] = span["last_week"] < window_end

    ev = events[["promo_id", "sku", "retailer_id", "start_week"]].merge(
        span, left_on="sku", right_index=True, how="left"
    )
    in_fade = ev["is_exit"] & (ev["start_week"] > ev["last_week"] - LIFE_WINDOW)
    # S <= F + 12 weeks: life weeks 1–13, the launch week being life week 1.
    last_launch_start = ev["first_week"] + LIFE_WINDOW - pd.Timedelta(weeks=1)
    in_launch = ev["is_launch"] & (ev["start_week"] <= last_launch_start)
    ev["life_stage"] = np.select(
        [in_fade, in_launch, ev["is_launch"]],
        ["exit fade (final 13 weeks)", "launch (life weeks 1–13)", "launch (after week 13)"],
        default="continuing",
    )

    # Same-line siblings that launch or exit, with their first/last week per retailer.
    churners = span[span["is_launch"] | span["is_exit"]].index
    per_retailer = (
        presence[presence["sku"].isin(churners)]
        .groupby(["sku", "retailer_id"])["week_ending"]
        .agg(sib_first="min", sib_last="max")
        .reset_index()
        .rename(columns={"sku": "sibling_sku"})
        .merge(span[["is_launch", "is_exit"]], left_on="sibling_sku", right_index=True)
    )
    per_retailer["line"] = per_retailer["sibling_sku"].str.split("-").str[1]
    ev["line"] = ev["sku"].str.split("-").str[1]
    pairs = ev[["promo_id", "sku", "line", "retailer_id", "start_week"]].merge(
        per_retailer, on=["line", "retailer_id"], how="inner"
    )
    pairs = pairs[pairs["sibling_sku"] != pairs["sku"]]
    start = pairs["start_week"]
    pairs["after_launch"] = (
        pairs["is_launch"] & (pairs["sib_first"] > start - LIFE_WINDOW) & (pairs["sib_first"] <= start)
    )
    pairs["after_exit"] = (
        pairs["is_exit"] & (pairs["sib_last"] >= start - LIFE_WINDOW) & (pairs["sib_last"] < start)
    )
    flags = pairs.groupby("promo_id")[["after_launch", "after_exit"]].any()
    ev = ev.merge(flags, left_on="promo_id", right_index=True, how="left")
    after_launch = ev["after_launch"].astype("boolean").fillna(False).astype(bool)
    after_exit = ev["after_exit"].astype("boolean").fillna(False).astype(bool)
    ev["sibling_assortment"] = np.select(
        [after_launch & after_exit, after_launch, after_exit],
        ["after both", "after same-line launch", "after same-line exit"],
        default="none",
    )
    return ev[["promo_id", "life_stage", "sibling_assortment"]]


def _life_stage_economics(result, assortment):
    """Prediction 4 (accuracy-spec §11.5): coverage and the ESTIMATED loss rate by
    life stage. Estimates and observed counts — no truth enters this block."""
    ev = result.events[["promo_id", "estimable", "lost_money"]].merge(assortment, on="promo_id")
    out = []
    for label, group in ev.groupby("life_stage", sort=True):
        estimable = group[group["estimable"]]
        out.append(
            {
                "label": str(label),
                "n_events": len(group),
                "n_estimable": len(estimable),
                "n_lost_money": int(estimable["lost_money"].sum()),
            }
        )
    return out


def _prediction_outcomes(scored_by_method):
    """Hit / miss / suppressed for each pre-registered §4.9.7 direction (§11.6)."""
    outcomes = []
    for regime, label, sign in PREDICTIONS:
        entry = {"regime": regime, "label": label, "predicted_bias": "high" if sign > 0 else "low"}
        for method, scored in scored_by_method.items():
            bucket = scored[scored["pct_defined"] & (scored[regime] == label)]
            block = {"n_events": len(bucket)}
            if len(bucket) < MIN_BUCKET:
                block["outcome"] = "suppressed"
            else:
                median = float(bucket["signed_pct_error"].median())
                block["median_signed_pct_error"] = round(median, 1)
                block["outcome"] = "hit" if median * sign > 0 else "miss"
            entry[method] = block
        outcomes.append(entry)
    return outcomes


# --- scoring ----------------------------------------------------------------


def _score_method(result, truth_causal):
    """Per-event signed % error for one method, on the rows that method scored.

    Joins the method's estimable store-weeks to truth at the same grain, so error
    measures estimation accuracy, not coverage (spec §2).
    """
    rows = result.rows.merge(truth_causal, on=["sku", "store_id", "week_ending"], how="left")
    rows["est_units"] = rows["observed_units"] - rows["baseline_units"]

    per_event = (
        rows.groupby("promo_id", sort=True)
        .agg(est_incremental=("est_units", "sum"), true_incremental=("causal_units", "sum"))
        .reset_index()
    )
    per_event["abs_unit_error"] = (per_event["est_incremental"] - per_event["true_incremental"]).abs()
    # % error only where the true denominator is meaningfully non-zero.
    defined = per_event["true_incremental"].abs() >= FLOOR_UNITS
    signed = 100.0 * (per_event["est_incremental"] - per_event["true_incremental"]) / per_event["true_incremental"]
    per_event["signed_pct_error"] = np.where(defined, signed, np.nan)
    per_event["pct_defined"] = defined
    return per_event


def _headline(scored):
    defined = scored[scored["pct_defined"]]
    below = scored[~scored["pct_defined"]]
    headline = {
        # One decimal everywhere — false-precision asymmetry reads sloppy on a
        # measurement page (copy-audit 2026-08-22).
        "median_abs_pct_error": round(float(defined["signed_pct_error"].abs().median()), 1),
        "median_signed_pct_error": round(float(defined["signed_pct_error"].median()), 1),
        "n_scored": len(defined),
        "n_below_floor": len(below),
    }
    # Aggregate absolute error for the below-floor bucket, only if it is large enough
    # to not read back to an individual event.
    if len(below) >= MIN_BUCKET:
        headline["median_abs_unit_error_below_floor"] = round(float(below["abs_unit_error"].median()), 3)
    return headline


def _regime(scored_with_features, feature):
    """Median errors per observed-feature bucket, suppressing buckets < MIN_BUCKET."""
    defined = scored_with_features[scored_with_features["pct_defined"]]
    buckets = []
    for label, group in defined.groupby(feature, sort=True):
        if label is None or len(group) < MIN_BUCKET:
            continue  # ≥5 events per bucket, so no bucket reads back to one event
        buckets.append(
            {
                "label": str(label),
                "n_events": len(group),
                "median_abs_pct_error": round(float(group["signed_pct_error"].abs().median()), 1),
                "median_signed_pct_error": round(float(group["signed_pct_error"].median()), 1),
            }
        )
    return buckets


def _method_block(result, truth_causal, features, extra_regimes=None):
    scored = _score_method(result, truth_causal).merge(features, on="promo_id", how="left")
    regimes = {
        feature: _regime(scored, feature)
        for feature in (
            "promo_type",
            "retailer",
            "product_line",
            "depth_band",
            "duration_band",
            "season",
            "life_stage",
            "sibling_assortment",
        )
    }
    if extra_regimes:
        for name, column in extra_regimes.items():
            merged = scored.merge(column, on="promo_id", how="left")
            regimes[name] = _regime(merged, name)
    return {"headline": _headline(scored), "regimes": regimes}, scored


def _story_lines(events, scored0, scored1):
    """Per seeded story: each method's signed % error. A percentage, not a truth value
    — true incremental is not published and is not reconstructable from a % alone."""
    s0 = scored0.set_index("promo_id")
    s1 = scored1.set_index("promo_id")
    lines = []
    stories = events[events["story_tag"].isin(STORY_TAGS)]
    for row in stories.itertuples(index=False):
        pid = row.promo_id

        def _pct(scored_indexed, pid=pid):
            if pid not in scored_indexed.index or not bool(scored_indexed.loc[pid, "pct_defined"]):
                return None
            return round(float(scored_indexed.loc[pid, "signed_pct_error"]), 1)

        lines.append(
            {
                "story_tag": row.story_tag,
                "promo_id": pid,
                "method0": {"estimable": pid in s0.index, "signed_pct_error": _pct(s0)},
                "method1": {"estimable": pid in s1.index, "signed_pct_error": _pct(s1)},
            }
        )
    return lines


def compute():
    """Score both methods against truth and return the artifact dict (errors only)."""
    events, delta = pr.load()

    # The one guard that must run before any scoring: refuse observed rows from one
    # generation scored against truth from another (the only silent failure here).
    truth.assert_aligned_with_observed(delta)
    # Row attribution is by observed promo_id, so it must be unambiguous (§11.1).
    assert_one_event_per_row(events)
    truth_causal = _truth_causal_per_row(truth.load_truth())

    assortment = _assortment_features(events, delta)
    features = _observed_features(events).merge(assortment, on="promo_id", how="left")
    result0 = method0.estimate()
    result1 = method1.estimate()

    # Method 1's match_relaxed_share is an observed regime dimension (spec §6).
    relaxed = result1.events[["promo_id"]].copy()
    relaxed["match_relaxed_share"] = result1.events["match_relaxed_share"].map(_relaxed_band)

    block0, scored0 = _method_block(result0, truth_causal, features)
    block1, scored1 = _method_block(
        result1, truth_causal, features, extra_regimes={"match_relaxed_share": relaxed}
    )
    block0["life_stage_economics"] = _life_stage_economics(result0, assortment)
    block1["life_stage_economics"] = _life_stage_economics(result1, assortment)

    return {
        "schema": SCHEMA,
        "package_version": pr.__version__,
        "floor_units": FLOOR_UNITS,
        "methods": {"method0": block0, "method1": block1},
        "predictions": _prediction_outcomes({"method0": scored0, "method1": scored1}),
        "stories": _story_lines(events, scored0, scored1),
    }


def serialize(payload):
    """Canonical JSON bytes-as-str: sorted keys, fixed separators, trailing LF."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def build(out_path=DEFAULT_OUT):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(serialize(compute()).encode("utf-8"))
    return out_path


def main():
    path = build()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
