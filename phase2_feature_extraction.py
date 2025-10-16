"""
PHASE 2: Feature Extraction for Hypothesis-1
--------------------------------------------
This script unzips the final provenance dataset and extracts
structured metadata fields from both tampered and untampered samples.

Outputs:
    - hypothesis1_features.csv
    - hypothesis1_features.jsonl
"""

import os
import re
import json
import math
import zipfile
from datetime import datetime
import pandas as pd

# =========================================================
# Helper Functions
# =========================================================

def is_base64_like(s: str) -> bool:
    """Heuristic check for long base64-like strings."""
    if not isinstance(s, str):
        return False
    if len(s) < 40:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=\s]+", s) is not None and any(ch in s for ch in "+/=")

def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy per character."""
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    ent = 0.0
    for c in freq.values():
        p = c / length
        ent -= p * math.log2(p)
    return ent

def collect_base64_strings(obj):
    """Recursively collect all base64-like strings from nested dict/list."""
    acc = []
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, (dict, list)):
                acc.extend(collect_base64_strings(v))
            elif isinstance(v, str) and is_base64_like(v):
                acc.append(v.strip())
    elif isinstance(obj, list):
        for v in obj:
            acc.extend(collect_base64_strings(v))
    return acc

def parse_iso8601_maybe(s: str):
    """Try multiple ISO-8601 timestamp formats."""
    if not s or not isinstance(s, str):
        return None
    s2 = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s2)
    except Exception:
        try:
            return datetime.strptime(s.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None

def get_nested(d, path, default=None):
    """Traverse nested keys safely."""
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def extract_times(payload):
    """Extract start/finish times and compute delta (seconds)."""
    started = get_nested(payload, ["metadata", "startedOn"], None) or \
              get_nested(payload, ["invocation", "startedOn"], None)
    finished = get_nested(payload, ["metadata", "finishedOn"], None) or \
               get_nested(payload, ["invocation", "finishedOn"], None)
    t_start = parse_iso8601_maybe(started) if started else None
    t_finish = parse_iso8601_maybe(finished) if finished else None
    delta = (t_finish - t_start).total_seconds() if t_start and t_finish else None
    return started, finished, delta

def first_subject_digest(payload):
    """Return first artifact digest (sha256 preferred)."""
    subj = payload.get("subject")
    if isinstance(subj, list) and subj:
        dig = subj[0].get("digest", {})
        if isinstance(dig, dict):
            if "sha256" in dig:
                return f"sha256:{dig['sha256']}"
            for k, v in dig.items():
                return f"{k}:{v}"
    return None

def extract_commands(payload):
    """Extract up to three build commands from recipe steps."""
    steps = get_nested(payload, ["recipe", "steps"], [])
    cmds = []
    if isinstance(steps, list):
        for s in steps:
            if isinstance(s, dict):
                if "command" in s and isinstance(s["command"], str):
                    cmds.append(s["command"])
                elif "args" in s and isinstance(s["args"], list):
                    cmds.append(" ".join(map(str, s["args"])))
    return cmds[:3]

# =========================================================
# Unzip and Parse
# =========================================================

zip_path = "Final Datasets.zip"            # <== your input zip
extract_dir = "final_datasets_extracted"   # temporary extraction path
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(extract_dir)

tampered_dir = os.path.join(extract_dir, "tampered_provenance_sample")
untampered_dir = os.path.join(extract_dir, "untampered_provenance_sample")

records = []

def process_file(file_path, rel_path, label):
    """Handle both JSON and JSONL provenance files."""
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                # if single JSON blob, reload whole file
                try:
                    payload = json.loads(open(file_path, "r", encoding="utf-8").read())
                except Exception:
                    continue

            builder_id = get_nested(payload, ["builder", "id"], None)
            materials = payload.get("materials", [])
            materials_count = len(materials) if isinstance(materials, list) else None
            commands = extract_commands(payload)
            startedOn, finishedOn, time_delta_sec = extract_times(payload)
            subject_dig = first_subject_digest(payload)
            b64_strings = collect_base64_strings(payload)
            entropy_b64 = round(shannon_entropy("".join(b64_strings)), 4) if b64_strings else 0.0

            records.append({
                "id": f"{os.path.splitext(os.path.basename(file_path))[0]}#{idx}",
                "path": rel_path,
                "label": label,
                "builder_id": builder_id,
                "materials_count": materials_count,
                "command_sample": commands,
                "startedOn": startedOn,
                "finishedOn": finishedOn,
                "time_delta_sec": time_delta_sec,
                "entropy_b64": entropy_b64,
                "subject_digest": subject_dig
            })
            count += 1
    return count

# Process both directories
for label, base_dir in [("tampered", tampered_dir), ("untampered", untampered_dir)]:
    if not os.path.isdir(base_dir):
        continue
    for root, _, files in os.walk(base_dir):
        for fn in files:
            if not (fn.lower().endswith(".json") or fn.lower().endswith(".jsonl")):
                continue
            fpath = os.path.join(root, fn)
            rel_path = os.path.relpath(fpath, extract_dir).replace("\\", "/")
            process_file(fpath, rel_path, label)

# =========================================================
# Save Outputs
# =========================================================

df = pd.DataFrame(records)

csv_out = "hypothesis1_features.csv"
jsonl_out = "hypothesis1_features.jsonl"

df.to_csv(csv_out, index=False)

with open(jsonl_out, "w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec) + "\n")

print(f"[✓] Extracted {len(df)} provenance records")
print(f"[✓] Saved to {csv_out} and {jsonl_out}")
print(df.head(5))
