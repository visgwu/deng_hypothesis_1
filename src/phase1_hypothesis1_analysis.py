import json
import glob
import os
import pandas as pd
import numpy as np
import Levenshtein
from scipy import stats
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
DATA_DIR_UNTAMPERED = "data/untampered"
DATA_DIR_TAMPERED = "data/tampered"
OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- METRIC FUNCTIONS ---

def get_builder_id(data):
    """Extracts builder ID safely."""
    try:
        return data['predicate']['builder']['id']
    except KeyError:
        return ""

def get_env_keys(data):
    """Extracts environment variable keys as a set."""
    try:
        return set(data['predicate']['invocation']['environment'].keys())
    except KeyError:
        return set()

def normalized_levenshtein(s1, s2):
    """
    Returns a normalized distance score between 0.0 (identical) and 1.0 (completely different).
    Formula: Distance / Max_Length
    """
    if not s1 and not s2: return 0.0
    dist = Levenshtein.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return dist / max_len if max_len > 0 else 0.0

def jaccard_similarity(set1, set2):
    """Returns Jaccard similarity between two sets (0.0 to 1.0)."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

# --- MAIN ANALYSIS ---

def analyze():
    print("Loading data...")
    untampered_files = glob.glob(os.path.join(DATA_DIR_UNTAMPERED, "*.json"))
    tampered_files = glob.glob(os.path.join(DATA_DIR_TAMPERED, "*.json"))
    
    if not untampered_files:
        print("Error: No untampered files found in data/untampered/")
        return

    # 1. Establish Baseline (Golden Reference)
    # We use the first valid file as the known good baseline
    with open(untampered_files[0], 'r') as f:
        golden_data = json.load(f)
        
    golden_builder = get_builder_id(golden_data)
    golden_env = get_env_keys(golden_data)
    
    print(f"Baseline Builder ID: {golden_builder}")
    
    records = []

    # 2. Process All Files
    all_files = [(f, 'untampered') for f in untampered_files] + \
                [(f, 'tampered') for f in tampered_files]

    for filepath, label in all_files:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Metric A: Builder ID Deviation (Normalized Distance)
        current_builder = get_builder_id(data)
        builder_dist = normalized_levenshtein(golden_builder, current_builder)
        
        # Metric B: Environment Similarity (Jaccard)
        current_env = get_env_keys(data)
        env_sim = jaccard_similarity(golden_env, current_env)
        
        # Convert Similarity to "Deviation" (1.0 - Similarity)
        env_deviation = 1.0 - env_sim

        records.append({
            "filename": os.path.basename(filepath),
            "label": label,
            "builder_id_deviation": builder_dist * 100, # Convert to %
            "env_var_deviation": env_deviation * 100    # Convert to %
        })

    # 3. Create DataFrame
    df = pd.DataFrame(records)
    
    # 4. Statistical Summary
    summary = df.groupby("label").mean(numeric_only=True)
    
    # Calculate the "Hypothesis Delta"
    untampered_means = summary.loc['untampered']
    tampered_means = summary.loc['tampered']
    
    delta = tampered_means - untampered_means
    
    print("\n--- RESULTS SUMMARY (Mean % Deviation) ---")
    print(summary)
    print("\n--- HYPOTHESIS CHECK (Target: >= 25% Delta) ---")
    print(delta)
    
    # Save Results
    csv_path = os.path.join(OUTPUT_DIR, "hypothesis1_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nDetailed CSV saved to: {csv_path}")

    # 5. Visual Plot
    plt.figure(figsize=(10, 6))
    categories = ['Builder ID', 'Environment']
    
    means_good = [untampered_means['builder_id_deviation'], untampered_means['env_var_deviation']]
    means_bad = [tampered_means['builder_id_deviation'], tampered_means['env_var_deviation']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    plt.bar(x - width/2, means_good, width, label='Untampered (Baseline)', color='green')
    plt.bar(x + width/2, means_bad, width, label='Tampered (Attack)', color='red')
    
    plt.axhline(y=25, color='black', linestyle='--', label='Threshold (25%)')
    
    plt.ylabel('% Deviation from Baseline')
    plt.title('Semantic Deviation: Tampered vs Untampered Artifacts')
    plt.xticks(x, categories)
    plt.legend()
    
    plot_path = os.path.join(OUTPUT_DIR, "hypothesis1_chart.png")
    plt.savefig(plot_path)
    print(f"Chart saved to: {plot_path}")

if __name__ == "__main__":
    analyze()