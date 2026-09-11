from __future__ import annotations

from _util import (
    LEVEL_2_OMEGA_LAMBDA_ERR,
    NAMED_BEST_FIT_PATH,
    OMEGA_LAMBDA_ERR_KEY,
    is_numeric,
    read_named_best_fit,
)

# Statistical-only uncertainty is ~0.013 (fixed M) or ~0.020 (marginalized M);
# switching to the systematics-inclusive covariance alone widens it to
# ~0.030, and to ~0.041 once M is also marginalized. This window catches
# "the systematics covariance was found" regardless of the magnitude
# treatment, while excluding both statistical-only cases.
LOWER, UPPER = LEVEL_2_OMEGA_LAMBDA_ERR


def test_named_best_fit_reports_systematics_level_uncertainty() -> None:
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"
    assert OMEGA_LAMBDA_ERR_KEY in record, (
        f"best_fit.json has no '{OMEGA_LAMBDA_ERR_KEY}' key: {sorted(record)}"
    )
    sigma = record[OMEGA_LAMBDA_ERR_KEY]
    assert is_numeric(sigma), f"{OMEGA_LAMBDA_ERR_KEY} is not numeric: {sigma!r}"
    assert LOWER <= sigma <= UPPER, f"{OMEGA_LAMBDA_ERR_KEY}={sigma} not in [{LOWER}, {UPPER}]"
