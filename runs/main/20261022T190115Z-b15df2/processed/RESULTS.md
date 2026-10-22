# Measured results

Phase: main
Planned: 140; valid: 139; invalid: 1.

| Condition | n | TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| http | 139 | 60 | 61 | 8 | 10 | 0.870504 | 0.882353 | 0.857143 | 0.869565 |
| container | 139 | 20 | 69 | 0 | 50 | 0.640288 | 1.0 | 0.285714 | 0.444444 |
| logs | 139 | 38 | 54 | 15 | 32 | 0.661871 | 0.716981 | 0.542857 | 0.617886 |
| http+container | 139 | 60 | 61 | 8 | 10 | 0.870504 | 0.882353 | 0.857143 | 0.869565 |
| http+logs | 139 | 70 | 46 | 23 | 0 | 0.834532 | 0.752688 | 1.0 | 0.858896 |
| container+logs | 139 | 58 | 54 | 15 | 12 | 0.805755 | 0.794521 | 0.828571 | 0.811189 |
| http+container+logs | 139 | 70 | 46 | 23 | 0 | 0.834532 | 0.752688 | 1.0 | 0.858896 |
| always_healthy_reference | 139 | 0 | 69 | 0 | 70 | 0.496403 | N/A | 0.0 | 0.0 |

| Condition | FPR | Accuracy 95% CI | Recall 95% CI | FPR 95% CI |
|---|---:|---:|---:|---:|
| http | 0.115942 | 0.804585-0.916494 | 0.756616-0.920511 | 0.059935-0.212457 |
| container | 0.0 | 0.557723-0.715307 | 0.193222-0.400502 | 0.0-0.052737 |
| logs | 0.217391 | 0.579815-0.735219 | 0.426983-0.654273 | 0.136408-0.328183 |
| http+container | 0.115942 | 0.804585-0.916494 | 0.756616-0.920511 | 0.059935-0.212457 |
| http+logs | 0.333333 | 0.763936-0.887136 | 0.947977-1.0 | 0.233511-0.450735 |
| container+logs | 0.217391 | 0.732136-0.86293 | 0.723834-0.899123 | 0.136408-0.328183 |
| http+container+logs | 0.333333 | 0.763936-0.887136 | 0.947977-1.0 | 0.233511-0.450735 |
| always_healthy_reference | 0.0 | 0.414506-0.578493 | 0-0.052023 | 0.0-0.052737 |

| Condition vs HTTP | only HTTP correct | only condition correct | exact McNemar p |
|---|---:|---:|---:|
| container | 40 | 8 | 3e-06 |
| logs | 47 | 18 | 0.000422 |
| http+container | 0 | 0 | 1.0 |
| http+logs | 15 | 10 | 0.424356 |
| container+logs | 27 | 18 | 0.232693 |
| http+container+logs | 15 | 10 | 0.424356 |

Undefined ratios are blank in CSV and N/A here, never replaced with zero.
This is a synthetic benchmark of fixed rules, not evidence about human skill or unseen production faults.
Repeated requests within a trial are not independent samples. Pilot data must not be presented as a separate main study.
Cleaning: no imputation, no deduplication; invalid trials excluded explicitly; all raw files retained.
See metrics_by_scenario.csv and metrics_by_round.csv for all strata and repetitions.
