from __future__ import annotations

from _util import find_omega_lambda_estimates

# Any legitimate combination of covariance and magnitude treatment lands
# here; this dimension only checks the cosmology fit itself is right.
LOWER, UPPER = 0.690, 0.735


def test_recovered_omega_lambda_is_in_expected_range() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    in_range = [omega for omega, _sigma, _path in estimates if LOWER <= omega <= UPPER]
    assert in_range, (
        f"no recorded Omega_Lambda estimate fell in [{LOWER}, {UPPER}]: "
        f"{[(o, str(p)) for o, _s, p in estimates]}"
    )
