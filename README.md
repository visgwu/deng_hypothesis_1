
### ✅ Hypothesis-1 Outcome

> **Hypothesis 1:**  
> *Tampered artifacts will show ≥ 25 % deviation in statistical patterns across provenance fields compared to untampered ones.*

**Result:** *Partially Supported*  
- Quantitatively supported by the model-derived `tampering_score` metric (≈ 193 % deviation, p < 0.001).  
- Not supported by low-variance provenance fields (`materials_count`, `entropy_b64`, `time_delta_sec`).

This indicates that the **fine-tuned LLM detects semantic tampering behavior**, whereas **raw provenance metadata fields alone** remain statistically stable.

---

### 📈 Visualization

The deviation chart below summarizes these findings:

![Hypothesis-1 Deviation Plot](hypothesis1_deviation_plot.png)

- The dashed red line marks the 25 % deviation threshold.  
- Only the `tampering_score` exceeds the threshold, confirming its discriminative effectiveness.

---

## 🌿 Workflow Overview

| **Phase** | **Script** | **Description** |
|:-----------|:------------|:----------------|
| **Phase 2** | `phase2_feature_extraction.py` | Unzips provenance dataset and extracts fields: `builder_id`, `materials_count`, `time_delta_sec`, `entropy_b64`, etc. |
| **Phase 3** | `phase3_model_inference.py` | Runs inference on each provenance record using the fine-tuned model `ft:gpt-4o-mini-2024-07-18:vchirrav::CQm2xpT1` and appends a `tampering_score`. |
| **Phase 4** | `phase4_hypothesis1_analysis.py` | Performs deviation and significance testing across tampered vs untampered sets; generates statistical summary and visualization. |

---

## ⚙️ Environment Setup

```bash
# Create virtual environment (optional)
python -m venv .venv
source .venv/bin/activate       # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

## 📊 Results Summary (Phase-4)

The model inference and deviation analysis produced the following metrics:

| Metric | Untampered Mean | Tampered Mean | Deviation % | t-Statistic | p-Value | Significant (p ≤ 0.05)? |
|:-------|:----------------|:---------------|:-------------|:-------------|:---------|:------------------------|
| **tampering_score** | 0.3265 | 0.9565 | **192.93 %** | 7.8311 | 0.00000 | ✅ True |
| materials_count | 0.9592 | 0.9130 | 4.81 % | –0.6937 | 0.49285 | ❌ False |
| time_delta_sec | — | — | — | — | — | ❌ No data |
| entropy_b64 | 5.7188 | 5.7193 | 0.01 % | 0.4535 | 0.65165 | ❌ False |

---

### 🧠 Interpretation

- **Tampering Score (p = 0.000, Δ ≈ 193 %)**  
  The fine-tuned LLM clearly separates tampered and untampered provenance artifacts, demonstrating strong discriminative learning.  
  This supports the model’s ability to detect provenance manipulation patterns.

- **Materials Count (Δ ≈ 4.8 %, p = 0.49)**  
  Minimal variation; indicates that the number of materials in provenance metadata does not change significantly when tampered.

- **Entropy (b64 payload)**  
  Negligible deviation (< 0.05 %) and no significance — implying that payload entropy alone is not a reliable indicator of tampering.

- **Time Delta**  
  Missing or inconsistent timestamp values prevented calculation; these fields can be refined in future dataset iterations.

---

### 🧩 Next Steps (Phase-5 – Extended Feature Extraction)

To strengthen statistical evaluation, enrich provenance feature space with:

| Feature | Description |
|:---------|:-------------|
| `recipe_steps_count` | Number of build steps in recipe |
| `avg_command_length` | Mean command-string length |
| `unique_material_hashes` | Count of unique material digests |
| `builder_domain` | Domain portion of `builder.id` |
| `signature_count` | Count of DSSE envelope signatures |
| `timestamp_delta_ratio` | Normalized duration of build process |

These features will introduce measurable variance across tampered and untampered sets, improving future hypothesis validation.

---

## License

This project is part of the Doctor of Engineering research under academic use.
All scripts and datasets are provided for research and educational purposes only.