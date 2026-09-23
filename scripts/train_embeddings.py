# scripts/train_embeddings.py
import sqlite3
import json
import os
import sys
import argparse
import torch
from torch.utils.data import DataLoader

try:
    from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
except ImportError:
    print("Error: 'sentence-transformers' library is not installed.")
    print("Please install it: pip install sentence-transformers torch")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "models", "bge-base-en-v1.5-fine-tuned")
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
DEFAULT_GOLDEN = os.path.join(REPO_ROOT, "data", "golden_validation_set.json")

def main():
    parser = argparse.ArgumentParser(description="Fine-tune local SentenceTransformer embeddings on CVE-to-Control pairs.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Output directory to save retrained model weights.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to golden validation dataset JSON.")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for training.")
    args = parser.parse_args()

    db_path = args.db_path
    golden_file = args.golden_file
    output_dir = args.output_dir

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using Device: {device.upper()}")

    val_cves = set()
    val_data = []
    if os.path.exists(golden_file):
        print(f"Loading golden validation set from {golden_file} to isolate from training data...")
        with open(golden_file, "r", encoding="utf-8") as f:
            val_data = json.load(f)
            val_cves = {item["cve_id"] for item in val_data}
    else:
        print(f"Warning: {golden_file} not found.")
        sys.exit(1)

    print("Extracting positive training pairs from SQLite database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT c.CveId, m.ControlId, c.Description, n.Title, n.Description
        FROM CveMetadatas c
        JOIN CweControlMaps m ON c.CweId = m.CweId
        JOIN NistControls n ON m.ControlId = n.ControlId
        WHERE c.Description IS NOT NULL AND length(c.Description) > 20
    """)
    rows = cursor.fetchall()

    cursor.execute("SELECT ControlId, Title, Description FROM NistControls")
    controls = cursor.fetchall()
    conn.close()

    train_examples = []
    excluded_count = 0

    for cve_id, control_id, cve_desc, ctrl_title, ctrl_desc in rows:
        if cve_id in val_cves:
            excluded_count += 1
            continue

        control_text = f"{control_id}: {ctrl_title}. {ctrl_desc}"
        train_examples.append(InputExample(texts=[cve_desc, control_text]))

    print(f"Loaded {len(train_examples)} training pairs (Excluded {excluded_count} validation pairs).")

    if not train_examples:
        print("Error: No training data found.")
        sys.exit(1)

    model_name = "BAAI/bge-base-en-v1.5"
    print(f"Loading base model '{model_name}'...")
    model = SentenceTransformer(model_name, device=device)

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    print("Setting up Information Retrieval Evaluator...")
    queries = {}
    corpus = {}
    relevant_docs = {}

    for cid, title, desc in controls:
        corpus[cid] = f"{cid}: {title}. {desc}"

    for i, item in enumerate(val_data):
        q_id = f"q_{i}"
        queries[q_id] = item["desc"]
        relevant_docs[q_id] = {item["true_control"]}

    evaluator = evaluation.InformationRetrievalEvaluator(
        queries, corpus, relevant_docs, 
        name="nist_validation",
        show_progress_bar=True
    )

    print(f"\nStarting model fine-tuning. Output will be saved to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=args.epochs,
        warmup_steps=100,
        output_path=output_dir,
        show_progress_bar=True,
        evaluation_steps=500
    )

    print("\nFine-tuning complete. Model weights saved successfully.")

if __name__ == "__main__":
    main()
