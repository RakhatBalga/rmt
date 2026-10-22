# Expected results for protocol 2.0 — fixed 22.10.2026, before any 2.0 data

Team: ZhumagulovMarlen_BalgabekovRakhat (SE-2424).
Context, stated honestly: two protocol 1.0 pilots were already observed on 22.10.2026.
They showed that 1.0 was deterministic, which is why protocol 2.0 was written.
The expectations below are for protocol 2.0. They were derived from the designed
noise rates (simulation of the protocol parameters, no measured 2.0 data) and from
the 1.0 pilot, and they are not edited after 2.0 data is collected.

Ranges refer to the planned main collection (10 rounds, n=140: 70 healthy, 70 faulty).
The 2.0 pilot (2 rounds, n=28) is only checked for direction ("trending toward/against").

| No. | Expected result | Falsified if (main run) | Confidence |
|---|---|---|---|
| ER1 | HTTP-only recall is about 0.84 | HTTP recall < 0.75 or > 0.92 | Medium: crash_restart visibility to HTTP is unknown |
| ER2 | Logs-only has the highest single-source FPR (about 0.23) | logs FPR <= HTTP FPR, or logs FPR outside 0.12-0.35 | Medium-high |
| ER3 | Container-only never raises a false alarm and detects only stopped/crashed containers (recall about 0.29) | any healthy trial flagged by container, or container recall outside 0.20-0.32 | High |
| ER4 | HTTP+container has higher accuracy than HTTP+logs: logs add recall but cost more in false alarms | accuracy(http+logs) >= accuracy(http+container) | Medium |
| ER5 | No configuration exceeds 0.92 accuracy once noise is present | any configuration accuracy >= 0.93 | Medium-high |
| ER6 | background_error is the fault type HTTP-only misses most (scenario recall <= 0.30) | another fault type has lower HTTP recall, or background_error HTTP recall > 0.30 | High |
| ER7 | Instrument validity: at least 95% of trials are valid | more than 5% invalid trials | High |

Signs of a broken process rather than a finding: container detector flags a healthy
trial; any configuration with recall 1.0 AND FPR 0.0 for all trials (noise not active);
two runs with identical per-trial decisions; healthy HTTP latency never above 0.1 s.

Outcome scenarios
- Bad 1: many invalid trials (crash_restart breaks readiness/cleanup) — the instrument, not the detectors, is measured.
- Bad 2: noise is not active (results identical to 1.0) — protocol 2.0 failed to create uncertainty.
- Medium 1: ranking as expected but FPR much lower than designed (e.g. latency spikes absorbed by the client) — conclusions hold only for clean environments.
- Medium 2: HTTP detects crash_restart almost never (restart faster than request interval) — container state becomes necessary, changing ER1/ER4.
- Good 1: ranges hold and http+container beats http+logs — clear trade-off between recall and false alarms.
- Good 2: ranges hold and per-scenario results explain every miss — the detector map by fault type is the main contribution.
