"""Event Anatomy artifact (anatomy/v2) — observed + estimated, never truth.

Anatomy explains the estimate; accuracy judges it. So this artifact carries only
observed metadata and the estimators' own outputs — the three-bar volume waterfall,
margin, cost — and never a truth decomposition (lift / dip / transfer / noise /
attribution). Option B (DECISIONS 2026-08-27) writes it as one slice per event plus a
prerender manifest, so the ~5,900-event artifact never ships whole to the browser.
These tests pin the record shape (from compute(), the source both writers share), the
slice/manifest structure, no-truth, and determinism.
"""

import json

import pytest

from incrementality import build_anatomy

# Truth-only decomposition columns — never in this artifact. (subsidized_baseline is
# the *estimated* baseline, an estimator output, and is allowed; only truth's own
# lift/dip/transfer/noise/attribution are forbidden.)
FORBIDDEN_TRUTH_TOKENS = ("lift_units", "dip_units", "transfer_units", "noise_units", "caused_by")

META_KEYS = {
    "promo_id",
    "sku",
    "retailer_id",
    "promo_type",
    "funding_mechanism",
    "plan_status",
    "story_tag",
    "start_week",
    "end_week",
    "n_weeks",
    "discount_depth_pct",
    "method0",
    "method1",
}

METHOD_KEYS = {
    "estimable",
    "exclusion_reason",
    "gross_promoted_units",
    "subsidized_baseline_units",
    "net_incremental_units",
    "net_margin_cents",
    "accrued_cost_cents",
    "roi",
    "lost_money",
    "subsidized_cost_share",
    "baseline_exceeds_promoted",
    "n_stores_estimable",
}


# Two estimator runs total for the module: compute() for the records, build() for the
# slices + manifest. Both scoped to the module.
@pytest.fixture(scope="module")
def computed():
    return build_anatomy.compute()


@pytest.fixture(scope="module")
def records(computed):
    return computed["events"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("anatomy")
    slices = out / "slices"
    manifest_path = out / "anatomy-manifest.json"
    build_anatomy.build(slices, manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return slices, manifest, manifest_path


def test_schema_and_full_event_count(computed):
    assert computed["schema"] == "anatomy/v2"
    assert set(computed) == {"schema", "package_version", "events"}
    assert len(computed["events"]) == 5636


def test_artifact_carries_no_truth_decomposition_token(computed):
    raw = build_anatomy.serialize(computed)
    for token in FORBIDDEN_TRUTH_TOKENS:
        assert token not in raw, f"anatomy leaks a truth token: {token!r}"


def test_every_event_has_both_methods_and_meta(records):
    for event in records:
        assert set(event) == META_KEYS
        assert set(event["method0"]) == METHOD_KEYS
        assert set(event["method1"]) == METHOD_KEYS


def test_waterfall_reconciles_gross_minus_baseline_equals_net(records):
    # The three bars must add up on screen: gross - baseline = net, to the displayed
    # decimal, for every estimable event under every method.
    for event in records:
        for method in ("method0", "method1"):
            m = event[method]
            if m["estimable"]:
                assert m["gross_promoted_units"] is not None
                assert round(m["gross_promoted_units"] - m["subsidized_baseline_units"], 1) == m[
                    "net_incremental_units"
                ]


def test_non_estimable_events_have_null_volumes_and_a_reason(records):
    # The specific excluded ids move with the generation; the invariant is that a
    # non-estimable method block carries a reason and null volumes.
    non = [e for e in records if not e["method0"]["estimable"]]
    assert non
    for event in non:
        m0 = event["method0"]
        assert m0["exclusion_reason"] == "insufficient_pre_period"
        assert m0["gross_promoted_units"] is None
        assert m0["net_incremental_units"] is None


def test_slices_and_manifest_are_written(built):
    slices, manifest, _ = built
    assert manifest["schema"] == "anatomy/v2"
    assert manifest["count"] == 5636
    # The prerender set is a bounded, non-empty subset — the whole point of Option B.
    assert 0 < len(manifest["prerender"]) < manifest["count"]
    slice_files = list(slices.glob("*.json"))
    assert len(slice_files) == 5636
    sample = json.loads((slices / f"{manifest['prerender'][0]}.json").read_text(encoding="utf-8"))
    assert sample["schema"] == "anatomy/v2"
    assert set(sample["event"]) == META_KEYS


def test_every_story_event_is_prerendered(records, built):
    _, manifest, _ = built
    story_ids = {e["promo_id"] for e in records if e["story_tag"] is not None}
    assert story_ids, "there are seeded story events"
    # Stories are deep-linked publicly, so they must be baked to HTML regardless of rank.
    assert story_ids <= set(manifest["prerender"])


def test_slices_use_lf_newline_and_no_nan(built):
    slices, manifest, manifest_path = built
    raw = manifest_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    sample = (slices / f"{manifest['prerender'][0]}.json").read_bytes()
    assert b"\r" not in sample
    assert b"NaN" not in sample
    assert b"Infinity" not in sample
    assert sample.endswith(b"\n")


def test_two_computes_are_byte_identical(computed):
    # Determinism: the same pinned package + code serialize identically.
    assert build_anatomy.serialize(computed) == build_anatomy.serialize(build_anatomy.compute())
