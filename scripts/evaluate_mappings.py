# scripts/evaluate_mappings.py
import sqlite3
import json
import os
import sys
import argparse
import requests
import numpy as np

try:
    import faiss
except ImportError:
    print("Error: 'faiss' library is not installed.")
    print("Please install it: pip install faiss-cpu")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
DEFAULT_GOLDEN = os.path.join(REPO_ROOT, "data", "golden_validation_set.json")

def get_embeddings_batched(api_url, model_name, texts, batch_size=32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = requests.post(api_url, json={"input": batch, "model": model_name}, timeout=60)
            response.raise_for_status()
            data = response.json()["data"]
            data_sorted = sorted(data, key=lambda x: x["index"])
            for item in data_sorted:
                embeddings.append(item["embedding"])
        except Exception as e:
            print(f"Batch embedding failed for slice {i} to {i+len(batch)}: {e}")
            raise e
    return embeddings

def get_parent_id(control_id):
    if "(" in control_id:
        return control_id.split("(")[0].strip()
    return control_id

def evaluate_model(api_url, model_name, dimension, controls, golden_dataset, query_prefix=""):
    print(f"\nEvaluating Model: {model_name}...")

    control_texts = [f"{cid}: {title}. {desc}" for cid, title, desc in controls]
    control_ids = [cid for cid, _, _ in controls]

    print(f"  - Embedding {len(control_texts)} controls...")
    try:
        control_vectors = get_embeddings_batched(api_url, model_name, control_texts, batch_size=32)
    except Exception as e:
        print(f"Failed to generate control embeddings: {e}")
        return None

    vectors_np = np.array(control_vectors).astype("float32")
    faiss.normalize_L2(vectors_np)

    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_np)

    query_texts = [f"{query_prefix}{item['desc']}" for item in golden_dataset]
    print(f"  - Embedding {len(query_texts)} queries...")
    try:
        query_vectors = get_embeddings_batched(api_url, model_name, query_texts, batch_size=32)
    except Exception as e:
        print(f"Failed to generate query embeddings: {e}")
        return None

    query_vectors_np = np.array(query_vectors).astype("float32")
    faiss.normalize_L2(query_vectors_np)

    print("  - Running batch search evaluation...")
    distances, indices = index.search(query_vectors_np, 3)

    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0.0

    parent_hits_at_1 = 0
    parent_hits_at_3 = 0
    parent_mrr_sum = 0.0

    total = len(golden_dataset)

    for idx, item in enumerate(golden_dataset):
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

    print(f"Results for {model_name} (Strict):")
    print(f"  - Hit Rate @ 1: {hits_at_1 / total * 100:.1f}%")
    print(f"  - Hit Rate @ 3: {hits_at_3 / total * 100:.1f}%")
    print(f"  - MRR: {mrr_sum / total:.3f}")

    print(f"Results for {model_name} (Parent Control Roll-up):")
    print(f"  - Hit Rate @ 1: {parent_hits_at_1 / total * 100:.1f}%")
    print(f"  - Hit Rate @ 3: {parent_hits_at_3 / total * 100:.1f}%")
    print(f"  - MRR: {parent_mrr_sum / total:.3f}")

    return {
        "hr1": hits_at_1 / total, 
        "hr3": hits_at_3 / total, 
        "mrr": mrr_sum / total,
        "p_hr1": parent_hits_at_1 / total,
        "p_hr3": parent_hits_at_3 / total,
        "p_mrr": parent_mrr_sum / total
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare embedding endpoints against golden validation set.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to golden validation set.")
    parser.add_argument("--model-a-url", default="http://localhost:1234/v1/embeddings", help="URL for Model A endpoint.")
    parser.add_argument("--model-a-name", default="text-embedding-bge-large-en-v1.5", help="Name for Model A.")
    parser.add_argument("--model-a-dim", type=int, default=1024, help="Embedding dimension for Model A.")
    parser.add_argument("--model-b-url", default="http://10.27.27.89:1235/v1/embeddings", help="URL for Model B endpoint.")
    parser.add_argument("--model-b-name", default="text-embedding-gte-qwen2-7b-instruct", help="Name for Model B.")
    parser.add_argument("--model-b-dim", type=int, default=3584, help="Embedding dimension for Model B.")
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print(f"Error: DB file not found at {args.db_path}")
        sys.exit(1)

    if not os.path.exists(args.golden_file):
        print(f"Error: Golden validation set not found at {args.golden_file}")
        sys.exit(1)

    with open(args.golden_file, "r", encoding="utf-8") as f:
        golden_dataset = json.load(f)

    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()
    conn.close()

    bge_prefix = "Represent this sentence for searching relevant passages: "
    qwen_prefix = "Instruct: Given a vulnerability description, retrieve the matching compliance control\nQuery: "

    res_a = evaluate_model(args.model_a_url, args.model_a_name, args.model_a_dim, controls, golden_dataset, query_prefix=bge_prefix)
    res_b = evaluate_model(args.model_b_url, args.model_b_name, args.model_b_dim, controls, golden_dataset, query_prefix=qwen_prefix)

    if res_a and res_b:
        print("\n=== SIDE-BY-SIDE COMPARISON ===")
        print("Metric                    | Model A             | Model B")
        print("-" * 75)
        print(f"Strict Hit Rate @ 1       | {res_a['hr1']*100:.1f}%              | {res_b['hr1']*100:.1f}%")
        print(f"Strict Hit Rate @ 3       | {res_a['hr3']*100:.1f}%              | {res_b['hr3']*100:.1f}%")
        print(f"Strict MRR                | {res_a['mrr']:.3f}                | {res_b['mrr']:.3f}")
        print("-" * 75)
        print(f"Parent Roll-up Hit @ 1    | {res_a['p_hr1']*100:.1f}%              | {res_b['p_hr1']*100:.1f}%")
        print(f"Parent Roll-up Hit @ 3    | {res_a['p_hr3']*100:.1f}%              | {res_b['p_hr3']*100:.1f}%")
        print(f"Parent Roll-up MRR        | {res_a['p_mrr']:.3f}                | {res_b['p_mrr']:.3f}")

if __name__ == "__main__":
    main()
