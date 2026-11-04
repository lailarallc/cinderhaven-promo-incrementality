"""Allowed: an attribute named `baseline` on something that is not the package."""

import cinderhaven_promo_response as pr


def estimate_baseline(result):
    events, _ = pr.load()
    return result.baseline, events
