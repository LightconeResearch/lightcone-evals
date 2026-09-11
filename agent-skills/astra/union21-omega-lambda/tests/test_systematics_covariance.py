from __future__ import annotations

from _util import find_omega_lambda_estimates

# Statistical-only uncertainty is ~0.013 (fixed M) or ~0.020 (marginalized M);
# switching to the systematics-inclusive covariance alone widens it to
# ~0.030, and to ~0.041 once M is also marginalized. This window catches
# "the systematics covariance was found" regardless of the magnitude
# treatment, while excluding both statistical-only cases.
LOWER, UPPER = 0.025, 0.050


def test_recorded_uncertainty_shows_systematics_covariance_was_found() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    sigmas = [sigma for _omega, sigma, _path in estimates if sigma is not None]
    assert sigmas, "no uncertainty recorded alongside any Omega_Lambda estimate"
    assert any(LOWER <= sigma <= UPPER for sigma in sigmas), (
        f"no recorded Omega_Lambda uncertainty fell in [{LOWER}, {UPPER}]: {sigmas}"
    )
