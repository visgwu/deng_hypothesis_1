"""
PHASE 4: Hypothesis-1 Deviation and Significance Analysis
--------------------------------------------------------
Reads model-inference output CSV, computes %-deviations,
runs statistical tests, and produces summary results.
"""

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt

# === Input file (from Phase-3) ===
CSV_FILE = "hypothesis1_inference_outputs.csv"

# === Load data ===
df = pd.read_csv(CSV_FILE)

# Clean up column names just in case
df.columns = [c.strip() for c in df.columns]

# === Convert tampering_score to numeric if needed ===
if df["tampering_score"].dtype == "object":
    df["tampering_score"] = (
        df["tampering_score"]
        .replace({"tampered": 1.0, "untampered": 0.0})
        .astype(float)
    )

# === Split into groups ===
df_t = df[df["label"].str.lower() == "tampered"]
df_u = df[df["label"].str.lower() == "untampered"]

# === Compute mean deviation function ===
def deviation(a, b):
    if a == 0 or pd.isna(a) or pd.isna(b):
        return np.nan
    return abs(a - b) / abs(a) * 100

# === Numeric fields to test ===
metrics = ["tampering_score", "materials_count", "time_delta_sec", "entropy_b64"]
summary = []

for m in metrics:
    mu_t = df_t[m].mean()
    mu_u = df_u[m].mean()
    dev_pct = deviation(mu_u, mu_t)
    tstat, pval = ttest_ind(df_t[m].dropna(), df_u[m].dropna(), equal_var=False)
    summary.append({
        "metric": m,
        "untampered_mean": round(mu_u, 4),
        "tampered_mean": round(mu_t, 4),
        "deviation_%": round(dev_pct, 2),
        "t_statistic": round(tstat, 4),
        "p_value": round(pval, 5),
        "significant_(p<=0.05)": pval <= 0.05
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv("hypothesis1_deviation_summary.csv", index=False)

# === Visualization ===
plt.figure(figsize=(6,4))
summary_df.plot.bar(x="metric", y="deviation_%", legend=False)
plt.axhline(25, color="red", linestyle="--", label="25% Threshold")
plt.title("Deviation (%) Between Tampered vs Untampered (Hypothesis-1)")
plt.ylabel("Deviation %")
plt.legend()
plt.tight_layout()
plt.savefig("hypothesis1_deviation_plot.png", dpi=200)
plt.close()

print("\n=== Hypothesis-1 Deviation Summary ===")
print(summary_df)
print("\nSaved to:")
print(" - hypothesis1_deviation_summary.csv")
print(" - hypothesis1_deviation_plot.png")

# === Interpretation Rule ===
supported_metrics = summary_df[
    (summary_df["deviation_%"] >= 25) & (summary_df["significant_(p<=0.05)"])
]
if not supported_metrics.empty:
    print("\n✅ Hypothesis-1 Supported:")
    print("  Deviations ≥ 25% with p ≤ 0.05 found in:")
    for m in supported_metrics["metric"]:
        print("  •", m)
else:
    print("\n❌ Hypothesis-1 Not Supported: no metric exceeded both thresholds.")
