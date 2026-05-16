# Sensitivity Sweep
Knobs swept: frontier quantile, constraint-score weighting scheme, cap multiplier.
Stress: how much do final predictions move when these are changed?

| Quantile | Scheme | Cap | Median Uplift | Mean Uplift | Max Uplift | % Capped |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0.90 | balanced | 2.0x | 1.250 | 1.222 | 2.000 | 0.0% |
| 0.90 | balanced | 3.0x | 1.250 | 1.222 | 2.227 | 0.0% |
| 0.90 | balanced | 4.0x | 1.250 | 1.222 | 2.227 | 0.0% |
| 0.90 | balanced | 5.0x | 1.250 | 1.222 | 2.227 | 0.0% |
| 0.90 | balanced | 6.0x | 1.250 | 1.222 | 2.227 | 0.0% |
| 0.90 | frontier_heavy | 2.0x | 1.250 | 1.224 | 2.000 | 0.0% |
| 0.90 | frontier_heavy | 3.0x | 1.250 | 1.224 | 2.341 | 0.0% |
| 0.90 | frontier_heavy | 4.0x | 1.250 | 1.224 | 2.341 | 0.0% |
| 0.90 | frontier_heavy | 5.0x | 1.250 | 1.224 | 2.341 | 0.0% |
| 0.90 | frontier_heavy | 6.0x | 1.250 | 1.224 | 2.341 | 0.0% |
| 0.90 | plateau_heavy | 2.0x | 1.250 | 1.241 | 2.000 | 0.0% |
| 0.90 | plateau_heavy | 3.0x | 1.250 | 1.241 | 2.133 | 0.0% |
| 0.90 | plateau_heavy | 4.0x | 1.250 | 1.241 | 2.133 | 0.0% |
| 0.90 | plateau_heavy | 5.0x | 1.250 | 1.241 | 2.133 | 0.0% |
| 0.90 | plateau_heavy | 6.0x | 1.250 | 1.241 | 2.133 | 0.0% |
| 0.95 | balanced | 2.0x | 1.250 | 1.227 | 2.000 | 0.0% |
| 0.95 | balanced | 3.0x | 1.250 | 1.227 | 2.526 | 0.0% |
| 0.95 | balanced | 4.0x | 1.250 | 1.227 | 2.526 | 0.0% |
| 0.95 | balanced | 5.0x | 1.250 | 1.227 | 2.526 | 0.0% |
| 0.95 | balanced | 6.0x | 1.250 | 1.227 | 2.526 | 0.0% |
| 0.95 | frontier_heavy | 2.0x | 1.250 | 1.230 | 2.000 | 0.0% |
| 0.95 | frontier_heavy | 3.0x | 1.250 | 1.230 | 2.818 | 0.0% |
| 0.95 | frontier_heavy | 4.0x | 1.250 | 1.230 | 2.818 | 0.0% |
| 0.95 | frontier_heavy | 5.0x | 1.250 | 1.230 | 2.818 | 0.0% |
| 0.95 | frontier_heavy | 6.0x | 1.250 | 1.230 | 2.818 | 0.0% |
| 0.95 | plateau_heavy | 2.0x | 1.250 | 1.244 | 2.000 | 0.0% |
| 0.95 | plateau_heavy | 3.0x | 1.250 | 1.244 | 2.420 | 0.0% |
| 0.95 | plateau_heavy | 4.0x | 1.250 | 1.244 | 2.420 | 0.0% |
| 0.95 | plateau_heavy | 5.0x | 1.250 | 1.244 | 2.420 | 0.0% |
| 0.95 | plateau_heavy | 6.0x | 1.250 | 1.244 | 2.420 | 0.0% |
