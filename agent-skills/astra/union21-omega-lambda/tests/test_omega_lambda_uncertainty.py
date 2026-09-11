from __future__ import annotations

from _util import find_omega_lambda_estimates

# Suzuki et al. 2012 published Omega_Lambda = 0.705 (+0.040, -0.043); ours is
# only comparable once the systematics-inclusive covariance is used, which
# widens sigma from ~0.013 (statistical only) to ~0.030. This dimension is
# scored separately from the central value: the value tests the fit itself,
# this tests whether the agent found and used the systematics covariance.
LOWER, UPPER = 0.022, 0.040


def test_final_recorded_uncertainty_is_comparable_to_the_paper() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    sigmas = [sigma for _omega, sigma, _path in estimates if sigma is not None]
    assert sigmas, "no uncertainty recorded alongside any Omega_Lambda estimate"
    assert any(LOWER <= sigma <= UPPER for sigma in sigmas), (
        f"no recorded Omega_Lambda uncertainty fell in [{LOWER}, {UPPER}]: {sigmas}"
    )
