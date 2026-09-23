# scripts/test_hybrid_search.py
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

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("Error: 'rank_bm25' library is not installed.")
    print("Please install it: pip install rank-bm25")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_MODEL = os.path.join(REPO_ROOT, "models", "bge-base-en-v1.5-fine-tuned")
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
DEFAULT_GOLDEN = os.path.join(REPO_ROOT, "data", "golden_validation_set.json")

def get_parent_id(control_id):
    if "(" in control_id:
        return control_id.split("(")[0].strip()
    return control_id

def tokenize(text):
    return text.lower().replace(".", " ").replace(",", " ").replace(":", " ").replace("-", " ").split()

def reciprocal_rank_fusion(dense_ranks, sparse_ranks, k=60):
    rrf_scores = {}
    for rank, item in enumerate(dense_ranks):
        rrf_scores[item] = rrf_scores.get(item, 0.0) + (1.0 / (k + rank + 1))
    for rank, item in enumerate(sparse_ranks):
        rrf_scores[item] = rrf_scores.get(item, 0.0) + (1.0 / (k + rank + 1))
    sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [item for item, score in sorted_candidates]

def main():
    parser = argparse.ArgumentParser(description="Evaluate Hybrid Search (Dense + BM25 with RRF).")
    parser.add_argument("--model-path", default=DEFAULT_MODEL, help="Path to dense model.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to golden validation dataset.")
    parser.add_argument("--rrf-k", type=int, default=60, help="Reciprocal Rank Fusion smoothing parameter.")
    args = parser.parse_args()

    if not os.path.exists(args.model_path):
        print(f"Error: Model not found at {args.model_path}")
        sys.exit(1)

    if not os.path.exists(args.db_path):
        print(f"Error: Database not found at {args.db_path}")
        sys.exit(1)

    if not os.path.exists(args.golden_file):
        print(f"Error: Golden validation set not found at {args.golden_file}")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading dense model from {args.model_path} on device: {device.upper()}...")
    model = SentenceTransformer(args.model_path, device=device)
    model.max_seq_length = 512

    with open(args.golden_file, "r", encoding="utf-8") as f:
        val_dataset = json.load(f)

    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()
    conn.close()

    control_ids = [cid for cid, _, _ in controls]
    control_texts = [f"{cid}: {title}. {desc}" for cid, title, desc in controls]

    print("Building BM25 sparse search index...")
    tokenized_corpus = [tokenize(text) for text in control_texts]
    bm25 = BM25Okapi(tokenized_corpus)

    print("Embedding controls for dense index...")
    control_vectors = model.encode(control_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    vectors_np = np.array(control_vectors).astype("float32")

    dimension = vectors_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_np)

    print("Embedding validation queries...")
    query_prefix = "Represent this sentence for searching relevant passages: "
    query_texts = [f"{query_prefix}{item['desc']}" for item in val_dataset]
    query_vectors = model.encode(query_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    query_vectors_np = np.array(query_vectors).astype("float32")

    print("Running dense search batch index queries...")
    dense_distances, dense_indices = index.search(query_vectors_np, 50)

    print(f"Evaluating Hybrid Search (Dense + BM25 Sparse with RRF k={args.rrf_k})...")
    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0.0

    parent_hits_at_1 = 0
    parent_hits_at_3 = 0
    parent_mrr_sum = 0.0

    total = len(val_dataset)

    for idx, item in enumerate(val_dataset):
        true_ctrl = item["true_control"]
        query_desc = item["desc"]

        dense_recs = [control_ids[dense_indices[idx][r]] for r in range(50)]

        tokenized_query = tokenize(query_desc)
        doc_scores = bm25.get_scores(tokenized_query)
        top_sparse_idx = np.argsort(doc_scores)[::-1][:50]
        sparse_recs = [control_ids[i] for i in top_sparse_idx]

        recommendations = reciprocal_rank_fusion(dense_recs, sparse_recs, k=args.rrf_k)[:3]

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
    print("            HYBRID SEARCH EVALUATION RESULTS      ")
    print("=" * 50)
    print(f"Dense Model: {args.model_path}")
    print(f"Sparse Method: BM25 Okapi")
    print(f"Fusion Rule: Reciprocal Rank Fusion (k={args.rrf_k})")
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

if __name__ == "__main__":
    main()
