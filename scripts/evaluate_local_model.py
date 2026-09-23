# scripts/evaluate_local_model.py
import sqlite3
import json
import os
import sys
import argparse
import numpy as np
import torch

try:
    import faiss
except ImportError:
    print("Error: 'faiss' library is not installed.")
    print("Please install it: pip install faiss-cpu")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: 'sentence-transformers' library is not installed.")
    print("Please install it: pip install sentence-transformers")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_MODEL = os.path.join(REPO_ROOT, "models", "bge-base-en-v1.5-fine-tuned")
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
DEFAULT_GOLDEN = os.path.join(REPO_ROOT, "data", "golden_validation_set.json")

def get_parent_id(control_id):
    if "(" in control_id:
        return control_id.split("(")[0].strip()
    return control_id

def main():
    parser = argparse.ArgumentParser(description="Evaluate SentenceTransformer embeddings against a golden validation set.")
    parser.add_argument("--model-path", default=DEFAULT_MODEL, help="Path to the model directory.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to validation set JSON.")
    parser.add_argument("--json-output", default=None, help="Optional path to output results as a JSON file.")
    args = parser.parse_args()

    model_path = args.model_path
    db_path = args.db_path
    golden_file = args.golden_file
    json_output = args.json_output

    if not os.path.exists(model_path):
        print(f"Error: Fine-tuned model directory not found at: {model_path}")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"Error: Database not found at: {db_path}")
        sys.exit(1)

    if not os.path.exists(golden_file):
        print(f"Error: Validation dataset not found at: {golden_file}")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading fine-tuned model from '{model_path}' on device: {device.upper()}...")
    model = SentenceTransformer(model_path, device=device)
    model.max_seq_length = 512

    print(f"Loading validation dataset from {golden_file}...")
    with open(golden_file, "r", encoding="utf-8") as f:
        val_dataset = json.load(f)

    print("Fetching NIST controls from SQLite database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()
    conn.close()

    print(f"Embedding {len(controls)} controls...")
    control_texts = [f"{cid}: {title}. {desc}" for cid, title, desc in controls]
    control_ids = [cid for cid, _, _ in controls]

    control_vectors = model.encode(control_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    vectors_np = np.array(control_vectors).astype("float32")

    dimension = vectors_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_np)

    print(f"Embedding {len(val_dataset)} validation queries...")
    query_prefix = "Represent this sentence for searching relevant passages: "
    query_texts = [f"{query_prefix}{item['desc']}" for item in val_dataset]

    query_vectors = model.encode(query_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    query_vectors_np = np.array(query_vectors).astype("float32")

    print("Running batch search evaluation...")
    distances, indices = index.search(query_vectors_np, 3)

    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0.0

    parent_hits_at_1 = 0
    parent_hits_at_3 = 0
    parent_mrr_sum = 0.0

    total = len(val_dataset)

    for idx, item in enumerate(val_dataset):
        true_ctrl = item["true_control"]
        recommendations = [control_ids[indices[idx][r]] for r in range(3)]

        if recommendations[0] == true_ctrl:
            hits_at_1 += 1
        if true_ctrl in recommendations:
            hits_at_3 += 1
            rank = recommendations.index(true_ctrl) + 1
            mrr_sum += 1.0 / rank

        true_parent = get_parent_id(true_ctrl)
        rec_parents = [get_parent_id(r) for r in recommendations]

        if rec_parents[0] == true_parent:
            parent_hits_at_1 += 1
        if true_parent in rec_parents:
            parent_hits_at_3 += 1
            rank = rec_parents.index(true_parent) + 1
            parent_mrr_sum += 1.0 / rank

    print("\n" + "=" * 50)
    print("            EVALUATION RESULTS (LOCAL MODEL)      ")
    print("=" * 50)
    print(f"Model Path: {model_path}")
    print(f"Total Validation Samples: {total}")
    print("-" * 50)
    print(f"Strict Hit Rate @ 1       : {hits_at_1 / total * 100:.2f}%")
    print(f"Strict Hit Rate @ 3       : {hits_at_3 / total * 100:.2f}%")
    print(f"Strict MRR                : {mrr_sum / total:.4f}")
    print("-" * 50)
    print(f"Parent Roll-up Hit @ 1    : {parent_hits_at_1 / total * 100:.2f}%")
    print(f"Parent Roll-up Hit @ 3    : {parent_hits_at_3 / total * 100:.2f}%")
    print(f"Parent Roll-up MRR        : {parent_mrr_sum / total:.4f}")
    print("=" * 50 + "\n")

    if json_output:
        metrics = {
            "hr1": hits_at_1 / total,
            "hr3": hits_at_3 / total,
            "mrr": mrr_sum / total,
            "p_hr1": parent_hits_at_1 / total,
            "p_hr3": parent_hits_at_3 / total,
            "p_mrr": parent_mrr_sum / total,
            "total_samples": total
        }
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics saved to {json_output}")

if __name__ == "__main__":
    main()
