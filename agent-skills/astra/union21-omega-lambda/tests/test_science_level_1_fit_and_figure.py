from __future__ import annotations

from _util import find_omega_lambda_estimates, iter_png_files

# science_level 1: a working fit and a figure to show for it. Any legitimate
# combination of covariance and magnitude treatment lands here — this level
# only checks the cosmology fit itself is right and was actually run.
OMEGA_LOWER, OMEGA_UPPER = 0.690, 0.735

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_FIGURE_BYTES = 10_000


def test_recovered_omega_lambda_is_in_expected_range() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, "no best-fit record found"
    in_range = [omega for omega, _sigma, _path in estimates if OMEGA_LOWER <= omega <= OMEGA_UPPER]
    assert in_range, (
        f"no recorded Omega_Lambda estimate fell in [{OMEGA_LOWER}, {OMEGA_UPPER}]: "
        f"{[(o, str(p)) for o, _s, p in estimates]}"
    )


def test_figure_exists_and_is_a_valid_nontrivial_png() -> None:
    candidates = [path for path in iter_png_files() if path.stat().st_size > MIN_FIGURE_BYTES]
    assert candidates, f"no PNG over {MIN_FIGURE_BYTES} bytes found under the project"

    signed = [path for path in candidates if path.read_bytes()[:8] == PNG_SIGNATURE]
    assert signed, "no candidate PNG has a valid PNG file signature"

    import matplotlib.image as mpimg

    decoded = False
    last_error: Exception | None = None
    for path in signed:
        try:
            image = mpimg.imread(path)
        except Exception as error:  # noqa: BLE001 - report the most recent failure
            last_error = error
            continue
        if image.size > 0:
            decoded = True
            break
    assert decoded, f"no candidate PNG decoded to a non-empty image: {last_error}"
