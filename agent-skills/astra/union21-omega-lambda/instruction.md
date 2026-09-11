I've put the Union2.1 Type Ia supernova compilation from the Supernova Cosmology Project in `/root/sn-cosmology/data/` — `SCPUnion2.1_mu_vs_z.txt`, plus the two covariance matrices the SCP publishes alongside it, `SCPUnion2.1_covmat_nosys.txt` and `SCPUnion2.1_covmat_sys.txt`.

Set this up as an ASTRA analysis in `/root/sn-cosmology`: fit a flat ΛCDM model to the distance moduli to recover Omega_Lambda, varying only Omega_Lambda and taking the rest of the cosmology from what the data file's header tells you. Two outputs: the best fit, and a downstream two-panel Hubble diagram — distance modulus with the best-fit curve, residuals below. Write the scripts the analysis calls, run them, and put the results somewhere sensible.

Then check us against the paper that published this catalogue, Suzuki et al. 2012 (arXiv 1105.3470, DOI 10.48550/arXiv.1105.3470) — it's already cached locally. Record their own Omega_Lambda constraint in the spec as a prior insight, with the quote as evidence so the claim is checkable.

Compare our uncertainty to theirs. If it doesn't look comparable, work out why, record the choice you make about it in the spec, and tell me what it does to the constraint.
