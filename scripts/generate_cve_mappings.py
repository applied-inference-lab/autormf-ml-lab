# scripts/generate_cve_mappings.py
import sqlite3
import os
import sys
import uuid
import argparse
from datetime import datetime
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

def main():
    parser = argparse.ArgumentParser(description="Generate proposed CVE-to-Control mapping records using local embeddings model.")
    parser.add_argument("--model-path", default=DEFAULT_MODEL, help="Path to SentenceTransformer model.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--recompute", action="store_true", help="Delete existing proposed mappings for non-adjudicated CVEs first.")
    parser.add_argument("--delta-cves-file", default=None, help="Path to text file containing list of changed CVE JSON files or CVE IDs.")
    args = parser.parse_args()

    model_path = args.model_path
    db_path = args.db_path
    recompute = args.recompute
    delta_cves_file = args.delta_cves_file

    if not os.path.exists(model_path):
        print(f"Error: Fine-tuned model directory not found at: {model_path}")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"Error: Database not found at: {db_path}")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading fine-tuned model from '{model_path}' on device: {device.upper()}...")
    model = SentenceTransformer(model_path, device=device)
    model.max_seq_length = 512

    print(f"Connecting to SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if recompute:
        print("Clearing out existing non-adjudicated proposed mappings to prepare for recomputation...")
        try:
            cursor.execute("""
                DELETE FROM PreComputedMappings 
                WHERE MappingType = 'PROPOSED'
                  AND SourceId NOT IN (
                      SELECT SourceId FROM PreComputedMappings 
                      WHERE MappingType IN ('USER_APPROVED', 'LOCKED')
                  )
            """)
            conn.commit()
            print(f"Cleared {cursor.rowcount} non-adjudicated proposed mappings.")
        except Exception as ex:
            print(f"Failed to clear existing mappings: {ex}")
            conn.close()
            sys.exit(1)

    print("Fetching NIST controls from database...")
    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()

    if not controls:
        print("Error: No controls found in NistControls table.")
        conn.close()
        sys.exit(1)

    control_ids = [cid for cid, _, _ in controls]
    control_texts = [f"{cid}: {title}. {desc}" for cid, title, desc in controls]

    if delta_cves_file and os.path.exists(delta_cves_file):
        print(f"Reading target CVE delta list from: {delta_cves_file}")
        with open(delta_cves_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        import re
        target_ids = set()
        for line in lines:
            match = re.search(r"(CVE-\d{4}-\d+)", line, re.IGNORECASE)
            if match:
                target_ids.add(match.group(1).upper())

        print(f"Targeting {len(target_ids)} CVEs from delta file for mapping generation...")

        if target_ids:
            placeholders = ",".join("?" * len(target_ids))
            cursor.execute(f"""
                SELECT CveId, Description FROM CveMetadatas 
                WHERE CveId IN ({placeholders})
                  AND Description IS NOT NULL 
                  AND length(Description) > 10
            """, list(target_ids))
            cves = cursor.fetchall()
        else:
            cves = []
    else:
        print("Fetching CVEs without active mapping records...")
        cursor.execute("""
            SELECT CveId, Description FROM CveMetadatas 
            WHERE CveId NOT IN (SELECT DISTINCT SourceId FROM PreComputedMappings)
              AND Description IS NOT NULL 
              AND length(Description) > 10
        """)
        cves = cursor.fetchall()

    if not cves:
        print("\nNo CVE records require mapping generation. Nothing to process.")
        conn.close()
        sys.exit(0)

    print(f"Found {len(cves)} CVE records to process in the database.")

    print(f"Embedding {len(controls)} controls...")
    control_vectors = model.encode(control_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    vectors_np = np.array(control_vectors).astype("float32")

    dimension = vectors_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_np)

    cve_ids = [cve[0] for cve in cves]
    cve_descs = [cve[1] for cve in cves]

    print(f"Embedding {len(cves)} CVEs...")
    query_prefix = "Represent this sentence for searching relevant passages: "
    query_texts = [f"{query_prefix}{desc}" for desc in cve_descs]

    query_vectors = model.encode(query_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    query_vectors_np = np.array(query_vectors).astype("float32")

    print("Running batch similarity search...")
    distances, indices = index.search(query_vectors_np, 3)

    insert_sql = """
        INSERT INTO PreComputedMappings (
            Id, SourceId, SourceType, ControlId, ConfidenceScore, 
            MappingType, AdjudicatorComments, AdjudicatedBy, AdjudicatedAt, 
            SyncPending, UpdatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    now_str = datetime.utcnow().isoformat() + "Z"
    new_records = []

    for idx, cve_id in enumerate(cve_ids):
        for rank in range(3):
            match_idx = indices[idx][rank]
            score = float(distances[idx][rank]) * 100.0
            matched_control = control_ids[match_idx]

            record_id = str(uuid.uuid4()).lower()
            comments = f"Proposed via local fine-tuned bge-base-en-v1.5. Rank: {rank+1}, Similarity: {score:.1f}%"

            row_data = (
                record_id,
                cve_id,
                "CVE",
                matched_control,
                round(score, 2),
                "PROPOSED",
                comments,
                None,
                None,
                0,
                now_str
            )
            new_records.append(row_data)

    cursor.executemany(insert_sql, new_records)
    conn.commit()

    print("\n" + "=" * 50)
    print("            MAPPING PIPELINE COMPLETE    ")
    print("=" * 50)
    print(f"Total CVEs processed     : {len(cve_ids)}")
    print(f"Total proposals inserted : {len(new_records)}")
    print(f"Database Updated         : {db_path}")
    print("=" * 50 + "\n")

    conn.close()

if __name__ == "__main__":
    main()
