#!/usr/bin/env python3
"""Fit Union2.1 distance moduli to flat LCDM, varying only Omega_Lambda."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

C_KM_S = 299_792.458
# The data file's header calibrates its absolute magnitude to h = 0.7; H0 is
# therefore held fixed rather than fit alongside Omega_Lambda.
H0_KM_S_MPC = 70.0

COVARIANCE_FILES = {
    "statistical_only": "covmat_nosys",
    "with_systematics": "covmat_sys",
}

MAGNITUDE_TREATMENTS = ("fixed", "marginalized")


def distance_modulus(redshift: np.ndarray, omega_l: float) -> np.ndarray:
    """Luminosity-distance modulus for a spatially flat matter+Lambda cosmology."""
    from scipy.integrate import quad

    omega_m = 1.0 - omega_l

    def inv_expansion_rate(z: float) -> float:
        return 1.0 / np.sqrt(omega_m * (1.0 + z) ** 3 + omega_l)

    comoving_integral = np.fromiter(
        (quad(inv_expansion_rate, 0.0, z, epsabs=1e-10, epsrel=1e-10)[0] for z in redshift),
        dtype=float,
        count=redshift.size,
    )
    luminosity_distance_mpc = (C_KM_S / H0_KM_S_MPC) * (1.0 + redshift) * comoving_integral
    return 5.0 * np.log10(luminosity_distance_mpc) + 25.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--covmat-nosys", required=True)
    parser.add_argument("--covmat-sys", required=True)
    parser.add_argument("--covariance", choices=sorted(COVARIANCE_FILES), required=True)
    parser.add_argument("--magnitude-treatment", choices=MAGNITUDE_TREATMENTS, required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    redshift, observed_mu, _statistical_error, _host_probability = np.loadtxt(
        args.data, comments="#", usecols=(1, 2, 3, 4), unpack=True
    )
    covariance_path = args.covmat_nosys if args.covariance == "statistical_only" else args.covmat_sys
    covariance = np.loadtxt(covariance_path)
    covariance_inverse = np.linalg.inv(covariance)
    marginalize_magnitude = args.magnitude_treatment == "marginalized"
    ones = np.ones(redshift.size)
    # E = 1^T C^-1 1 does not depend on Omega_Lambda; compute it once.
    normalization = float(ones @ covariance_inverse @ ones)

    def chi_squared(omega_l: float) -> float:
        residual = observed_mu - distance_modulus(redshift, omega_l)
        quadratic_form = float(residual @ covariance_inverse @ residual)
        if not marginalize_magnitude:
            return quadratic_form
        # Analytically marginalize over an additive absolute-magnitude offset
        # Delta_M with a flat prior: chi2_marg = A - B^2/E, where A is the
        # ordinary quadratic form, B = r^T C^-1 1, and E = 1^T C^-1 1. The
        # dropped normalization term ln(E / 2*pi) does not depend on
        # Omega_Lambda and so does not affect the best fit or its curvature.
        cross_term = float(residual @ covariance_inverse @ ones)
        return quadratic_form - cross_term**2 / normalization

    result = minimize_scalar(
        chi_squared, bounds=(0.001, 0.999), method="bounded", options={"xatol": 1e-10}
    )
    omega_l = float(result.x)
    chi2_min = float(result.fun)

    # 1-sigma uncertainty from the curvature of chi-squared at the minimum
    # (Delta chi^2 = 1 for a single free parameter).
    step = 1e-4
    second_derivative = (
        chi_squared(omega_l + step) - 2.0 * chi2_min + chi_squared(omega_l - step)
    ) / step**2
    omega_l_sigma = float(np.sqrt(2.0 / second_derivative))

    # Marginalizing over Delta_M analytically still spends a degree of
    # freedom on it, on top of the one spent fitting Omega_Lambda.
    degrees_of_freedom = int(redshift.size - 1 - int(marginalize_magnitude))
    summary = {
        "H0_km_s_Mpc": H0_KM_S_MPC,
        "Omega_L": omega_l,
        "Omega_L_sigma": omega_l_sigma,
        "Omega_m": 1.0 - omega_l,
        "chi_squared": chi2_min,
        "degrees_of_freedom": degrees_of_freedom,
        "reduced_chi_squared": chi2_min / degrees_of_freedom,
        "n_supernovae": int(redshift.size),
        "covariance": args.covariance,
        "covariance_file": Path(covariance_path).name,
        "magnitude_treatment": args.magnitude_treatment,
    }

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "best_fit.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
