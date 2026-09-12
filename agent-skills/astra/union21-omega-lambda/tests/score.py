#!/usr/bin/env python3
"""The two continuous science scores, printed as JSON on stdout.

These cannot be pytest tests: a pytest verdict is pass/fail, i.e. 0/1, and
the whole point of v3 is that "how close is the answer" is a number, not a
window. So test.sh runs this module directly and folds its output into
/logs/verifier/{reward,details}.json.

Both scores read the *named* best_fit.json through _util — the same strict
contract read the deliverables test uses. A missing file, a missing key, or
a non-numeric value scores 0 for that quantity; it does not crash.

    omega_lambda_score     = exp(-0.5 * ((omega - 0.705) / 0.0415)^2)
    omega_lambda_err_score = exp(-0.5 * (ln(sigma / 0.0415) / ln(1.4))^2)

The first is a Gaussian in Omega_Lambda whose width is the paper's own
uncertainty: 1.00 on the published value, 0.61 one paper-sigma away, ~0.14
two sigma away. The second is a Gaussian in *log* sigma, because an
uncertainty is a scale — being a factor of two too small and a factor of two
too large are the same size of mistake, and a difference of 0.02 means
something completely different at sigma = 0.04 than at sigma = 0.4. Its
width is one factor of 1.4, so a sigma 1.4x too small or too large scores
exp(-1/2) = 0.61.
"""

from __future__ import annotations

import json
import math

from _util import (
    OMEGA_LAMBDA_ERR_KEY,
    OMEGA_LAMBDA_ERR_LOG_WIDTH,
    OMEGA_LAMBDA_ERR_REF,
    OMEGA_LAMBDA_KEY,
    OMEGA_LAMBDA_REF,
    named_value,
)


def omega_lambda_score(omega: float | None) -> float:
    """Gaussian in Omega_Lambda, width = the paper's own uncertainty."""
    if omega is None:
        return 0.0
    return math.exp(-0.5 * ((omega - OMEGA_LAMBDA_REF) / OMEGA_LAMBDA_ERR_REF) ** 2)


def omega_lambda_err_score(sigma: float | None) -> float:
    """Gaussian in ln(sigma), width = one factor of OMEGA_LAMBDA_ERR_LOG_WIDTH.

    A non-positive sigma has no logarithm and is not an uncertainty; it scores 0.
    """
    if sigma is None or sigma <= 0.0:
        return 0.0
    log_ratio = math.log(sigma / OMEGA_LAMBDA_ERR_REF)
    return math.exp(-0.5 * (log_ratio / math.log(OMEGA_LAMBDA_ERR_LOG_WIDTH)) ** 2)


def main() -> None:
    omega = named_value(OMEGA_LAMBDA_KEY)
    sigma = named_value(OMEGA_LAMBDA_ERR_KEY)
    print(
        json.dumps(
            {
                "omega_lambda": omega,
                "omega_lambda_err": sigma,
                "omega_lambda_ref": OMEGA_LAMBDA_REF,
                "omega_lambda_err_ref": OMEGA_LAMBDA_ERR_REF,
                "omega_lambda_score": round(omega_lambda_score(omega), 4),
                "omega_lambda_err_score": round(omega_lambda_err_score(sigma), 4),
            }
        )
    )


if __name__ == "__main__":
    main()
