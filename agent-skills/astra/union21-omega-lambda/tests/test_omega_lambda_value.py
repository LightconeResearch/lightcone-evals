from __future__ import annotations

from _util import find_omega_lambda_estimates

# Suzuki et al. 2012: Omega_Lambda = 0.705 (+0.040, -0.043). Our own fit lands
# at 0.722 (statistical only) or 0.714 (with systematics); this window covers
# either legitimate choice of covariance while rejecting a wrong cosmology.
LOWER, UPPER = 0.695, 0.745


def test_recovered_omega_lambda_is_in_expected_range() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    in_range = [omega for omega, _sigma, _path in estimates if LOWER <= omega <= UPPER]
    assert in_range, (
        f"no recorded Omega_Lambda estimate fell in [{LOWER}, {UPPER}]: "
        f"{[(o, str(p)) for o, _s, p in estimates]}"
    )
