# Data dictionary and metrics

[README](../README.md) | [Actual results walkthrough](RESULTS_GUIDE.md)

## Positive means a fault was detected

`truth` is the known actual condition: 1 for an injected defect and 0 for healthy.
`prediction` is the detector's decision: 1 for fault and 0 for healthy.
Positive does not mean that the API is working correctly.

| Actual condition | Detector says fault (1) | Detector says healthy (0) |
|---|---|---|
| Faulty (truth=1) | TP: True Positive. Correct detection. | FN: False Negative. Missed fault. |
| Healthy (truth=0) | FP: False Positive. False alarm. | TN: True Negative. Correct healthy decision. |

An injected HTTP 500 flagged by HTTP detection is TP. An internal audit failure
returning HTTP 200 and missed by HTTP alone is FN. A healthy trial flagged because
of an unexpected timeout would be FP. A healthy trial left unflagged is TN.

## n, NP, N/A, null and zero

| Notation | Meaning |
|---|---|
| n | Number of valid trials in that row: TP + TN + FP + FN |
| NP / np | Not a defined column or abbreviation in this project; it may be a misreading of n, FP, FN or N/A |
| np in other Python code | Often a NumPy alias; this project does not use or require NumPy |
| N/A in RESULTS.md | Undefined metric because its denominator is zero |
| Blank numeric cell in a metrics CSV | The same undefined metric |
| null in HTTP JSON | No HTTP status received, for example after timeout or connection failure |
| 0 | Actual numeric zero, not an undefined value |
| Empty error / transport_error text | No error of that particular kind recorded |

The always-healthy reference has undefined precision because it never raises an
alarm (TP + FP = 0). Its recall is zero: faults exist and all are missed. Do not
replace N/A with zero or treat it as an invalid trial.

## Metric definitions

Proportions range from 0 to 1: 0.8 means 80%. TP, TN, FP and FN count trials.

| Metric | Formula | Interpretation | Better direction |
|---|---|---|---|
| accuracy | (TP + TN) / n | Share of all decisions that are correct | Higher |
| precision | TP / (TP + FP) | Share of fault alarms that are real faults | Higher |
| recall | TP / (TP + FN) | Share of actual faults detected | Higher |
| specificity | TN / (TN + FP) | Share of healthy trials without a false alarm | Higher |
| FPR | FP / (FP + TN) | Share of healthy trials that trigger a false alarm | Lower |
| F1 | 2TP / (2TP + FP + FN) | Combined precision/recall performance | Higher |
| balanced_accuracy | (recall + specificity) / 2 | Equal-weight performance on faulty and healthy classes | Higher |

F1 is the harmonic mean of precision and recall where that expression is defined.
It does not include TN. Precision can be 100% while recall is low: every raised
alarm may be correct even though many other faults go undetected.

FPR is not 1 minus precision. FPR divides false alarms by actual healthy trials;
precision divides correct alarms by all raised alarms.

A zero denominator gives N/A. In fault-only scenario rows, specificity and FPR are
undefined because there are no healthy trials. Balanced accuracy is undefined
when either actual class is absent. With the implemented count formula, F1 is
undefined only when 2TP + FP + FN equals zero.

## Worked calculation from Marlen's HTTP row

The measured counts are n=20, TP=8, TN=10, FP=0, FN=2.

- Accuracy = (8 + 10) / 20 = 0.9 = 90%.
- Precision = 8 / (8 + 0) = 1 = 100%.
- Recall = 8 / (8 + 2) = 0.8 = 80%.
- Specificity = 10 / (10 + 0) = 1 = 100%.
- FPR = 0 / (0 + 10) = 0 = 0%.
- F1 = 16 / (16 + 0 + 2) = 0.888889, approximately 88.89%.
- Balanced accuracy = (0.8 + 1) / 2 = 0.9 = 90%.

HTTP correctly identified all ten healthy trials, detected eight of ten injected
faults, missed two audit failures and produced no false alarms in this pilot.

## Run-level evidence files

| File | Meaning |
|---|---|
| environment.json | UTC time, Python/Docker versions, platform, image metadata, operator, phase, protocol hash |
| protocol.json | Fixed rules, timeout, seed, scenarios, sample settings and limitations |
| source/ | Snapshot of the runner, API and Dockerfile before collection |
| schedule.json | Planned trial IDs, rounds, scenarios and truth labels |
| trials.csv | All attempted trials, validity and collection errors |
| journal.jsonl | One JSON record per trial, including start/end times and operator |
| completion.json | Planned/valid/invalid counts and completion time |
| manifest.sha256.json | Checksums of original evidence, used to detect edits |
| build.log | Build output copied when available |

Phase and operator are recorded labels, not automatic proof of experimental
validity or personal authorship. A checksum establishes file integrity, not the
scientific adequacy of the design.

## Trial and decision fields

| Field | Type | Meaning |
|---|---|---|
| trial | Text | ID such as T0006; unique within a run |
| round | Integer | Repetition number of the full 10-trial schedule |
| scenario | Category | One of the six protocol scenarios |
| truth | 0/1 | Actual healthy/faulty label |
| valid | True/False | Whether a usable observation set was collected |
| error | Text | Collection/infrastructure error; empty for a valid trial |
| condition | Text | Signals used, such as http+logs |
| prediction | 0/1 | Decision for that condition |
| http_positive | 0/1 | HTTP-only decision |
| container_positive | 0/1 | Container-only decision |
| logs_positive | 0/1 | Logs-only decision |

All three single-signal decisions are repeated in each of a trial's seven rows.
Each condition uses only its selected signals. A http-only row may contain
logs_positive=1, but that field does not affect the HTTP-only prediction.

valid=True does not mean healthy or correctly detected. A faulty API can yield a
valid trial and still be missed by a detector.

## Files inside raw/T0006/ or another trial directory

| File | Meaning |
|---|---|
| ground_truth.json | Trial, round, scenario and truth; unavailable to detectors |
| injection.json | Container ID, configured mode, stop request flag and record time |
| readiness.json | Startup probes to /ready; excluded from measured requests |
| http.json | Five measured requests to /api/items |
| container.json | Selected state snapshot after observations and before cleanup |
| application.jsonl | Actual JSON application log events from Docker |
| failure.json | Created if a collection error is caught; reason and UTC time |
| cleanup.json | Return code, stdout and stderr of removing the trial container |

In stopped_container, the API initially runs in healthy mode and is then stopped.
Thus mode=healthy in injection.json is consistent with that scenario. Check
stop_requested and the saved Running field too.

## HTTP fields

| Field | Meaning |
|---|---|
| request | Sequential request number within the trial, in CSV exports |
| timestamp_utc | Time measurement completed, in ISO 8601 UTC |
| status | Received HTTP status; null/blank when no status was received |
| elapsed_ms | Client time to a response or transport error, in milliseconds |
| body | Received response body; empty if unavailable |
| transport_error | Timeout/connection error; empty when HTTP transport succeeded |

HTTP 200 means the endpoint returned success, but audit functionality may still
have failed. HTTP 500 is the injected calculation failure. HTTP 503 is the injected
unavailable-service response. A timeout has no status and still triggers HTTP
detection. A 500 response can have an empty transport_error: the response arrived
successfully but reports an application failure.

After a timeout, elapsed_ms is the time the client waited, not the server's final
completion time. Observed times can slightly exceed 400 ms due to overhead.
The detector checks transport errors/status; it does not apply a separate numeric
latency threshold to elapsed_ms.

## Container and log fields

| Field | Meaning |
|---|---|
| Running | Whether the container process is running at the snapshot |
| OOMKilled | Whether Docker reports an out-of-memory kill |
| RestartCount | Number of restarts reported by Docker |
| Status | Text state such as running or exited |
| ExitCode | Process exit status; recorded but not used by the detector |
| Log time | Application event time, UTC |
| Log level | Severity such as INFO or ERROR |
| Log message | Application event description |
| Cleanup code | Return code of Docker removal; zero means the command succeeded |

Running=True does not imply a correct API. Logs detection checks ERROR or CRITICAL,
not scenario names. The current schedule injects no out-of-memory fault, even
though the state detector can observe that field.

## Raw versus processed files

raw/requests.csv is written during collection. It can include requests from a trial
that subsequently fails during state/log collection. processed/http_measurements.csv
contains valid trials only and adds scenario labels.

decisions.csv has one row per valid trial/condition. metrics.csv aggregates these
rows by condition. metrics_by_scenario.csv and metrics_by_round.csv subdivide the
same decisions; their counts must not be added to the aggregate counts as new data.

There is no imputation or deduplication. Repeated scenarios are intentional.
Invalid trials are excluded explicitly and retained with their error evidence.

## Time and interpretation limits

20261022T101634Z-23a61b identifies 22 October 2026 at 10:16:34 UTC, plus a random
suffix. This is 15:16:34 in Kazakhstan's UTC+5 timezone.

Requests within one trial are not independent experimental repetitions. Precision
and accuracy depend on the chosen fault mixture. Accuracy equals balanced accuracy
here because the classes are balanced, not because the formulas are identical.
OR combinations cannot reduce recall or reduce FPR relative to constituent
detectors on the same trials. That is a property of OR, not an empirical discovery.
The lab does not perform significance tests or make population-level claims.

## Added in protocol 2.0

| Field / file | Meaning |
|---|---|
| injection.json `trial_seed` | Seed string `<protocol seed>:<trial>` passed to the API; the container hostname is also mixed in |
| container.json `RestartCount` | Now meaningful: crash_restart is restarted by `--restart on-failure` |
| expectations.md (run folder) | Copy of the frozen expectations; its SHA-256 and modification time are in environment.json |
| `*_ci95` columns in metrics.csv | 95% Wilson score interval, written `low-high` |
| paired_vs_http.csv | For each configuration: trials only HTTP got right (b), trials only that configuration got right (c), exact two-sided McNemar p = min(1, 2·Σ_{i≤min(b,c)} C(b+c, i) / 2^(b+c)) |

Wilson interval for k successes out of n, z = 1.96:
centre = (p + z²/2n) / (1 + z²/n), half-width = z·√(p(1−p)/n + z²/4n²) / (1 + z²/n).
