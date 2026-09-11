from __future__ import annotations

from _util import find_omega_lambda_estimates

# Suzuki et al. 2012 published Omega_Lambda = 0.705 (+0.040, -0.043). Full
# reproduction needs both seeded defects found together: the systematics
# covariance (widens sigma) and analytic marginalization over the SN
# absolute magnitude (widens it further, to ~0.041). Both bounds must hold
# on the SAME recorded estimate, not just somewhere across different files,
# since only that combination is an actual reproduction rather than two
# unrelated numbers that happen to individually clear looser bars.
OMEGA_LOWER, OMEGA_UPPER = 0.697, 0.712
SIGMA_LOWER, SIGMA_UPPER = 0.036, 0.046


def test_paper_constraint_is_reproduced() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    reproduced = [
        (omega, sigma, path)
        for omega, sigma, path in estimates
        if sigma is not None
        and OMEGA_LOWER <= omega <= OMEGA_UPPER
        and SIGMA_LOWER <= sigma <= SIGMA_UPPER
    ]
    assert reproduced, (
        f"no single recorded estimate had both Omega_Lambda in "
        f"[{OMEGA_LOWER}, {OMEGA_UPPER}] and sigma in [{SIGMA_LOWER}, {SIGMA_UPPER}]: "
        f"{[(o, s, str(p)) for o, s, p in estimates]}"
    )
