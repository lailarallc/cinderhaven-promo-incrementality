"""Deliberate violation: reaching the churn step through the package alias.

No import statement names `assortment`; the attribute access does.
"""

import cinderhaven_promo_response as pr


def estimate_baseline(delta):
    return pr.assortment.churn(42)  # <- the violation
