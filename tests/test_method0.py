"""Method 0 estimator — properties, not golden numbers.

These assert invariants the pre-period-average estimator must hold (spec
``docs/estimators.md``): exact reconciliation, sign, the phantom near-zero-lift
property, the estimable-count labelling, and a background-distribution claim for
the giveaway share. Where a figure is pinned (the two non-estimable events,
N_estimable) it is pinned deliberately with a comment — it is the point of the
test, not a snapshot of whatever the code did.

Deliberately NOT asserted: that Method 0 "finds" the four seeded stories on the
Scorecard. Method 0 is the naive estimator; whether its biased baseline recovers
``pure_subsidy`` (its volume share is 62.5% against a 60.2% median — barely above)
is the Accuracy view's question, scored against truth there and not here.
Asserting it in this file would over-claim the naive estimator.
"""

import pytest

from incrementality import method0


@pytest.fixture(scope="module")
def result():
    # estimate() calls pr.load() (~0.6s warm); compute once for the module.
    return method0.estimate()


# --- reconciliation (spec 2.7): exact, no float tolerance -------------------


def test_portfolio_net_ties_to_row_grain_exactly(result):
    # The event-sum and the row-grain sum are the same integer cents added in two
    # groupings. Integer equality, no tolerance — the whole reason money is cents.
    row_grain = int(result.rows["incremental_margin_cents"].sum())
    event_grain = int(result.events.loc[result.events["estimable"], "net_margin_cents"].sum())
    assert row_grain == event_grain
    assert result.portfolio["net_incremental_margin_cents"] == row_grain


def test_net_margin_and_cost_are_integer_cents(result):
    ev = result.events
    # Nullable Int64 for net (null on non-estimable events); plain int64 for cost.
    assert str(ev["net_margin_cents"].dtype) == "Int64"
    assert str(ev["accrued_cost_cents"].dtype) == "int64"
    assert isinstance(result.portfolio["total_accrued_spend_cents"], int)
    assert isinstance(result.portfolio["net_incremental_margin_cents"], int)


# --- estimability and its labels (spec 2.2) ---------------------------------


def test_all_131_events_present_with_129_estimable(result):
    ev = result.events
    assert len(ev) == 5636
    assert result.portfolio["n_events"] == 5636
    # N_estimable is pinned: it is the labelled denominator the tool refuses to
    # shrink silently. If it moves, the pre-period sufficiency logic changed.
    assert result.portfolio["n_estimable"] == 5484
    assert int(ev["estimable"].sum()) == 5484


def test_non_estimable_events_all_carry_the_pre_period_reason(result):
    ev = result.events
    non_estimable = ev[~ev["estimable"]]
    # Method 0 excludes an event when no store has the four pre-period weeks it needs
    # (series-start and sparse-authorization events). The specific set moves with the
    # generation; the invariant is that every exclusion carries the reason, so the
    # labelled denominator is never silently shrunk (spec 2.2).
    assert len(non_estimable) > 0
    assert (non_estimable["exclusion_reason"] == "insufficient_pre_period").all()


def test_non_estimable_events_carry_no_fabricated_numbers(result):
    non_estimable = result.events[~result.events["estimable"]]
    assert non_estimable["net_margin_cents"].isna().all()
    assert non_estimable["roi"].isna().all()
    assert non_estimable["lost_money"].isna().all()
    assert non_estimable["subsidized_cost_share"].isna().all()


# --- sign: incremental margin is not clamped --------------------------------


def test_event_net_margins_span_both_signs(result):
    est = result.events[result.events["estimable"]]
    # A promoted week can sell below its pre-period average; the negative sign is
    # carried, not floored at zero.
    assert est["net_margin_cents"].min() < 0
    assert est["net_margin_cents"].max() > 0


def test_portfolio_has_both_winners_and_losers(result):
    pf = result.portfolio
    assert 0 < pf["n_lost_money"] < pf["n_estimable"]


# --- phantom near-zero-lift (spec 4, DECISIONS) -----------------------------


def test_phantom_events_produce_negligible_portfolio_lift(result):
    # Phantom promos ran nowhere: every promoted row is non-complied, so the
    # incremental is noise around zero and cannot be a systematic contributor.
    # Aggregate phantom net must be a tiny fraction of portfolio net — a claim
    # about no-lift, robust to the sign of the noise on any single phantom.
    ev = result.events
    phantom_net = int(ev.loc[ev["plan_status"] == "phantom", "net_margin_cents"].sum())
    portfolio_net = result.portfolio["net_incremental_margin_cents"]
    assert abs(phantom_net) < 0.05 * portfolio_net


# --- zero accrued cost (spec 2.6 clarification) -----------------------------


def test_zero_cost_events_have_null_roi_but_defined_lost_money(result):
    ev = result.events
    zero_cost = ev[(ev["accrued_cost_cents"] == 0) & ev["estimable"]]
    assert len(zero_cost) >= 1  # at least the two zero-cost phantoms
    # ROI divides by cost — undefined at zero, so null (not a sentinel).
    assert zero_cost["roi"].isna().all()
    # lost_money uses net < cost, still defined at zero cost.
    assert zero_cost["lost_money"].notna().all()


# --- giveaway share: bounded ratio + background distribution (spec 2.4) ------


def test_giveaway_share_flag_marks_exactly_the_over_one_events(result):
    ev = result.events
    scored = ev[ev["subsidized_cost_share"].notna()]
    over_one = scored["subsidized_cost_share"] > 1.0
    flagged = scored["baseline_exceeds_promoted"].astype("boolean").fillna(False)
    # A share > 1 (baseline exceeded promoted volume — a dip) is exactly the set
    # the net-dip flag marks, so the view never shows a nonsensical >100% subsidy.
    assert (over_one.to_numpy() == flagged.to_numpy()).all()


def test_phantom_events_have_no_giveaway_share(result):
    # No complied volume sold, so "share of discounted volume" is undefined.
    ev = result.events
    phantom = ev[ev["plan_status"] == "phantom"]
    assert phantom["subsidized_cost_share"].isna().all()


def test_background_giveaway_share_is_substantial(result):
    # The honest, non-seeded finding: portfolio-wide, a large share of the volume
    # sold on discount would have sold anyway — the mediocre middle the tool
    # exists to show, not a planted outlier. A background-distribution claim.
    ev = result.events
    shares = ev.loc[ev["subsidized_cost_share"].notna(), "subsidized_cost_share"]
    assert shares.min() >= 0.0
    assert shares.median() > 0.3


# --- determinism (spec 6) ---------------------------------------------------


def test_two_runs_produce_an_identical_portfolio(result):
    again = method0.estimate().portfolio
    # Same pinned package + same code → identical numbers, floats included, since
    # the ratios derive from the same integer cents.
    assert again == result.portfolio
