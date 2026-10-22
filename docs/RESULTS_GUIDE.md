# Walkthrough of the measured pilot results

[README](../README.md) | [Metric definitions](DATA_AND_METRICS.md)

## Which collection is described?

This guide describes the completed pilot stored in
`runs/pilot/20261022T101634Z-23a61b`, with recorded operator **Marlen**.
It contains 20 valid trials, zero invalid trials and 100 measured HTTP requests.
The earlier automated pilot has the same aggregate metrics but remains a separate
collection. Do not pool the two silently or treat seven signal configurations as
seven independent experiments.

The directly traceable source is
[metrics.csv](../runs/pilot/20261022T101634Z-23a61b/processed/metrics.csv).
The compact report is
[RESULTS.md](../runs/pilot/20261022T101634Z-23a61b/processed/RESULTS.md).

## Every aggregate row explained

All rows below score the same 20 trials: ten healthy and ten faulty.
Positive means fault. Counts are trials, not requests.

| Configuration | TP | TN | FP | FN | Accuracy | Recall | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| http | 8 | 10 | 0 | 2 | 90% | 80% | Finds four of the five fault types; misses internal audit failures |
| container | 2 | 10 | 0 | 8 | 60% | 20% | Finds stopped containers; misses faults inside a still-running process |
| logs | 4 | 10 | 0 | 6 | 70% | 40% | Finds the exception and audit failures that emit ERROR |
| http+container | 8 | 10 | 0 | 2 | 90% | 80% | Adds no detections to HTTP in this dataset because stopped-container failures already break HTTP |
| http+logs | 10 | 10 | 0 | 0 | 100% | 100% | HTTP finds externally visible problems; logs add the internal audit failure |
| container+logs | 6 | 10 | 0 | 4 | 80% | 60% | Finds stopped containers, exceptions and audit failures; misses silent 503 and slow response |
| http+container+logs | 10 | 10 | 0 | 0 | 100% | 100% | Same detections as HTTP+logs in this dataset |
| always_healthy_reference | 0 | 10 | 0 | 10 | 50% | 0% | Gets every healthy trial right and misses every fault by construction |

Precision is 100% for all seven actual configurations because none produced a
false alarm. This does not make them equally useful: container-only misses eight
faults, while HTTP+logs misses none in this pilot. The always-healthy reference
has N/A precision because it never predicts a fault at all.

## Which signals saw each scenario?

Each fault scenario was repeated twice. The healthy scenario has ten trials.
The entries describe the observed single-source decisions in this pilot:

| Scenario | Truth | HTTP predicts fault | Container predicts fault | Logs predict fault |
|---|---:|---|---|---|
| healthy | 0 | No | No | No |
| exception | 1 | Yes | No | Yes |
| silent_http_error | 1 | Yes | No | No |
| background_error | 1 | No | No | Yes |
| slow_response | 1 | Yes | No | No |
| stopped_container | 1 | Yes | Yes | No |

For healthy trials, No is correct (TN). For faulty trials, Yes is correct (TP)
and No means a miss (FN). These observations explain the aggregate counts. For
example, HTTP misses background_error twice, giving FN=2.

The faults were designed to differ in observability. These results show how the
fixed rules behave on this synthetic setup; they do not establish universal
superiority or reliability on production systems. In particular, container state
added no new detections to HTTP+logs here. It may still be informative in a
different, independently specified experiment.

## Trace one missed fault from source to metric

Use trial T0006 in the Marlen run:

1. Open `raw/T0006/ground_truth.json`: scenario is background_error and truth is 1.
2. Open `raw/T0006/http.json`: the five responses have status 200.
3. Open `raw/T0006/container.json`: the process is still running.
4. Open `raw/T0006/application.jsonl`: ERROR events record failed audit writes.
5. In `processed/decisions.csv`, filter trial=T0006.
6. The http row has prediction=0 while truth=1: one FN for HTTP.
7. The logs and http+logs rows have prediction=1: one TP for each configuration.

You can filter these rows directly in PowerShell:

```powershell
cd <project folder>
Import-Csv .\runs\pilot\20261022T101634Z-23a61b\processed\decisions.csv |
    Where-Object { $_.trial -eq 'T0006' } |
    Format-Table trial, scenario, condition, truth, prediction, http_positive, container_positive, logs_positive
```

A second audit-failure trial supplies the second HTTP FN. Nothing is inferred from
a screenshot alone: the raw observations and decision rows let a reader check it.

## Read the remaining output files

| Output | How to interpret it |
|---|---|
| metrics_by_round.csv | Each condition has n=10 in each of the two rounds; use to compare repeatability |
| metrics_by_scenario.csv | Healthy rows have n=10; each fault-type row has n=2; undefined metrics are expected when a class is absent |
| decisions.csv | 140 rows: seven condition decisions for each of 20 trials |
| http_measurements.csv | 100 valid measured requests; elapsed_ms is response/error waiting time, not detection accuracy |
| accuracy.svg | Visualizes aggregate accuracy only; it does not display uncertainty, recall, or timing |
| completion.json | Confirms planned=20, valid=20, invalid=0; not a detector score |
| trials.csv | Confirms collection success; valid=True does not mean healthy or correctly detected |
| journal.jsonl | Records when each trial was run and the operator label |

Example: logs-only for silent_http_error has n=2, TP=0 and FN=2. Recall is 0, but
specificity and FPR are undefined because that subgroup contains no healthy trials.
A blank subgroup metric is therefore not evidence that data was lost.

## What 100% does and does not establish

HTTP+logs and all-three correctly classified all 20 trials in this pilot. That is
a measured result for this particular balanced set, API and fixed rules. It does
not mean all possible faults are detectable, that false alarms never occur, or
that the study measured human skill. Report both counts and the sample size.

The experiment does not measure root-cause localization accuracy: a correct
binary fault alarm does not show that the detector identified the exact cause.
It also does not compare detection speed; elapsed_ms is HTTP request timing.

## Before a future main run

Keep this pilot as pilot evidence. Choose and document the next protocol and
sample size before the next collection. If expectations were not written before
this pilot, record that fact instead of backdating them. New expectations informed
by the pilot must be described as such. A main run is not created by renaming an
existing pilot directory.

# Protocol 2.0 pilot (run 20261022T183629Z-157c1c)

28 valid trials (14 healthy, 14 faulty: two of each of seven fault types), 140 requests,
macOS arm64. Expectations were frozen at 18:35:51 UTC, before this run started at 18:36:29.

| Configuration | TP | TN | FP | FN | Accuracy | Recall | FPR |
|---|---:|---:|---:|---:|---:|---:|---:|
| http | 12 | 13 | 1 | 2 | 0.893 | 0.857 | 0.071 |
| container | 4 | 14 | 0 | 10 | 0.643 | 0.286 | 0.000 |
| logs | 8 | 10 | 4 | 6 | 0.643 | 0.571 | 0.286 |
| http+container | 12 | 13 | 1 | 2 | 0.893 | 0.857 | 0.071 |
| http+logs | 14 | 9 | 5 | 0 | 0.821 | 1.000 | 0.357 |
| container+logs | 11 | 10 | 4 | 3 | 0.750 | 0.786 | 0.286 |
| http+container+logs | 14 | 9 | 5 | 0 | 0.821 | 1.000 | 0.357 |
| always_healthy_reference | 0 | 14 | 0 | 14 | 0.500 | 0.000 | 0.000 |

Unlike 1.0, false alarms now occur: one healthy trial (T0021) had a latency spike
that hit the timeout (HTTP FP), and four healthy trials logged a benign ERROR line
(logs FP). Adding logs to HTTP found the two background_error faults but added four
false alarms, so accuracy fell from 0.893 to 0.821. With n=28 every interval is wide
(HTTP accuracy 95% CI 0.73–0.96) and no paired difference against HTTP is clear
except container-only being worse (exact McNemar p=0.039). These are pilot numbers;
the expectations are tested on the main run.

Caution about log "detections": in slow_response T0015 and crash_restart T0005 the
logs detector fired only because of a benign noise line, not because of the fault.
The binary rule counts these as TP. Read metrics_by_scenario.csv with this in mind.
