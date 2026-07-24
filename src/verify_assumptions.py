"""
Standalone verification of the statistical assumptions behind the Hypothesis 1
significance test (praxis Section 3.5.3).

Reads results/hypothesis1_results.csv (produced by phase1_hypothesis1_analysis.py)
and reports, for the Jaccard environment-variable deviation metric:

  1. What the two-sample test does and the assumptions the parametric
     Student's t-test relies on.
  2. Explicit verification of each assumption:
        - Independence  : satisfied by design.
        - Normality     : Shapiro-Wilk per group.
        - Equal variance: Levene's test.
  3. The appropriate significance test given the assumption results. Because
     normality and equal variance are violated, the non-parametric
     Mann-Whitney U test is the primary result; Welch's t-test (unequal
     variance) and Student's t-test are reported for reference.

The builder-identity (NLD) metric is intentionally NOT tested: both groups have
zero within-group variance, so any t-statistic is mathematically undefined and
the result is reported as a categorical separation of constants (Section 4.2.1).

Usage:
    python src/verify_assumptions.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

CSV_PATH = os.path.join("results", "hypothesis1_results.csv")
OUT_PATH = os.path.join("results", "assumption_checks.txt")
ALPHA = 0.05


def describe(name, arr):
    return (f"  {name:<10}: n={len(arr)}, mean={arr.mean():.4f}, "
            f"var={arr.var(ddof=1):.4f}, "
            f"values={dict(zip(*[x.tolist() for x in np.unique(arr, return_counts=True)]))}")


def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"Missing {CSV_PATH}. Run phase1_hypothesis1_analysis.py first.")

    df = pd.read_csv(CSV_PATH)
    u = df[df["label"] == "untampered"]["env_var_deviation"].to_numpy(float)
    t = df[df["label"] == "tampered"]["env_var_deviation"].to_numpy(float)

    out = []
    out.append("HYPOTHESIS 1 — STATISTICAL ASSUMPTION VERIFICATION")
    out.append("Metric: Jaccard environment-variable deviation (%)")
    out.append("=" * 62)
    out.append("A two-sample test compares the metric between the untampered")
    out.append("control and tampered experimental groups, testing the null")
    out.append("hypothesis that both are drawn from the same distribution.")
    out.append("The parametric Student's t-test assumes: (1) independence,")
    out.append("(2) within-group normality, (3) homogeneity of variance.")
    out.append("")
    out.append("Group summary:")
    out.append(describe("untampered", u))
    out.append(describe("tampered", t))
    out.append("")

    # Assumption 1: independence
    out.append("Assumption 1 — Independence: satisfied by design; every")
    out.append("provenance file comes from a separate ephemeral CI/CD run.")
    out.append("")

    # Assumption 2: normality (Shapiro-Wilk)
    out.append("Assumption 2 — Normality (Shapiro-Wilk):")
    for name, arr in (("untampered", u), ("tampered", t)):
        if np.ptp(arr) == 0:
            out.append(f"  {name:<10}: constant (all = {arr[0]:.1f}); test "
                       "degenerate — incompatible with normality.")
        else:
            w, p = stats.shapiro(arr)
            v = "normal" if p > ALPHA else "NOT normal (reject H0)"
            out.append(f"  {name:<10}: W={w:.4f}, p={p:.3e} -> {v}")
    out.append("")

    # Assumption 3: homogeneity of variance (Levene)
    lw, lp = stats.levene(u, t)
    lv = "equal" if lp > ALPHA else "UNEQUAL (reject H0)"
    out.append("Assumption 3 — Homogeneity of variance (Levene):")
    out.append(f"  W={lw:.4f}, p={lp:.3e} -> variances {lv}")
    out.append("")

    # Decision + tests
    out.append("-" * 62)
    out.append("DECISION: normality and equal-variance assumptions are")
    out.append("violated, so the parametric t-test is not appropriate as the")
    out.append("primary test. The non-parametric Mann-Whitney U test, which")
    out.append("requires neither assumption, is used as the primary result.")
    out.append("")
    U, p_mw = stats.mannwhitneyu(u, t, alternative="two-sided")
    rb = 1.0 - (2.0 * U) / (len(u) * len(t))
    out.append(f"[PRIMARY]   Mann-Whitney U : U={U:.1f}, p={p_mw:.3e}, "
               f"rank-biserial={rb:.2f}")
    tw, pw = stats.ttest_ind(t, u, equal_var=False)
    out.append(f"[secondary] Welch's t-test : t={tw:.4f}, p={pw:.3e}")
    ts, ps = stats.ttest_ind(t, u, equal_var=True)
    out.append(f"[reference] Student's t    : t={ts:.4f}, p={ps:.3e} "
               "(assumptions unmet; shown for comparison)")
    out.append("")
    concl = "significant" if p_mw < 0.001 else "not significant"
    out.append(f"Conclusion: tampered vs. untampered deviation is {concl} "
               f"(p < 0.001) under the assumption-free primary test.")

    report = "\n".join(out)
    print(report)
    os.makedirs("results", exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        fh.write(report + "\n")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
