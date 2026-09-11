from __future__ import annotations

from _util import find_omega_lambda_estimates, iter_png_files

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_FIGURE_BYTES = 10_000


def test_best_fit_artifact_exists_and_is_machine_readable() -> None:
    estimates = find_omega_lambda_estimates()
    assert estimates, (
        "no JSON or YAML file under the project carried a field that looks like "
        "an Omega_Lambda best-fit value"
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
