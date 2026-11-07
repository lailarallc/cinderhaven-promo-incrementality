"""Deliberate violation: estimation code importing the v0.7.0 churn step.

assortment.churn() returns launch settled velocities, exit fades and the
sibling-cannibalization disposition — generator structure, not observed data.
"""

from cinderhaven_promo_response.assortment import churn  # <- the violation


def estimate_baseline(delta):
    return churn
