"""ROI Scorecard artifact (scorecard/v3) — split schema, NA->null, determinism.

The artifact is the seam between the Python pipeline and the front end (PLAN.md
names it the highest-risk seam). Option B (DECISIONS 2026-08-27) splits it: the
imported scorecard.json carries the summary (a portfolio header per method, the
precomputed chart tiers, filter options, cross-estimable counts) plus a first page of
the ranked list; the full per-event array is written separately and fetched on demand.
These tests pin the summary shape from the file and the per-event records from
compute(), assert only declared estimation fields (no intermediate volumes, no truth),
and that missing values become JSON null, not NaN.
"""

import json

import cinderhaven_promo_response as pr
import pytest

from incrementality import build_scorecard

PORTFOLIO_KEYS = {
    "method_label",
    "n_events",
    "n_estimable",
    "n_lost_money",
    "total_accrued_spend_cents",
    "net_incremental_margin_cents",
    "portfolio_roi",
}

SHARED_EVENT_KEYS = {
    "promo_id",
    "sku",
    "retailer_id",
    "promo_type",
    "plan_status",
    "story_tag",
    "accrued_cost_cents",
    "method0",
    "method1",
}

METHOD0_KEYS = {
    "estimable",
    "exclusion_reason",
    "n_stores_estimable",
    "net_margin_cents",
    "roi",
    "lost_money",
    "subsidized_cost_share",
    "baseline_exceeds_promoted",
}
METHOD1_KEYS = METHOD0_KEYS | {"match_relaxed_share"}

SUMMARY_KEYS = {
    "tiers",
    "filter_options",
    "cross_estimable",
    "net_margin_top_decile_share",
    "first_page_size",
    "spend_context",
}


# Building runs both estimators, so build once for the module and reuse. Both the
# summary and the full-events file go to tmp so the test never touches web/static.
@pytest.fixture(scope="module")
def artifact_path(tmp_path_factory):
    out = tmp_path_factory.mktemp("scorecard")
    return build_scorecard.build(out / "scorecard.json", out / "scorecard-events.json")


@pytest.fixture(scope="module")
def payload(artifact_path):
    return json.loads(artifact_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def records():
    # The full per-event records (fetched on demand at runtime); compute() is the source.
    return build_scorecard.compute()["events"]


def test_artifact_has_the_declared_schema_and_top_level_keys(payload):
    assert payload["schema"] == "scorecard/v3"
    assert set(payload) == {"schema", "package_version", "portfolios", "summary", "first_page"}
    assert payload["package_version"] == pr.__version__


def test_summary_carries_the_precomputed_front_door_fields(payload):
    summary = payload["summary"]
    assert set(summary) == SUMMARY_KEYS
    for method in ("method0", "method1"):
        tiers = summary["tiers"][method]
        assert len(tiers) == 4  # [lost, 1-2x, 2-4x, 4x+]
        assert all(isinstance(n, int) for n in tiers)
    assert set(summary["filter_options"]) == {"retailer", "line", "type", "status"}
    assert set(summary["cross_estimable"]) == {"method0", "method1"}
    assert isinstance(summary["first_page_size"], int)


def test_both_method_portfolios_carry_the_cfo_numbers(payload):
    portfolios = payload["portfolios"]
    assert set(portfolios) == {"method0", "method1"}
    for key, portfolio in portfolios.items():
        assert set(portfolio) == PORTFOLIO_KEYS, key
        assert portfolio["n_events"] == 5636
    # N_estimable is pinned per method: the labelled denominator the tool refuses to
    # shrink silently. If it moves, the sufficiency logic changed.
    assert portfolios["method0"]["n_estimable"] == 5484
    assert portfolios["method1"]["n_estimable"] == 4818
    assert portfolios["method0"]["method_label"].startswith("Method 0")
    assert portfolios["method1"]["method_label"].startswith("Method 1")


def test_first_page_is_a_bounded_declared_subset(payload, records):
    first_page = payload["first_page"]
    ids = {r["promo_id"] for r in records}
    assert 0 < len(first_page) < len(records)
    for record in first_page:
        assert set(record) == SHARED_EVENT_KEYS
        assert record["promo_id"] in ids


def test_every_event_co_locates_both_methods_with_declared_fields(records):
    # No intermediate columns and no truth leak out — only declared fields, and
    # method1 alone carries the relaxation regime dimension.
    assert len(records) == 5636
    for record in records:
        assert set(record) == SHARED_EVENT_KEYS
        assert set(record["method0"]) == METHOD0_KEYS
        assert set(record["method1"]) == METHOD1_KEYS


def test_money_fields_are_integer_cents_or_null(records):
    for record in records:
        assert isinstance(record["accrued_cost_cents"], int)
        for method in ("method0", "method1"):
            net = record[method]["net_margin_cents"]
            assert net is None or isinstance(net, int)
            assert isinstance(record[method]["n_stores_estimable"], int)


def test_a_method_that_cannot_estimate_an_event_serializes_nulls(records):
    # Some event is estimable under Method 0 but not Method 1 (insufficient pool). The
    # specific id moves with the generation; the null serialization is the invariant.
    only_m0 = [r for r in records if r["method0"]["estimable"] and not r["method1"]["estimable"]]
    assert only_m0, "no event estimable under Method 0 but not Method 1"
    m1 = only_m0[0]["method1"]
    assert m1["exclusion_reason"] == "insufficient_comparable_pool"
    assert m1["net_margin_cents"] is None
    assert m1["roi"] is None
    assert m1["match_relaxed_share"] is None


def test_relaxed_share_is_present_and_bounded_where_method1_estimates(records):
    for record in records:
        share = record["method1"]["match_relaxed_share"]
        if record["method1"]["estimable"]:
            assert share is not None and 0.0 <= share <= 1.0
        else:
            assert share is None


def test_artifact_contains_no_nan_or_infinity_tokens(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"NaN" not in raw
    assert b"Infinity" not in raw
    json.loads(raw.decode("utf-8"), parse_constant=_reject)


def _reject(token):
    raise AssertionError(f"non-JSON constant in artifact: {token}")


def test_two_builds_are_byte_identical(artifact_path, tmp_path):
    again = build_scorecard.build(tmp_path / "again.json", tmp_path / "again-events.json")
    assert artifact_path.read_bytes() == again.read_bytes()


def test_artifact_uses_lf_newline_and_canonical_serialization(artifact_path):
    raw = artifact_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    payload = json.loads(raw)
    expected = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    assert raw == expected.encode("utf-8")


def test_spend_context_ratios_are_ordered_percentages(payload):
    # Spend is a smaller share of all revenue than of promoted revenue, and
    # promoted volume is a strict share of total volume — properties, not golden
    # numbers. The scope-note copy reads these, so they must exist and be sane.
    ctx = payload["summary"]["spend_context"]
    assert set(ctx) == {
        "promoted_volume_pct",
        "spend_pct_of_total_revenue",
        "spend_pct_of_promoted_revenue",
    }
    assert 0 < ctx["promoted_volume_pct"] < 100
    assert 0 < ctx["spend_pct_of_total_revenue"] < ctx["spend_pct_of_promoted_revenue"] < 100
