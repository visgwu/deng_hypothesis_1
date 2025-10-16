"""
PHASE 3 (FIXED): Model Inference for Hypothesis-1
-------------------------------------------------
Uses the fine-tuned model ft:gpt-4o-mini-2024-07-18:vchirrav::CQm2xpT1
to classify each provenance record as tampered or untampered.

Outputs:
  - hypothesis1_inference_outputs.csv  (with tampering_score column)
"""

import os, json, pandas as pd, openai
from tqdm import tqdm

# === Configuration ===
MODEL = "ft:gpt-4o-mini-2024-07-18:vchirrav::CQm2xpT1"
openai.api_key = "XXXXXXXX"
DATASET_PATH = "hypothesis1_features.csv"
BASE_DIR = "final_datasets_extracted"

# === Load features ===
df = pd.read_csv(DATASET_PATH)

def get_provenance_text(row):
    """Read raw provenance JSON text from extracted folder."""
    fpath = os.path.join(BASE_DIR, row["path"])
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("Error reading:", fpath, e)
        return ""

def call_model_on_provenance(prov_text):
    """
    Query fine-tuned model and handle multiple possible response formats.
    Maps 'tampered' -> 1.0, 'untampered' -> 0.0
    """
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a provenance tampering detector. Respond with only one word: 'tampered' or 'untampered'."
                },
                {"role": "user", "content": prov_text}
            ],
            temperature=0
        )

        # --- inspect various formats ---
        content = None
        try:
            content = response.choices[0].message.get("content", None)
        except Exception:
            pass

        # if it's nested under content[0].text
        if not content:
            msg = response.choices[0].message
            if isinstance(msg, dict) and "content" in msg and isinstance(msg["content"], list):
                # Newer SDKs sometimes return a list of blocks
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content = block.get("text", "").strip()
                        break

        if not content:
            print("⚠️ No content field found in response:", response)
            return None

        result = content.strip().lower()
        if "untampered" in result:
            return 0.0
        elif "tampered" in result:
            return 1.0
        else:
            print("⚠️ Unrecognized response:", result)
            return None

    except Exception as e:
        print("Error calling model:", e)
        return None

# === Inference loop ===
scores, responses = [], []

for i, row in tqdm(df.iterrows(), total=len(df)):
    prov_text = get_provenance_text(row)
    score = call_model_on_provenance(prov_text)
    scores.append(score)

df["tampering_score"] = scores
df.to_csv("hypothesis1_inference_outputs.csv", index=False)

print("\n[✓] Inference complete — results saved to hypothesis1_inference_outputs.csv")
print(df[["id", "label", "tampering_score"]].head())
