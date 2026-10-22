# Measured results

Phase: pilot
Planned: 28; valid: 28; invalid: 0.

| Condition | n | TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| http | 28 | 12 | 13 | 1 | 2 | 0.892857 | 0.923077 | 0.857143 | 0.888889 |
| container | 28 | 4 | 14 | 0 | 10 | 0.642857 | 1.0 | 0.285714 | 0.444444 |
| logs | 28 | 8 | 10 | 4 | 6 | 0.642857 | 0.666667 | 0.571429 | 0.615385 |
| http+container | 28 | 12 | 13 | 1 | 2 | 0.892857 | 0.923077 | 0.857143 | 0.888889 |
| http+logs | 28 | 14 | 9 | 5 | 0 | 0.821429 | 0.736842 | 1.0 | 0.848485 |
| container+logs | 28 | 11 | 10 | 4 | 3 | 0.75 | 0.733333 | 0.785714 | 0.758621 |
| http+container+logs | 28 | 14 | 9 | 5 | 0 | 0.821429 | 0.736842 | 1.0 | 0.848485 |
| always_healthy_reference | 28 | 0 | 14 | 0 | 14 | 0.5 | N/A | 0.0 | 0.0 |

| Condition | FPR | Accuracy 95% CI | Recall 95% CI | FPR 95% CI |
|---|---:|---:|---:|---:|
| http | 0.071429 | 0.728041-0.962882 | 0.600586-0.959906 | 0.012722-0.314687 |
| container | 0.0 | 0.458303-0.792942 | 0.117214-0.546491 | 0-0.215311 |
| logs | 0.285714 | 0.458303-0.792942 | 0.325906-0.786192 | 0.117214-0.546491 |
| http+container | 0.071429 | 0.728041-0.962882 | 0.600586-0.959906 | 0.012722-0.314687 |
| http+logs | 0.357143 | 0.644086-0.921215 | 0.784689-1.0 | 0.163447-0.612356 |
| container+logs | 0.285714 | 0.566443-0.873235 | 0.524108-0.924286 | 0.117214-0.546491 |
| http+container+logs | 0.357143 | 0.644086-0.921215 | 0.784689-1.0 | 0.163447-0.612356 |
| always_healthy_reference | 0.0 | 0.326331-0.673669 | 0-0.215311 | 0-0.215311 |

| Condition vs HTTP | only HTTP correct | only condition correct | exact McNemar p |
|---|---:|---:|---:|
| container | 8 | 1 | 0.039062 |
| logs | 10 | 3 | 0.092285 |
| http+container | 0 | 0 | 1.0 |
| http+logs | 4 | 2 | 0.6875 |
| container+logs | 7 | 3 | 0.34375 |
| http+container+logs | 4 | 2 | 0.6875 |

Undefined ratios are blank in CSV and N/A here, never replaced with zero.
This is a synthetic benchmark of fixed rules, not evidence about human skill or unseen production faults.
Repeated requests within a trial are not independent samples. Pilot data must not be presented as a separate main study.
Cleaning: no imputation, no deduplication; invalid trials excluded explicitly; all raw files retained.
See metrics_by_scenario.csv and metrics_by_round.csv for all strata and repetitions.
