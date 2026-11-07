"""Walking-skeleton pipeline step: schema, contract values, and determinism.

Determinism is a stated arc requirement — same pinned package + same code must
produce byte-identical artifacts — and nothing else in this repo checks it yet.
This is where that gets asserted, on the one artifact that exists.
"""

import json

from incrementality import build_skeleton


def _build_to(tmp_path, name="skeleton.json"):
    out = tmp_path / name
    return build_skeleton.build(out)


def test_artifact_has_the_declared_schema_and_keys(tmp_path):
    payload = json.loads(_build_to(tmp_path).read_text(encoding="utf-8"))
    assert payload["schema"] == "walking-skeleton/v1"
    assert set(payload) == {
        "schema",
        "package_version",
        "event_count",
        "scan_row_count",
        "total_observed_units",
    }


def test_counts_match_the_data_contract(tmp_path):
    payload = json.loads(_build_to(tmp_path).read_text(encoding="utf-8"))
    # The contract figures from CLAUDE.md. If these move, the upstream data
    # changed under a pinned SHA — which should be impossible.
    assert payload["event_count"] == 5636
    assert payload["scan_row_count"] == 1_293_126


def test_every_numeric_value_is_an_integer(tmp_path):
    # No floats in the artifact — the determinism requirement forbids them, and
    # units are integer by decision.
    payload = json.loads(_build_to(tmp_path).read_text(encoding="utf-8"))
    for key in ("event_count", "scan_row_count", "total_observed_units"):
        assert isinstance(payload[key], int), f"{key} is not an int"


def test_two_builds_are_byte_identical(tmp_path):
    # Determinism: no wall-clock, no unseeded value, pinned serialization.
    a = _build_to(tmp_path, "a.json").read_bytes()
    b = _build_to(tmp_path, "b.json").read_bytes()
    assert a == b


def test_artifact_uses_lf_newline_not_platform_default(tmp_path):
    # The artifact must hash identically on Windows and Linux CI. text-mode
    # writes translate LF to CRLF on Windows; this guards against a regression
    # to write_text, which would make dev and CI artifacts differ.
    raw = _build_to(tmp_path).read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")


def test_serialization_is_canonical(tmp_path):
    # Sorted keys and fixed separators — the exact shape the determinism test
    # depends on. Pinned so a formatting change is a visible failure.
    raw = _build_to(tmp_path).read_bytes()
    payload = json.loads(raw)
    expected = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    assert raw == expected.encode("utf-8")
