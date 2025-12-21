# Hypothesis 1: Semantic Deviation in Tampered Software Provenance

## 1. Research Overview
This research component of the Doctor of Engineering praxis investigates the statistical characteristics of software supply chain artifacts under attack. The study focuses on quantifying the "semantic noise" introduced when a software build process is compromised by malicious actors.

## 2. Hypothesis Statement
**Hypothesis 1:** "Software artifacts subjected to tampering will exhibit a statistically significant deviation (**≥ 25%**) in **semantic similarity metrics** (Levenshtein Distance, Jaccard Index) across key provenance fields (Builder ID, Environment) when compared to a baseline of verified, untampered artifacts."

## 3. Methodology

### 3.1 Data Collection
The dataset was constructed through controlled empirical execution of CI/CD pipelines using **GitHub Actions**:
* **Untampered Baseline ($N=50$):** Fifty independent build runs were executed using a secured, SLSA-compliant workflow. These builds utilized the standard `github-hosted-runner` and verified build entry points.
* **Tampered Dataset ($N=50$):** Fifty additional build runs were executed after introducing malware-based components into the pipeline. These runs simulated common supply chain attack vectors, including:
    * **Builder Compromise:** Redirecting execution to an untrusted private runner.
    * **Environment Injection:** Injecting malicious environment variables (e.g., `LD_PRELOAD`, debug flags) and removing security controls (`SECURE_BOOT`).

### 3.2 Metric Selection
To quantify the deviation, two specific semantic metrics were calculated for each artifact:
1.  **Builder Identity Deviation:** Measured using **Normalized Levenshtein Distance**. This captures the textual difference between the expected builder URI and the actual builder URI found in the provenance.
2.  **Environment Deviation:** Measured using the **Jaccard Distance** ($1 - Jaccard Index$). This captures the divergence in the set of environment variables present during the build.

## 4. Results

The analysis compared the semantic metrics of the 50 tampered artifacts against the Golden Reference baseline. The results demonstrate a massive statistical separation between the two groups.

### 4.1 Quantitative Findings
The study successfully identified that tampering introduces deviation significantly exceeding the 25% threshold defined in the hypothesis.

| Metric | Untampered Mean Deviation | Tampered Mean Deviation | Hypothesis Threshold | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Builder ID Deviation** | 0.00% | **61.11%** | > 25% | **PASS** |
| **Environment Deviation** | 0.00% | **29.25%** | > 25% | **PASS** |

### 4.2 Visual Evidence
The chart below illustrates the stark contrast between the baseline (Green) and the tampered (Red) samples. The dashed line represents the 25% validation threshold.

![Semantic Deviation Results](results/hypothesis1_chart.png)

*Figure 1: Mean semantic deviation observed in Builder ID and Environment fields. Both metrics in the tampered group significantly exceed the hypothesis threshold.*

## 5. Conclusion
**Hypothesis 1 is ACCEPTED.**

The empirical data confirms that software supply chain attacks leave a distinct semantic footprint in provenance metadata. 
* **Builder Compromise** resulted in a **61.1% deviation**, proving that attacker infrastructure cannot easily mimic trusted builder identities without detection.
* **Environment Tampering** resulted in a **29.3% deviation**, confirming that the injection of malicious flags or removal of security controls creates measurable statistical noise.

These findings validate that semantic similarity metrics are a reliable first-line indicator for detecting artifact tampering.