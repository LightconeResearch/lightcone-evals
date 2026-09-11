from __future__ import annotations

from _util import read_named_best_fit

# Statistical-only uncertainty is ~0.013 (fixed M) or ~0.020 (marginalized M);
# switching to the systematics-inclusive covariance alone widens it to
# ~0.030, and to ~0.041 once M is also marginalized. This window catches
# "the systematics covariance was found" regardless of the magnitude
# treatment, while excluding both statistical-only cases.
LOWER, UPPER = 0.025, 0.050


def test_named_best_fit_reports_systematics_level_uncertainty() -> None:
    record = read_named_best_fit()
    assert record is not None, "results/best_fit.json is missing or not valid JSON"
    assert "omega_lambda_err" in record, (
        f"results/best_fit.json has no 'omega_lambda_err' key: {sorted(record)}"
    )
    sigma = record["omega_lambda_err"]
    assert isinstance(sigma, (int, float)) and not isinstance(sigma, bool), (
        f"omega_lambda_err is not numeric: {sigma!r}"
    )
    assert LOWER <= sigma <= UPPER, f"omega_lambda_err={sigma} not in [{LOWER}, {UPPER}]"
