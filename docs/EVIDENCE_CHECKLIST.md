# Evidence and handover checklist

[Back to README](../README.md)

This checklist identifies technical artefacts for the team. It does not replace
the assignment text. Use actual files from a named run and explain their origin.

## Files to hand over

| Evidence | Files or actions |
|---|---|
| Environment | doctor output, environment.json, Dockerfile, image ID and build log |
| Reproducible method | protocol.json, scenarios, rules, seed, repetitions and limitations |
| Working instrument | app/server.py, lab.py, Dockerfile and run_pilot.ps1 |
| Pilot execution | Full selected runs/pilot folder, including journal and all trials |
| Original measurements | raw/, trials.csv and raw/requests.csv |
| Derived results | processed/ tables, decisions, summary and accuracy chart |
| Plan versus collection | completion.json; explain any invalid trials or interruptions |
| Procedure changes | Dated notes describing actual changes and reasons |
| Expectations | Team's honestly dated expectations and falsification criteria |
| Public accessibility | Open cloud/repository links tested without requesting access |

Keep all runs you report, not just the best one. Share entire selected run
folders so that someone can trace decisions to raw observations. Preserve the
original code snapshots and manifests. Operator labels in environment.json are
part of the recorded evidence and are never edited.

The assignment requests six outcome scenarios: two bad, two medium and two good.
It also requests numbered, captioned figures referenced in the text. These are
report tasks; the measurement code does not manufacture expectations or references.

## Five suggested illustrations of your own study

1. Architecture of this actual setup: runner -> Docker API -> HTTP/state/logs -> CSV.
2. Your Dockerfile and a real running trial container in Docker Desktop.
3. A complete pilot run in the terminal, including date/context and output folder.
4. One trial's HTTP response, container state and application log side by side.
5. Your measured CSV results or the generated accuracy.svg chart.

The runner removes temporary containers after saving observations, so capture a
running-container screenshot while collection is in progress. Do not invent a
screenshot or modify observations to make the display look more successful.

Every report figure needs a number, a caption explaining what it demonstrates,
and at least one reference from the text. A diagram or chart does not by itself
prove that an experiment actually ran; use it alongside logs and raw measurements.

## Repository and report preparation

- Explain self-developed code and adaptations accurately.
- Link methodological choices to sources you actually read in A2.
- Keep the original/replication declaration consistent with what was done.
- Explain that this fixed-rule study has no human participants or ML training.
- Use Block D as the primary technical-study block and relevant experiment items
  from C; confirm the instructor's preferred treatment where the blocks overlap.
- Explain N/A entries rather than silently leaving required explanations blank.
- Preserve expectations as originally dated; the existing pilot has already been seen.
- Include limitations: synthetic faults, one API, local environment and limited repetitions.
- Upload the selected evidence and check public links in a private browser window.
- Keep links available through the required examination period.

The scripts do not upload files, publish a repository or write the assignment.
