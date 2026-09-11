"""The three science dimensions, each independent and each 0/1.

They are nested *in fact* — any run inside the paper windows is also inside
the fit-and-figure and systematics windows — but nothing here enforces the
nesting, and test.sh runs all three unconditionally. A run that reproduces
the paper's numbers but wrote no figure scores paper_reproduced=1 with
fit_and_figure=0; that is information about the run, not an inconsistency.

All three read the named output contract strictly (contract.json, via
_util.read_named_best_fit) — no globbing, no key-name pattern matching.
"""

from __future__ import annotations

from _util import (
    FIT_AND_FIGURE_OMEGA_LAMBDA,
    NAMED_BEST_FIT_PATH,
    NAMED_FIGURE_PATH,
    OMEGA_LAMBDA_ERR_KEY,
    OMEGA_LAMBDA_KEY,
    PAPER_OMEGA_LAMBDA,
    PAPER_OMEGA_LAMBDA_ERR,
    SYSTEMATICS_OMEGA_LAMBDA_ERR,
    is_numeric,
    read_named_best_fit,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_FIGURE_BYTES = 10_000


def test_fit_and_figure() -> None:
    # A working fit and a figure to show for it, at the exact paths and keys
    # the prompt asked for. Any legitimate combination of covariance and
    # magnitude treatment lands in this window — this dimension only checks
    # the cosmology fit itself is right and was actually run.
    lower, upper = FIT_AND_FIGURE_OMEGA_LAMBDA
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"
    assert OMEGA_LAMBDA_KEY in record, (
        f"best_fit.json has no '{OMEGA_LAMBDA_KEY}' key: {sorted(record)}"
    )
    omega = record[OMEGA_LAMBDA_KEY]
    assert is_numeric(omega), f"{OMEGA_LAMBDA_KEY} is not numeric: {omega!r}"
    assert lower <= omega <= upper, f"{OMEGA_LAMBDA_KEY}={omega} not in [{lower}, {upper}]"

    assert NAMED_FIGURE_PATH.is_file(), f"{NAMED_FIGURE_PATH} does not exist"
    assert NAMED_FIGURE_PATH.stat().st_size > MIN_FIGURE_BYTES, (
        f"{NAMED_FIGURE_PATH} is only {NAMED_FIGURE_PATH.stat().st_size} bytes"
    )
    assert NAMED_FIGURE_PATH.read_bytes()[:8] == PNG_SIGNATURE, (
        f"{NAMED_FIGURE_PATH} does not have a valid PNG signature"
    )

    import matplotlib.image as mpimg

    image = mpimg.imread(NAMED_FIGURE_PATH)
    assert image.size > 0, f"{NAMED_FIGURE_PATH} decoded to an empty image"


def test_systematics_covariance() -> None:
    # Statistical-only uncertainty is ~0.013 (fixed M) or ~0.020
    # (marginalized M); switching to the systematics-inclusive covariance
    # alone widens it to ~0.030, and to ~0.041 once M is also marginalized.
    # This window catches "the systematics covariance was found" regardless
    # of the magnitude treatment, while excluding both statistical-only cases.
    lower, upper = SYSTEMATICS_OMEGA_LAMBDA_ERR
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"
    assert OMEGA_LAMBDA_ERR_KEY in record, (
        f"best_fit.json has no '{OMEGA_LAMBDA_ERR_KEY}' key: {sorted(record)}"
    )
    sigma = record[OMEGA_LAMBDA_ERR_KEY]
    assert is_numeric(sigma), f"{OMEGA_LAMBDA_ERR_KEY} is not numeric: {sigma!r}"
    assert lower <= sigma <= upper, f"{OMEGA_LAMBDA_ERR_KEY}={sigma} not in [{lower}, {upper}]"


def test_paper_reproduced() -> None:
    # Suzuki et al. 2012 published Omega_Lambda = 0.705 (+0.040, -0.043).
    # Full reproduction needs both seeded defects found together: the
    # systematics covariance (widens sigma) and analytic marginalization
    # over the SN absolute magnitude (widens it further, to ~0.041). Reading
    # a single named file for both keys makes "same estimate" structural.
    omega_lower, omega_upper = PAPER_OMEGA_LAMBDA
    sigma_lower, sigma_upper = PAPER_OMEGA_LAMBDA_ERR
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"
    omega = record.get(OMEGA_LAMBDA_KEY)
    sigma = record.get(OMEGA_LAMBDA_ERR_KEY)
    assert is_numeric(omega), f"{OMEGA_LAMBDA_KEY} is not numeric: {omega!r}"
    assert is_numeric(sigma), f"{OMEGA_LAMBDA_ERR_KEY} is not numeric: {sigma!r}"
    assert omega_lower <= omega <= omega_upper, (
        f"{OMEGA_LAMBDA_KEY}={omega} not in [{omega_lower}, {omega_upper}]"
    )
    assert sigma_lower <= sigma <= sigma_upper, (
        f"{OMEGA_LAMBDA_ERR_KEY}={sigma} not in [{sigma_lower}, {sigma_upper}]"
    )
