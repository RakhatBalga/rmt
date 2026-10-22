# Measured results

Phase: pilot
Planned: 20; valid: 20; invalid: 0.

| Condition | n | TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| http | 20 | 8 | 10 | 0 | 2 | 0.9 | 1.0 | 0.8 | 0.888889 |
| container | 20 | 2 | 10 | 0 | 8 | 0.6 | 1.0 | 0.2 | 0.333333 |
| logs | 20 | 4 | 10 | 0 | 6 | 0.7 | 1.0 | 0.4 | 0.571429 |
| http+container | 20 | 8 | 10 | 0 | 2 | 0.9 | 1.0 | 0.8 | 0.888889 |
| http+logs | 20 | 10 | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 |
| container+logs | 20 | 6 | 10 | 0 | 4 | 0.8 | 1.0 | 0.6 | 0.75 |
| http+container+logs | 20 | 10 | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 | 1.0 |
| always_healthy_reference | 20 | 0 | 10 | 0 | 10 | 0.5 | N/A | 0.0 | 0.0 |

Undefined ratios are blank in CSV and N/A here, never replaced with zero.
This is a synthetic benchmark of fixed rules, not evidence about human skill or unseen production faults.
Repeated requests within a trial are not independent samples. Pilot data must not be presented as a separate main study.
Cleaning: no imputation, no deduplication; invalid trials excluded explicitly; all raw files retained.
See metrics_by_scenario.csv and metrics_by_round.csv for all strata and repetitions.
