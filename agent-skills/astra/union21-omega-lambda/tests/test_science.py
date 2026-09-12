"""The science floor: did the agent produce the two deliverables at all.

This is the only *binary* science check. "Is the number right" and "is the
uncertainty right" are continuous and therefore cannot be pytest verdicts —
a pytest run is pass/fail, i.e. 0/1 — so they live in `score.py`, which
test.sh runs separately.

`test_deliverables` reads the named output contract strictly (contract.json,
via _util.read_named_best_fit) — no globbing, no key-name pattern matching.
"""

from __future__ import annotations

from _util import (
    NAMED_BEST_FIT_PATH,
    NAMED_FIGURE_PATH,
    OMEGA_LAMBDA_ERR_KEY,
    OMEGA_LAMBDA_KEY,
    is_numeric,
    read_named_best_fit,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_FIGURE_BYTES = 10_000


def test_deliverables() -> None:
    # Both prompts name exactly two files and exactly two JSON keys. This
    # dimension asks only whether they are there and readable: a numeric
    # value and a numeric uncertainty in the named JSON, and a figure that is
    # really a PNG and really decodes. Whether the numbers are *right* is
    # score.py's continuous business, not this test's.
    record = read_named_best_fit()
    assert record is not None, f"{NAMED_BEST_FIT_PATH} is missing or not valid JSON"

    for key in (OMEGA_LAMBDA_KEY, OMEGA_LAMBDA_ERR_KEY):
        assert key in record, f"best_fit.json has no '{key}' key: {sorted(record)}"
        assert is_numeric(record[key]), f"{key} is not numeric: {record[key]!r}"

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
