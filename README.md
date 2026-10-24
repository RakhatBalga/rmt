# RMT A3: Containerized API Fault-Detection Lab (protocol 2.0)

Team ZhumagulovMarlen_BalgabekovRakhat, group SE-2424.

This project contains the experiment code, real pilot observations and instructions
for reproducing the measurements. The Assignment 3 report is a separate document.

Research question: **How accurately can injected faults in a containerized Web API
be detected from HTTP responses, container state and application logs, used
separately and in combination?**

## Start here

| Your task | Documentation |
|---|---|
| Run the experiment | Follow this README |
| Understand n, TP, TN, FP, FN, N/A and formulas | [Data and metrics](docs/DATA_AND_METRICS.md) |
| Understand the actual results, row by row | [Results walkthrough](docs/RESULTS_GUIDE.md) |
| See what was done, when, by whom | [Research log](docs/RESEARCH_LOG.md) |
| Read the frozen expectations | [Expected results v2](expectations/EXPECTED_RESULTS_v2.md) |
| Prepare screenshots and hand over files | [Evidence checklist](docs/EVIDENCE_CHECKLIST.md) |
| Review the Docker setup history | [Setup notes](docs/SETUP_NOTES.md) |
| Dataset card, data dictionary and citation | [Section 9](#9-dataset) |
| Literature the design is based on | [Section 10](#10-references) |

## Runs present (22 October 2026)

| Folder under runs/pilot/ | Protocol | Machine | Valid trials | Requests |
|---|---|---|---:|---:|
| 20261022T100815Z-3082e0 | 1.0 | Windows 11 PC, Docker 29.9.2 | 20 | 100 |
| 20261022T101634Z-23a61b | 1.0 | Windows 11 PC, Docker 29.9.2 | 20 | 100 |
| 20261022T183629Z-157c1c | 2.0 | macOS arm64 laptop, Docker 29.4.3 | 28 | 140 |

| Folder under runs/main/ | Protocol | Machine | Valid trials | Requests (valid trials) |
|---|---|---|---:|---:|
| 20261022T190115Z-b15df2 | 2.0 | macOS arm64 laptop, Docker 29.4.3 | 139 of 140 | 695 |

The runs are separate datasets, not one pooled sample. The main run has one invalid
trial (T0125): two log lines written at the same moment by two server threads were
joined on one line, so the log file could not be parsed. It is excluded and reported,
not replaced (see docs/RESULTS_GUIDE.md).

**Why protocol 2.0 exists.** Both 1.0 pilots gave identical results: every fault type
was built to be visible to a fixed set of detectors, and healthy responses (max 43 ms)
could never reach the 400 ms timeout, so a false alarm was impossible. Protocol 2.0
keeps the detector rules unchanged but adds environmental noise to every mode
(rare latency spikes, benign ERROR log lines) and two faults whose visibility is not
fixed (intermittent_exception, crash_restart). Expectations for 2.0 were frozen in
`expectations/EXPECTED_RESULTS_v2.md` before the 2.0 pilot; the run records the file's
SHA-256 and modification time in `environment.json`.

## 1. Check the environment

Requirements: Python 3.10+, Docker CLI on PATH, Docker running Linux containers.
No pip packages, database, cloud account or API key are needed.

```text
python lab.py doctor          # Windows PowerShell
python3 lab.py doctor         # macOS / Linux
```

A successful check ends with `READY: Linux Docker engine responds.`

## 2. Run the full pilot with one script

Windows: `.\run_pilot.ps1`. macOS/Linux: `./run_pilot.sh`. Enter the real operator name
when asked. The script checks Docker, builds the image, collects two rounds,
analyzes them and prints the results path.

A progress line such as `T0005 crash_restart: collected` means usable measurements
were recorded. It does not mean the API was healthy or that a detector was right.

## 3. Run the steps manually

```text
python lab.py doctor
python -m unittest discover -s tests -v
python lab.py build
python lab.py collect --phase pilot --rounds 2 --operator "Marlen"
python lab.py analyze "<RUN DIRECTORY printed by collect>"
```

Tests should finish with `OK` (7 tests). The build creates image `rmt-a3-api:2.0`.
`collect` refuses to start if the expectations file named in `protocol.json` is missing.

| Argument | Meaning |
|---|---|
| `--phase pilot` / `--phase main` | Store under runs/pilot/ or runs/main/; the method is the same |
| `--rounds 2` | Repeat the complete 14-trial schedule twice |
| `--operator "..."` | Who starts the run; not a participant or detector |

Protocol 1.0 runs must be analyzed with their own preserved analyzer:

```text
python runs/pilot/20261022T101634Z-23a61b/source/lab.py analyze runs/pilot/20261022T101634Z-23a61b
```

## 4. Results files (inside each run's processed/ folder)

| File | Purpose |
|---|---|
| RESULTS.md | Readable summary, confidence intervals, paired comparison; start here |
| metrics.csv | All metrics per configuration, with 95% Wilson intervals |
| paired_vs_http.csv | Discordant trials vs the HTTP baseline and exact McNemar p (2.0 only) |
| metrics_by_scenario.csv | Which fault types each detector misses |
| metrics_by_round.csv | Results for each repetition |
| decisions.csv | Each trial's decision for all seven signal configurations |
| http_measurements.csv | Measured requests from valid trials with scenario labels |
| accuracy.svg | Accuracy chart |

## 5. Requests, trials, rounds and runs

- A request is one measured call to `/api/items`.
- A trial uses a fresh container and five measured requests.
- A round (2.0) contains seven healthy trials plus one of each of seven fault types.
- A run is one invocation of `collect`, with its own output folder.

The analysis unit is a trial. Requests inside a trial are not independent observations.

## 6. What the experiment does (protocol 2.0)

| Scenario | Actual action |
|---|---|
| healthy | HTTP 200 with an item list (plus the noise below) |
| exception | Division by zero, ERROR log, HTTP 500 on every request |
| silent_http_error | HTTP 503 without an ERROR log |
| background_error | Simulated audit-write failure, ERROR log, HTTP 200 kept |
| slow_response | Handler delayed 1 s; client timeout 0.4 s |
| stopped_container | Readiness confirmed, then container stopped before measured requests |
| intermittent_exception | Each request fails with HTTP 500 + ERROR with probability 0.35 |
| crash_restart | Process exits without a log line 0.05–0.5 s after the first request; Docker restarts it |

Noise in every mode: base delay 5–50 ms; latency spike with probability 0.04 per
request (extra 0.25–0.60 s, so about 2.6% of requests time out); benign
`ERROR Upstream cache timeout; served from fallback` with probability 0.05 per request.

| Detector | Fault rule (unchanged from 1.0) |
|---|---|
| HTTP | Any measured request has a transport error or status >=400 |
| Container | Running is false, OOMKilled is true, or RestartCount >0 |
| Logs | Any application JSON log entry has level ERROR or CRITICAL |
| Combined | OR of the selected detectors |

HTTP alone is the baseline. `always_healthy_reference` is a reference line, not a baseline.
Each trial: fresh container, `--restart on-failure`, read-only filesystem, 1 CPU,
128 MB memory, localhost port. Schedule order is shuffled with seed 2424 (so every run
has the same order); noise draws are seeded per trial and container and recorded.
Detectors never read ground-truth or injection files.

There is no ML training and no train/validation/test split: the rules are fixed and
nothing is tuned on collected data.

## 7. Project map

```text
app/server.py                  API, controlled faults and noise
Dockerfile                     Image definition with pinned base digest
protocol.json                  Protocol 2.0 rules, noise, seed and limitations
protocol_v1.json               Protocol 1.0, kept for reference
expectations/                  Expected results, frozen before 2.0 data
lab.py                         Collection and analysis commands
run_pilot.ps1 / run_pilot.sh   One-script launcher (Windows / macOS-Linux)
tests/test_lab.py              Software checks
docs/                          Explanations, research log, evidence checklist
evidence/                      Console logs, docker ps capture, 1.0 validation summary
runs/pilot/<run-id>/
  protocol.json, expectations.md   Frozen snapshots (expectations: 2.0 only)
  environment.json             Versions, image, operator, phase, hashes
  source/                      Code snapshot used for the run
  schedule.json                Planned trial order and labels
  trials.csv                   Attempted trials, validity and errors
  journal.jsonl                Trial start/end times and operator
  completion.json              Planned, valid and invalid counts
  manifest.sha256.json         Original evidence checksums
  raw/requests.csv             RAW DATA: measured HTTP requests
  raw/T0001/                   RAW DATA: per-trial HTTP, container, logs, control records
  processed/                   WORKING COPY: derived tables used for analysis
```

Do not edit raw evidence or its checksum manifest; the analyzer refuses changed evidence.

## 8. Main collection

```text
python lab.py collect --phase main --rounds 10 --operator "<who runs it>"
```

10 rounds = 140 trials (70 healthy, 70 faulty), collected on 22.10.2026 as
`runs/main/20261022T190115Z-b15df2`. The expectations in
`expectations/EXPECTED_RESULTS_v2.md` give their ranges for this size and were not
edited after collection.

Known instrument defect for any future collection: the API writes a log line with
`print`, and two threads writing at the same moment can join two JSON lines. A fix
(write each line in one call under a lock) would be a new protocol version; it is
not applied to the existing runs.

## 9. Dataset

All data in this repository were generated by our own instrument (`app/server.py` and
`lab.py`); no external dataset or database is used. Every run stores plain CSV and JSON
files, so the data can be opened in any spreadsheet or with Python without extra tools.

| Item | Entry |
|---|---|
| Name and version | RMT-A3 fault-detection trials; protocol 1.0 (2 pilot runs) and protocol 2.0 (1 pilot run, 1 main run) |
| Generated | 22.10.2026 |
| License | Code: MIT; data and documentation: CC BY 4.0 (see `LICENSE`) |
| Size | 4 runs, 208 trials planned, 207 valid; 1,035 measured requests in valid trials. Main run: 140 trials, 139 valid, 695 requests |
| Unit of analysis | Trial (one fresh container, five measured requests) |
| Classes | truth 0 = healthy, truth 1 = faulty; scenarios: healthy, exception, silent_http_error, background_error, slow_response, stopped_container, intermittent_exception (2.0), crash_restart (2.0) |
| Missing or wrong items | 1 invalid trial (main run T0125, malformed log line, excluded and kept with `failure.json`); 0 missing files; `status` is empty when no HTTP response arrived; undefined ratios are blank, never 0 |
| Raw data | `runs/<phase>/<run>/raw/requests.csv` and `raw/Txxxx/` (protected by `manifest.sha256.json`) |
| Processed data (working copy) | `runs/<phase>/<run>/processed/decisions.csv` and `metrics.csv` |
| File used for Assignment 4 | `runs/main/20261022T190115Z-b15df2/processed/metrics.csv` (with `decisions.csv` and `metrics_by_scenario.csv`) |

Main data files and their columns (full dictionary: [docs/DATA_AND_METRICS.md](docs/DATA_AND_METRICS.md)):

| File | One row is | Columns |
|---|---|---|
| `raw/requests.csv` | one measured request | trial, request, timestamp_utc, status, elapsed_ms, body, transport_error |
| `trials.csv` | one attempted trial | trial, round, scenario, truth, valid, error |
| `processed/decisions.csv` | one trial × one signal configuration | trial, round, scenario, truth, condition, prediction, http_positive, container_positive, logs_positive |
| `processed/metrics.csv` | one signal configuration | condition, n, TP, TN, FP, FN, accuracy, precision, recall, specificity, FPR, F1, balanced_accuracy, accuracy_ci95, recall_ci95, FPR_ci95 |

How to cite the data:

Zhumagulov, M. and Balgabekov, R. (2026) *RMT-A3 containerized API fault-detection trials*,
runs 20261022T100815Z-3082e0, 20261022T101634Z-23a61b, 20261022T183629Z-157c1c,
20261022T190115Z-b15df2. Available at: https://github.com/RakhatBalga/rmt

Weakness of the dataset: faults and noise are synthetic and chosen by us, so it has no
real incidents, no real user load, no multi-service dependencies and no slowly developing
faults (memory leaks, disk exhaustion). It shows whether a signal detects a fault, not how
fast.

## 10. References

Sources the design, fault set, detection rules and metrics are based on (Harvard style;
the same list as in our Assignment 2 and Assignment 3 reports):

- Fang, A., Zhang, S., Yang, Y., Wu, H., Xu, J., Wang, X., Wang, R., Wang, M., Lu, Q. and He, P. (2025) 'Rethinking the evaluation of microservice RCA with a fault propagation-aware benchmark', *arXiv preprint*, arXiv:2510.04711. doi:10.48550/arXiv.2510.04711. Available at: https://arxiv.org/abs/2510.04711 (Accessed: 3 October 2026).
- Kim, M., Xin, Q., Sinha, S. and Orso, A. (2022) 'Automated test generation for REST APIs: no time to rest yet', in *Proceedings of the 31st ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA 2022)*. New York: ACM, pp. 289–301. doi:10.1145/3533767.3534401. Available at: https://arxiv.org/abs/2204.08348 (Accessed: 3 October 2026).
- Le, V.-H. and Zhang, H. (2022) 'Log-based anomaly detection with deep learning: how far are we?', in *Proceedings of the 44th International Conference on Software Engineering (ICSE 2022)*. New York: ACM, pp. 1356–1367. doi:10.1145/3510003.3510155.
- Pham, L., Zhang, H., Ha, H., Salim, F. and Zhang, X. (2025) 'RCAEval: a benchmark for root cause analysis of microservice systems with telemetry data', in *Companion Proceedings of the ACM Web Conference 2025 (WWW Companion '25)*. New York: ACM, pp. 777–780. doi:10.1145/3701716.3715290.
- Simonsson, J., Zhang, L., Morin, B., Baudry, B. and Monperrus, M. (2021) 'Observability and chaos engineering on system calls for containerized applications in Docker', *Future Generation Computer Systems*, 122, pp. 117–129. doi:10.1016/j.future.2021.04.001.
- Soldani, J. and Brogi, A. (2022) 'Anomaly detection and failure root cause analysis in (micro)service-based cloud applications: a survey', *ACM Computing Surveys*, 55(3), Article 59, pp. 1–39. doi:10.1145/3501297. Available at: https://arxiv.org/abs/2105.12378 (Accessed: 3 October 2026).
- Zhou, X., Peng, X., Xie, T., Sun, J., Ji, C., Li, W. and Ding, D. (2021) 'Fault analysis and debugging of microservice systems: industrial survey, benchmark system, and empirical study', *IEEE Transactions on Software Engineering*, 47(2), pp. 243–260. doi:10.1109/TSE.2018.2887384.

## 11. Troubleshooting

| Symptom | Action |
|---|---|
| Docker cannot connect | Start Docker Desktop, wait for the Linux engine, rerun doctor |
| PowerShell blocks .ps1 | Use the manual commands above |
| Image not found | Run build before collect |
| Freeze expectations before collecting | The expectations file is missing |
| INVALID / Readiness failed | Preserve data; inspect trials.csv and raw/Txxxx/failure.json |
| Evidence changed since collection | Restore the genuine original file; never edit the checksum |
| Analyzer changed / supports 2.0 only | Use the run's preserved source/lab.py |
| HTTP 500/503/timeout | Usually an intended fault or noise observation |
