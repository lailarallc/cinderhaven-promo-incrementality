"""Deliberate violation: estimation code importing the baseline builder.

baseline.build_baseline() constructs the true counterfactual series — the
answer to the question every estimator in src/ exists to estimate.
"""

from cinderhaven_promo_response import baseline  # <- the violation


def estimate_baseline(delta):
    return baseline.build_baseline
