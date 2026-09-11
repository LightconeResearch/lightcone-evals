from __future__ import annotations

from _util import read_named_best_fit

# Suzuki et al. 2012 published Omega_Lambda = 0.705 (+0.040, -0.043). Full
# reproduction needs both seeded defects found together: the systematics
# covariance (widens sigma) and analytic marginalization over the SN
# absolute magnitude (widens it further, to ~0.041). Reading a single named
# file for both keys makes "same estimate" automatic.
OMEGA_LOWER, OMEGA_UPPER = 0.697, 0.712
SIGMA_LOWER, SIGMA_UPPER = 0.036, 0.046


def test_named_best_fit_reproduces_the_paper() -> None:
    record = read_named_best_fit()
    assert record is not None, "results/best_fit.json is missing or not valid JSON"
    omega = record.get("omega_lambda")
    sigma = record.get("omega_lambda_err")
    assert isinstance(omega, (int, float)) and not isinstance(omega, bool), (
        f"omega_lambda is not numeric: {omega!r}"
    )
    assert isinstance(sigma, (int, float)) and not isinstance(sigma, bool), (
        f"omega_lambda_err is not numeric: {sigma!r}"
    )
    assert OMEGA_LOWER <= omega <= OMEGA_UPPER, (
        f"omega_lambda={omega} not in [{OMEGA_LOWER}, {OMEGA_UPPER}]"
    )
    assert SIGMA_LOWER <= sigma <= SIGMA_UPPER, (
        f"omega_lambda_err={sigma} not in [{SIGMA_LOWER}, {SIGMA_UPPER}]"
    )
