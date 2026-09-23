# scripts/offline_rag_mapper.py
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
DEFAULT_URL = "http://localhost:1234/v1/embeddings"
DEFAULT_MODEL = "bge-large-en-v1.5"
DEFAULT_DIM = 1024

def get_embedding(api_url, model_name, text):
    payload = {
        "input": text,
        "model": model_name
    }
    response = requests.post(api_url, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    return result["data"][0]["embedding"]

def main():
    parser = argparse.ArgumentParser(description="Propose compliance control mappings for unmapped CVEs using offline embeddings API.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--inference-url", default=DEFAULT_URL, help="OpenAI-compatible embeddings endpoint URL.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL, help="Model name identifier on inference server.")
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIM, help="Embedding vector dimension.")
    parser.add_argument("--output", default="cmmc_proposals_seed.json", help="Output JSON proposals file.")
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print(f"Error: Database file not found at {args.db_path}")
        sys.exit(1)

    print(f"Connecting to database: {args.db_path}")
    conn = sqlite3.connect(args.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()

    if not controls:
        print("No controls found in NistControls table to map against.")
        conn.close()
        sys.exit(1)

    print(f"Loaded {len(controls)} controls from catalog. Generating embeddings...")
    control_vectors = []
    control_ids = []

    for cid, title, desc in controls:
        text = f"{cid}: {title}. {desc}"
        try:
            vector = get_embedding(args.inference_url, args.model_name, text)
            control_vectors.append(vector)
            control_ids.append(cid)
        except Exception as e:
            print(f"Failed to generate embedding for control {cid}: {e}")
            print(f"Verify that inference server is active at {args.inference_url}")
            conn.close()
            sys.exit(1)

    print("Building local FAISS index...")
    vectors_np = np.array(control_vectors).astype("float32")
    faiss.normalize_L2(vectors_np)

    index = faiss.IndexFlatIP(args.dimension)
    index.add(vectors_np)
    print("FAISS index populated successfully.")

    cursor.execute("""
        SELECT CveId, Description FROM CveMetadatas 
        WHERE CveId NOT IN (SELECT DISTINCT SourceId FROM PreComputedMappings)
    """)
    cves = cursor.fetchall()

    if not cves:
        print("All CVEs currently in the database have active mapping records. Nothing to map.")
        conn.close()
        sys.exit(0)

    print(f"Found {len(cves)} unmapped CVE records. Proposing mappings...")
    proposals = []
    skipped_count = 0

    for cve_id, desc in cves:
        if not desc or len(desc.strip()) < 10:
            skipped_count += 1
            continue

        try:
            cve_vector = np.array([get_embedding(args.inference_url, args.model_name, desc)]).astype("float32")
            faiss.normalize_L2(cve_vector)

            distances, indices = index.search(cve_vector, 3)

            for rank in range(3):
                match_idx = indices[0][rank]
                score = float(distances[0][rank]) * 100.0
                matched_control = control_ids[match_idx]

                proposals.append({
                    "SourceId": cve_id,
                    "SourceType": "CVE",
                    "ControlId": matched_control,
                    "ConfidenceScore": round(score, 2),
                    "MappingType": "PROPOSED",
                    "AdjudicatorComments": f"Proposed via offline RAG using {args.model_name}. Similarity: {score:.1f}%"
                })
        except Exception as e:
            print(f"Skipping CVE {cve_id} due to inference error: {e}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2)

    print("\nMapping execution complete.")
    print(f"Mapped {len(cves) - skipped_count} CVEs with top-3 recommendations.")
    print(f"Output written to: {args.output}")
    conn.close()

if __name__ == "__main__":
    main()
