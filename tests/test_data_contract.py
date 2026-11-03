"""The consumer contract, asserted rather than trusted.

This is the whole interface to `cinderhaven-promo-response`: two frames from
`pr.load()`, observed columns only. If any of it drifts, every downstream
number drifts with it and nothing else in this repo would notice.

Green on a cold cache since upstream v0.1.1 (SHA 7cfe95c). In v0.1.0
`pr.load()` raised FileNotFoundError on the first call in any fresh install —
the consumer serve path rewrote a source file absent from the wheel — so this
job was red on every CI run (cold cache) and passed only on a warm local one.
The upstream packaging fix removed that asymmetry; the pin was moved to v0.1.1
in the same change that flipped this green. See FAILURES.md and DECISIONS.md.
"""

import cinderhaven_promo_response as pr
import pytest

# Contract figures from CLAUDE.md. Pinned deliberately: these are the shape of
# the dependency, not an output of this repo's code, so a golden value is the
# point. A change here means the upstream data changed under a pinned SHA,
# which should be impossible.
EXPECTED_EVENTS = 5897
EXPECTED_SCAN_ROWS = 1_340_462
OBSERVED_COLUMNS = [
    "sku",
    "store_id",
    "week_ending",
    "observed_units",
    "regular_price",
    "promoted_price",
    "promo_id",
    "complied",
]


@pytest.fixture(scope="session")
def loaded():
    """~8.5s cold, ~0.6s warm. Loaded once per session, per tests/CLAUDE.md."""
    return pr.load()


def test_package_is_the_pinned_version(loaded):
    assert pr.__version__ == "0.6.2"


def test_event_count_matches_the_contract(loaded):
    events, _ = loaded
    assert len(events) == EXPECTED_EVENTS


def test_scan_delta_row_count_matches_the_contract(loaded):
    _, delta = loaded
    assert len(delta) == EXPECTED_SCAN_ROWS


def test_scan_delta_carries_observed_columns_only(loaded):
    """Truth must not ride along on the observed artifact.

    The upstream loader hard-fails if it does. Asserted again on this side of
    the boundary because it is the one failure that would otherwise be silent
    and would invalidate every accuracy figure downstream.
    """
    _, delta = loaded
    assert list(delta.columns) == OBSERVED_COLUMNS


# store_card() — added in v0.3.0, consumed by Method 1's comparable-store match.
# Store-master identity only; the demarcation forbids anything velocity-shaped.
STORE_CARD_COLUMNS = ["store_id", "retailer_id", "region"]
EXPECTED_STORES = 640


def test_store_card_carries_identity_columns_only(loaded):
    # No volume/size tier: the card is identity (geography), and volume is derived
    # by the estimator from observed units — the store_card demarcation (DECISIONS).
    card = pr.store_card()
    assert list(card.columns) == STORE_CARD_COLUMNS


def test_store_card_covers_every_store(loaded):
    card = pr.store_card()
    assert card["store_id"].nunique() == EXPECTED_STORES
    assert len(card) == EXPECTED_STORES


def test_store_card_region_is_categorical_not_a_velocity_proxy(loaded):
    # A small closed set of geographic regions — not a per-store continuous value
    # that could stand in for baseline velocity. Guards the demarcation from the
    # consumer side.
    card = pr.store_card()
    assert 2 <= card["region"].nunique() <= 12
