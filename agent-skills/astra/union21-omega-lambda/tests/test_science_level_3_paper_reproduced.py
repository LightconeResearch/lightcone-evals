from __future__ import annotations

from _util import (
    LEVEL_3_OMEGA_LAMBDA,
    LEVEL_3_OMEGA_LAMBDA_ERR,
    NAMED_BEST_FIT_PATH,
    OMEGA_LAMBDA_ERR_KEY,
    OMEGA_LAMBDA_KEY,
    is_numeric,
    read_named_best_fit,
)

# Suzuki et al. 2012 published Omega_Lambda = 0.705 (+0.040, -0.043). Full
# reproduction needs both seeded defects found together: the systematics
# covariance (widens sigma) and analytic marginalization over the SN
# absolute magnitude (widens it further, to ~0.041). Reading a single named
# file for both keys makes "same estimate" automatic.
OMEGA_LOWER, OMEGA_UPPER = LEVEL_3_OMEGA_LAMBDA
SIGMA_LOWER, SIGMA_UPPER = LEVEL_3_OMEGA_LAMBDA_ERR


def test_named_best_fit_reproduces_the_paper() -> None:
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"
    omega = record.get(OMEGA_LAMBDA_KEY)
    sigma = record.get(OMEGA_LAMBDA_ERR_KEY)
    assert is_numeric(omega), f"{OMEGA_LAMBDA_KEY} is not numeric: {omega!r}"
    assert is_numeric(sigma), f"{OMEGA_LAMBDA_ERR_KEY} is not numeric: {sigma!r}"
    assert OMEGA_LOWER <= omega <= OMEGA_UPPER, (
        f"{OMEGA_LAMBDA_KEY}={omega} not in [{OMEGA_LOWER}, {OMEGA_UPPER}]"
    )
    assert SIGMA_LOWER <= sigma <= SIGMA_UPPER, (
        f"{OMEGA_LAMBDA_ERR_KEY}={sigma} not in [{SIGMA_LOWER}, {SIGMA_UPPER}]"
    )
