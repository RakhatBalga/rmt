# Research log

[Back to README](../README.md)

One row per working session or collection run. Times are UTC (Kazakhstan = UTC+5).
Per-trial start/end times are in each run's `journal.jsonl`.

| No. | Date, time (UTC) | Who | What was done | What went wrong | What was changed |
|---|---|---|---|---|---|
| L1 | 22.10.2026, before 10:00 | Team (Windows PC) | Installed the lab on the team's Windows 11 PC; ran `doctor` | Docker Desktop would not start (socket errors, Windows error 1920) | Moved two Docker runtime folders aside, restarted Docker (see SETUP_NOTES.md) |
| L2 | 22.10.2026, before 10:08 | Team (Windows PC) | Built image `rmt-a3-api:1.0`, ran 5 software tests | First test attempt could not reach localhost in a restricted shell | Re-ran with local network access; all 5 passed. HTTPError responses now closed explicitly |
| L3 | 22.10.2026, 10:08:15–10:09:36 | Team, automated launcher | Pilot 1.0, run 20261022T100815Z-3082e0: 20 trials, 100 requests | Nothing; 20/20 valid | — |
| L4 | 22.10.2026, 10:16:34–10:17:46 | Marlen Zhumagulov | Pilot 1.0 via `run_pilot.ps1`, run 20261022T101634Z-23a61b: 20 trials | Nothing; 20/20 valid. Console log saved as UTF-16 by PowerShell | Later converted to UTF-8; launcher now writes UTF-8 |
| L5 | 22.10.2026, ~18:00 | Rakhat Balgabekov | Reviewed both 1.0 pilots and re-ran their analysis on macOS: identical tables reproduced, checksums intact | Both pilots gave identical results; healthy latency max 43 ms vs 400 ms timeout, so FP was impossible and the outcome was fixed by design | Decided to write protocol 2.0 before any main run |
| L6 | 22.10.2026, ~18:15–18:35 | Rakhat Balgabekov | Wrote protocol 2.0 (noise, intermittent_exception, crash_restart, restart policy, 7 healthy trials per round, Wilson CIs, McNemar). Detector rules unchanged. 7 tests pass | — | Removed a personal Windows path from SETUP_NOTES.md; removed cache files |
| L7 | 22.10.2026, 18:35:51 | Rakhat Balgabekov | Froze `expectations/EXPECTED_RESULTS_v2.md` (SHA-256 5ccdc0c1…ea04773) from a simulation of the designed noise rates | — | — |
| L8 | 22.10.2026, 18:36:22 | Rakhat Balgabekov | Built image `rmt-a3-api:2.0` on macOS arm64, Docker Desktop 4.73.0 / Engine 29.4.3 | — | — |
| L9 | 22.10.2026, 18:36:29–18:37:50 | Rakhat Balgabekov, automated launcher | Pilot 2.0, run 20261022T183629Z-157c1c: 28 trials, 140 requests; `docker ps` captured mid-run | No invalid trials. Noted: stopped containers refuse connections in ~1 ms on macOS but time out (~415 ms) on Windows; some log-detector hits on silent/slow/crash faults come from benign noise lines, not from the fault | Nothing changed after seeing the data; observations recorded for the main run |
| L10 | 22.10.2026, after 18:38 | Rakhat Balgabekov | Analyzed the 2.0 pilot, compared it with the frozen expectations, wrote the A3 report | — | — |
| L11 | planned | Team | Main collection: `collect --phase main --rounds 10` (140 trials) with protocol 2.0 unchanged | | |
