Use lightcone-cli for this task.

Please finish the supplied supernova analyses and leave a reproducible handoff.
The projects are in /root/snae-natural. Their scientific methods and scripts are
already supplied; this is execution work, not a request to redesign the analysis.

In new-analysis, I only need the Hubble diagram and the fit it depends on.
Leave the other products unbuilt for now.

In updated-analysis, the uncertainty treatment has already been changed to use
statistical uncertainties only. Bring the results into agreement with that choice,
reusing anything that is still valid rather than rebuilding unrelated products.

In interrupted-analysis, a measurement was corrected, but the subsequent update
failed. Repair the execution problem and finish the update without undoing the
corrected data or changing the scientific method. Preserve the work that already
succeeded and keep earlier results recoverable.

Create a separate reproducible copy of updated-analysis at
/root/snae-natural/reproduced-analysis. Rebuild all its outputs there from the
project's tracked inputs and recorded environment, without copying generated
results or an installed environment from another project. The rebuilt outputs
should match the updated original. Prepare the original updated-analysis for
publication under CC-BY-4.0, including its machine-readable publication metadata.

Keep the requested analysis settings, input data, and scientific scripts intact except
for the execution repair. Use the projects' normal isolated execution and
provenance mechanisms, leave the finished repositories clean, and briefly
summarize what you completed and anything that remains unresolved.
