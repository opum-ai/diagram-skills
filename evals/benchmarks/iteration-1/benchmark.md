# Skill Benchmark: diagram-skills

**Model**: claude-opus-5-5 (subagents)
**Date**: 2026-10-06T16:49:59Z
**Evals**: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 (1 run each per configuration; ± is across evals)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 78% ± 9% | +0.22 |
| Time | 78.4s ± 27.3s | 62.3s ± 29.1s | +16.1s |
| Tokens | 39153 ± 5965 | 28425 ± 4461 | +10728 |

## Analyst notes

- One run per configuration per eval: the ± figures are spread across the 12 evals, not run-to-run variance. A second round should run 3 per arm before any delta is quoted as stable.
- 12 of the baseline's 17 failed expectations are missing accTitle/accDescr. Accessibility fields are the dominant discriminator.
- Truth assertions (every node real, no invented components, exact Quest edges, FK set) did not discriminate: the baseline read this small fixture accurately too. The fixture has 7 components and no misleading docs, so invention pressure is low; harder fixtures (larger repos, stale docs that name removed services) are needed to test the truth check's value.
- Remaining real deltas: scoping plan views (baseline drew completed tasks and tasks outside the epic) and marking the chosen option in text; one beginner baseline drew the chosen approach only, with no options.
- Cost: with-skill runs used about 38% more tokens and 26% more time (they run the three checks and read references).
- Not measured: correctness of the prose. The eval-09 with-skill answer says legacy_carts is created and dropped in 001_init.sql; it is 002_coupons.sql. Objective graders do not read prose claims.
- The grader was fixed twice during the round (node classification; quoted labels with parentheses were truncated). Both fixes were applied to every run of both arms before the final grading.
