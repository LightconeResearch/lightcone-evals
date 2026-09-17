#!/usr/bin/env python3
"""Bootstrap flat-LCDM fits for Union2.1 with process-level parallelism."""

from __future__ import annotations

import argparse
import io
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from artifacts import write_archive
from cosmology import distance_modulus, effective_error, load_union21, selection_mask
from scipy.optimize import minimize

SCALE_SAMPLES = {"pilot": 200, "production": 20_000}
_WORKER_DATA: tuple[np.ndarray, np.ndarray, np.ndarray, str] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--optimizer", choices=("nelder_mead", "l_bfgs_b"), required=True
    )
    parser.add_argument(
        "--error-model", choices=("stat_only", "stat_and_sys"), required=True
    )
    parser.add_argument("--redshift-cut", choices=("none", "z_min_001"), required=True)
    parser.add_argument("--scale", choices=tuple(SCALE_SAMPLES), required=True)
    parser.add_argument("--workers", type=int, required=True)
    return parser.parse_args()


def initialize_worker(
    redshift: np.ndarray,
    observed_mu: np.ndarray,
    sigma_mu: np.ndarray,
    optimizer: str,
) -> None:
    global _WORKER_DATA
    _WORKER_DATA = (redshift, observed_mu, sigma_mu, optimizer)


def fit_resample(seed: int) -> tuple[float, float]:
    if _WORKER_DATA is None:
        raise RuntimeError("Bootstrap worker was not initialized")
    redshift, observed_mu, sigma_mu, optimizer = _WORKER_DATA
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, redshift.size, size=redshift.size)
    z = redshift[indices]
    mu = observed_mu[indices]
    sigma = sigma_mu[indices]

    def chi_squared(parameters: np.ndarray) -> float:
        h0, omega_l = parameters
        if not 40.0 <= h0 <= 100.0 or not 0.001 <= omega_l <= 0.999:
            return float("inf")
        model_mu = distance_modulus(z, float(h0), float(omega_l))
        return float(np.sum(np.square((mu - model_mu) / sigma)))

    method = "Nelder-Mead" if optimizer == "nelder_mead" else "L-BFGS-B"
    result = minimize(
        chi_squared,
        x0=np.array([70.0, 0.7]),
        method=method,
        bounds=((40.0, 100.0), (0.001, 0.999)),
        options={"maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(str(result.message))
    return float(result.x[0]), float(result.x[1])


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be positive")

    redshift, observed_mu, statistical_error, _ = load_union21(args.data)
    keep = selection_mask(redshift, args.redshift_cut)
    redshift = redshift[keep]
    observed_mu = observed_mu[keep]
    sigma_mu = effective_error(statistical_error[keep], args.error_model)

    sample_count = SCALE_SAMPLES[args.scale]
    seeds = np.random.SeedSequence(20260811).generate_state(sample_count).tolist()
    with ProcessPoolExecutor(
        max_workers=args.workers,
        initializer=initialize_worker,
        initargs=(redshift, observed_mu, sigma_mu, args.optimizer),
    ) as pool:
        fits = np.asarray(list(pool.map(fit_resample, seeds, chunksize=8)))

    percentiles = (2.5, 16.0, 50.0, 84.0, 97.5)
    h0_percentiles = np.percentile(fits[:, 0], percentiles)
    omega_l_percentiles = np.percentile(fits[:, 1], percentiles)
    summary = {
        "bootstrap_samples": sample_count,
        "workers": args.workers,
        "optimizer": args.optimizer,
        "error_model": args.error_model,
        "redshift_cut": args.redshift_cut,
        "percentile_levels": list(percentiles),
        "H0_km_s_Mpc": h0_percentiles.tolist(),
        "Omega_L": omega_l_percentiles.tolist(),
    }

    samples_csv = io.StringIO()
    np.savetxt(
        samples_csv,
        fits,
        delimiter=",",
        header="H0_km_s_Mpc,Omega_L",
        comments="",
    )

    write_archive(
        args.output,
        {
            "bootstrap_intervals.json": json.dumps(summary, indent=2, sort_keys=True)
            + "\n",
            "bootstrap_samples.csv": samples_csv.getvalue(),
        },
    )


if __name__ == "__main__":
    main()
