The Union2.1 Type Ia supernova compilation from the Supernova Cosmology Project is in `/root/sn-cosmology/data/` — `SCPUnion2.1_mu_vs_z.txt`, plus the two covariance matrices the SCP publishes alongside it, `SCPUnion2.1_covmat_nosys.txt` and `SCPUnion2.1_covmat_sys.txt`.

Use it to measure the dark energy density: fit a flat ΛCDM model to the distance moduli for Omega_Lambda. I want the constraint, and a two-panel Hubble diagram — distance modulus with the best-fit curve, residuals below. Save the constraint to `/root/sn-cosmology/results/best_fit.json` with keys `omega_lambda` and `omega_lambda_err` (the 1σ uncertainty), and the figure to `/root/sn-cosmology/results/hubble_diagram.png`.

Then reproduce the constraint the paper that published this catalogue reports for these supernovae alone — Suzuki et al. 2012, arXiv 1105.3470. Get as close to their value *and* their uncertainty as you can, and tell me what you had to do to get there and where you still differ.
