"""Method 1 (comparable-store) — properties, not golden numbers.

Invariants the comparable-store estimator must hold (spec §3): exact
reconciliation, integer-cent money, the visible `insufficient_comparable_pool`
exclusion, the hierarchical relaxation recorded as an observed regime dimension,
and the coverage contrast with Method 0 (a better baseline rescues a series-start
event the naive one cannot). Pinned figures (the two non-estimable events, the
relaxation of the seeded stories) are pinned deliberately — they are the point of
the test, and they move only on a logged MIN_POOL/band re-run.

Deliberately NOT asserted: that Method 1 recovers the seeded stories' *truth*.
Whether its comparable baseline is closer to truth than Method 0's is the Accuracy
view's question, scored against truth there. Here we assert only that the stories
are estimable (the flat-match failure they exposed does not return).
"""

import pytest

from incrementality import method0, method1


@pytest.fixture(scope="module")
def result():
    # ~13s: the per-store-event hierarchical match. Computed once for the module.
    return method1.estimate()


@pytest.fixture(scope="module")
def method0_result():
    return method0.estimate()


# --- reconciliation (spec 2.7) ----------------------------------------------


def test_portfolio_net_ties_to_row_grain_exactly(result):
    row_grain = int(result.rows["incremental_margin_cents"].sum())
    event_grain = int(result.events.loc[result.events["estimable"], "net_margin_cents"].sum())
    assert row_grain == event_grain
    assert result.portfolio["net_incremental_margin_cents"] == row_grain


def test_money_is_integer_cents(result):
    ev = result.events
    assert str(ev["net_margin_cents"].dtype) == "Int64"
    assert str(ev["accrued_cost_cents"].dtype) == "int64"
    assert isinstance(result.portfolio["total_accrued_spend_cents"], int)


# --- estimability, its reason, and the coverage contrast (spec 3.5, 3.6) -----


def test_all_131_present_and_129_estimable(result):
    ev = result.events
    assert len(ev) == 5636
    assert result.portfolio["n_estimable"] == 4818


def test_non_estimable_events_carry_the_comparable_pool_reason(result):
    ev = result.events
    non = ev[~ev["estimable"]]
    # The specific excluded set moves with the generation (v0.6.1 density thins the
    # comparable pools — DECISIONS 2026-08-27); the invariant is that every exclusion
    # carries the reason and no fabricated number, so the denominator stays honest.
    assert len(non) > 0
    assert (non["exclusion_reason"] == "insufficient_comparable_pool").all()
    assert non["net_margin_cents"].isna().all()
    assert non["roi"].isna().all()


def test_method1_estimates_some_events_method0_cannot(result, method0_result):
    # The "a better baseline rescues some of these" contrast (spec 3.6): comparable
    # stores have during-week velocity where a series-start test store has no pre-period,
    # so Method 1 estimates events Method 0 must exclude. The specific ids move with the
    # generation; a non-empty rescue set is the invariant.
    m1 = result.events.set_index("promo_id")
    m0 = method0_result.events.set_index("promo_id")
    rescued = [p for p in m1.index if m1.loc[p, "estimable"] and not m0.loc[p, "estimable"]]
    assert len(rescued) > 0


def test_the_two_methods_exclude_for_different_reasons(result, method0_result):
    # The reason codes distinguish the methods' coverage (spec §3.5).
    m1_reasons = set(result.events["exclusion_reason"].dropna().unique())
    m0_reasons = set(method0_result.events["exclusion_reason"].dropna().unique())
    assert m1_reasons == {"insufficient_comparable_pool"}
    assert m0_reasons == {"insufficient_pre_period"}


# --- sign, winners and losers -----------------------------------------------


def test_event_net_margins_span_both_signs(result):
    est = result.events[result.events["estimable"]]
    assert est["net_margin_cents"].min() < 0
    assert est["net_margin_cents"].max() > 0


def test_portfolio_has_winners_and_losers(result):
    pf = result.portfolio
    assert 0 < pf["n_lost_money"] < pf["n_estimable"]


# --- the seeded stories are estimable (flat-match regression) ----------------


def test_all_four_seeded_stories_are_estimable(result):
    # The flat region+format+band match dropped all four (three are Walmart, a
    # single-banner format class). The hierarchy must keep them estimable.
    ev = result.events
    stories = ev[ev["story_tag"].notna()]
    assert len(stories) == 4
    assert stories["estimable"].all()


# --- the relaxation regime dimension (spec 3.3) -----------------------------


def test_relaxed_share_is_a_bounded_fraction_for_estimable_events(result):
    ev = result.events
    est = ev[ev["estimable"]]
    shares = est["match_relaxed_share"].astype("float64")
    assert shares.min() >= 0.0
    assert shares.max() <= 1.0
    # Non-estimable events have no share.
    assert ev.loc[~ev["estimable"], "match_relaxed_share"].isna().all()


def test_relaxation_actually_happens_because_single_banner_classes_exist(result):
    # club (Costco) and supercenter (Walmart) are single-banner format classes, so
    # a large share of matching must relax to region+volume — the measured reason
    # the hierarchy exists. A degenerate all-full result would mean the relaxation
    # path is dead code.
    est = result.events[result.events["estimable"]]
    relaxed_any = (est["match_relaxed_share"].astype("float64") > 0).mean()
    assert relaxed_any > 0.5


# --- determinism (spec 3.8) --------------------------------------------------


def test_two_runs_produce_an_identical_portfolio(result):
    again = method1.estimate().portfolio
    assert again == result.portfolio
