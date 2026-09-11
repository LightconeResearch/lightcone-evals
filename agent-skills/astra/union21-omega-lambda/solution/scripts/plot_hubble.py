#!/usr/bin/env python3
"""Two-panel Union2.1 Hubble diagram: distance modulus and residuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad

C_KM_S = 299_792.458


def distance_modulus(redshift: np.ndarray, h0: float, omega_l: float) -> np.ndarray:
    omega_m = 1.0 - omega_l

    def inv_expansion_rate(z: float) -> float:
        return 1.0 / np.sqrt(omega_m * (1.0 + z) ** 3 + omega_l)

    comoving_integral = np.fromiter(
        (quad(inv_expansion_rate, 0.0, z, epsabs=1e-10, epsrel=1e-10)[0] for z in redshift),
        dtype=float,
        count=redshift.size,
    )
    luminosity_distance_mpc = (C_KM_S / h0) * (1.0 + redshift) * comoving_integral
    return 5.0 * np.log10(luminosity_distance_mpc) + 25.0


def load_fit(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--fit", required=True, help="path to the fit's output JSON file")
    parser.add_argument("--output", required=True, help="path to the output PNG file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fit = load_fit(args.fit)
    redshift, observed_mu, statistical_error, _host_probability = np.loadtxt(
        args.data, comments="#", usecols=(1, 2, 3, 4), unpack=True
    )
    h0 = float(fit["h0_km_s_mpc"])
    omega_l = float(fit["omega_lambda"])
    model_mu = distance_modulus(redshift, h0, omega_l)

    z_curve = np.linspace(float(redshift.min()), float(redshift.max()), 400)
    mu_curve = distance_modulus(z_curve, h0, omega_l)

    figure, (top, bottom) = plt.subplots(
        2,
        1,
        figsize=(7.2, 6.6),
        sharex=True,
        height_ratios=[3, 1],
        constrained_layout=True,
    )
    top.errorbar(
        redshift,
        observed_mu,
        yerr=statistical_error,
        fmt=".",
        color="#377eb8",
        alpha=0.5,
        markersize=3,
        elinewidth=0.5,
        label=f"Union2.1 ({redshift.size} SNe Ia)",
    )
    top.plot(
        z_curve,
        mu_curve,
        color="#e41a1c",
        linewidth=2,
        label=rf"Flat $\Lambda$CDM: $\Omega_\Lambda={omega_l:.3f}$ ($H_0={h0:.0f}$)",
    )
    top.set_ylabel("Distance modulus μ")
    top.set_title("Union2.1 Hubble diagram")
    top.grid(alpha=0.2)
    top.legend(frameon=False)

    bottom.errorbar(
        redshift,
        observed_mu - model_mu,
        yerr=statistical_error,
        fmt=".",
        color="#377eb8",
        alpha=0.5,
        markersize=3,
        elinewidth=0.5,
    )
    bottom.axhline(0.0, color="#e41a1c", linewidth=1.5)
    bottom.set_xlabel("Redshift z")
    bottom.set_ylabel("Residual μ")
    bottom.grid(alpha=0.2)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
