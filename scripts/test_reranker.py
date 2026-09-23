# scripts/test_reranker.py
import sqlite3
import json
import os
import sys
import argparse
import numpy as np
import torch
import requests

try:
    import faiss
except ImportError:
    print("Error: 'faiss' library is not installed.")
    print("Please install it: pip install faiss-cpu")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
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

def rerank_via_local_cross_encoder(cross_encoder, query, candidates, controls_dict):
    pairs = [[query, f"{cid}: {controls_dict[cid]['title']}. {controls_dict[cid]['desc']}"] for cid in candidates]
    scores = cross_encoder.predict(pairs)
    ranked_candidates = [candidates[i] for i in np.argsort(scores)[::-1]]
    return ranked_candidates

def rerank_via_remote_llm(lm_studio_url, llm_model_name, query, candidates, controls_dict):
    options_text = ""
    for idx, cid in enumerate(candidates):
        options_text += f"{idx + 1}. Control ID: {cid}\n   Title: {controls_dict[cid]['title']}\n   Description: {controls_dict[cid]['desc']}\n\n"

    prompt = (
        "You are a compliance security mapping expert.\n"
        f"Analyze the following vulnerability description and rank the {len(candidates)} candidate controls below by their direct relevance to resolving or auditing this vulnerability.\n"
        "Your rank order must go from most relevant (rank 1) to least relevant.\n\n"
        f"Vulnerability Description:\n\"{query}\"\n\n"
        f"Candidate Controls:\n{options_text}"
        f"Return ONLY a raw JSON string containing a list of the Control IDs in order, for example: [\"{candidates[0]}\", \"{candidates[1]}\"].\n"
        "Do not include markdown blocks, explanation text, or formatting. Output only the raw JSON list."
    )

    try:
        payload = {
            "model": llm_model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 100
        }

        response = requests.post(lm_studio_url, json=payload, timeout=15)
        response.raise_for_status()
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1]).strip()

        ranked_list = json.loads(content)
        cleaned_list = [cid.strip().upper() for cid in ranked_list if cid.strip().upper() in candidates]

        for cid in candidates:
            if cid not in cleaned_list:
                cleaned_list.append(cid)

        return cleaned_list
    except Exception as e:
        print(f"Warning: Remote LLM reranking failed: {e}. Falling back to default order.")
        return candidates

def main():
    parser = argparse.ArgumentParser(description="Evaluate candidate reranking using local Cross-Encoder or remote LLM.")
    parser.add_argument("mode", choices=["local", "remote"], help="Reranking mode: local or remote.")
    parser.add_argument("--model-path", default=DEFAULT_MODEL, help="Path to dense retriever model.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to golden validation dataset.")
    parser.add_argument("--lm-studio-url", default="http://10.27.27.89:1235/v1/chat/completions", help="Remote LLM completions endpoint.")
    parser.add_argument("--llm-model-name", default="qwen2.5-7b-instruct", help="Name of model on remote endpoint.")
    parser.add_argument("--sample-limit", type=int, default=100, help="Limit sample count for remote evaluation.")
    args = parser.parse_args()

    mode = args.mode

    if not os.path.exists(args.model_path):
        print(f"Error: Model not found at {args.model_path}")
        sys.exit(1)

    if not os.path.exists(args.db_path):
        print(f"Error: Database not found at {args.db_path}")
        sys.exit(1)

    if not os.path.exists(args.golden_file):
        print(f"Error: Golden validation set not found at {args.golden_file}")
        sys.exit(1)

    cross_encoder = None
    if mode == "local":
        print("Loading local Cross-Encoder ('BAAI/bge-reranker-base')...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        cross_encoder = CrossEncoder("BAAI/bge-reranker-base", device=device)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading dense retriever from {args.model_path} on device: {device.upper()}...")
    retriever_model = SentenceTransformer(args.model_path, device=device)
    retriever_model.max_seq_length = 512

    with open(args.golden_file, "r", encoding="utf-8") as f:
        val_dataset = json.load(f)

    if mode == "remote" and args.sample_limit:
        print(f"Limiting evaluation to first {args.sample_limit} samples for remote API speed...")
        val_dataset = val_dataset[:args.sample_limit]

    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()
    conn.close()

    control_ids = [cid for cid, _, _ in controls]
    control_texts = [f"{cid}: {title}. {desc}" for cid, title, desc in controls]
    controls_dict = {cid: {"title": title, "desc": desc} for cid, title, desc in controls}

    print("Embedding controls for first-stage retrieval...")
    control_vectors = retriever_model.encode(control_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    vectors_np = np.array(control_vectors).astype("float32")

    dimension = vectors_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_np)

    print("Embedding validation queries...")
    query_prefix = "Represent this sentence for searching relevant passages: "
    query_texts = [f"{query_prefix}{item['desc']}" for item in val_dataset]
    query_vectors = retriever_model.encode(query_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    query_vectors_np = np.array(query_vectors).astype("float32")

    print("Running first-stage retrieval (top 10)...")
    distances, indices = index.search(query_vectors_np, 10)

    print(f"Running reranking evaluation using mode: {mode.upper()}...")
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

        candidates = [control_ids[indices[idx][r]] for r in range(10)]

        if mode == "local":
            recommendations = rerank_via_local_cross_encoder(cross_encoder, query_desc, candidates, controls_dict)[:3]
        else:
            print(f" [{idx + 1}/{total}] Reranking CVE: {item['cve_id']}...")
            recommendations = rerank_via_remote_llm(args.lm_studio_url, args.llm_model_name, query_desc, candidates, controls_dict)[:3]

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
    print(f"            RERANKING RESULTS ({mode.upper()})      ")
    print("=" * 50)
    print(f"First-Stage Model: {args.model_path}")
    if mode == "local":
        print("Rerank Model: BAAI/bge-reranker-base (Local Cross-Encoder)")
    else:
        print(f"Rerank Model: {args.llm_model_name} at {args.lm_studio_url}")
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
