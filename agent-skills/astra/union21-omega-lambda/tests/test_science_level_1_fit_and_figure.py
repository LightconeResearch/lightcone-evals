from __future__ import annotations

from _util import NAMED_FIGURE_PATH, read_named_best_fit

# science_level 1: a working fit and a figure to show for it, at the exact
# paths and keys the prompt asked for. Any legitimate combination of
# covariance and magnitude treatment lands here — this level only checks the
# cosmology fit itself is right and was actually run.
OMEGA_LOWER, OMEGA_UPPER = 0.690, 0.735

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_FIGURE_BYTES = 10_000


def test_named_best_fit_reports_omega_lambda_in_expected_range() -> None:
    record = read_named_best_fit()
    assert record is not None, "results/best_fit.json is missing or not valid JSON"
    assert "omega_lambda" in record, f"results/best_fit.json has no 'omega_lambda' key: {sorted(record)}"
    omega = record["omega_lambda"]
    assert isinstance(omega, (int, float)) and not isinstance(omega, bool), (
        f"omega_lambda is not numeric: {omega!r}"
    )
    assert OMEGA_LOWER <= omega <= OMEGA_UPPER, (
        f"omega_lambda={omega} not in [{OMEGA_LOWER}, {OMEGA_UPPER}]"
    )


def test_named_figure_exists_and_is_a_valid_nontrivial_png() -> None:
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
