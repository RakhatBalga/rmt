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

## 9. Troubleshooting

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
