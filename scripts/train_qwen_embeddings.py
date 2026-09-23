# scripts/train_qwen_embeddings.py
import sqlite3
import json
import os
import sys
import argparse
import torch
from torch.utils.data import DataLoader

try:
    from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
    from peft import LoraConfig, get_peft_model
except ImportError:
    print("Error: 'sentence-transformers', 'peft', or 'accelerate' libraries are not installed.")
    print("Please install them: pip install sentence-transformers peft accelerate transformers torch")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "models", "gte-qwen2-7b-adjudicated-lora")
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
DEFAULT_GOLDEN = os.path.join(REPO_ROOT, "data", "golden_validation_set.json")

def main():
    parser = argparse.ArgumentParser(description="Fine-tune GTE-Qwen2-7B-instruct with LoRA adapters.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Output directory for LoRA adapter.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--golden-file", default=DEFAULT_GOLDEN, help="Path to golden validation dataset JSON.")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training.")
    parser.add_argument("--lora-r", type=int, default=64, help="LoRA rank parameter.")
    parser.add_argument("--lora-alpha", type=int, default=128, help="LoRA alpha parameter.")
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print(f"Error: Database not found at {args.db_path}")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    print(f"Using Device: {device.upper()} | Data Type: {dtype}")

    val_cves = set()
    val_data = []
    if os.path.exists(args.golden_file):
        print(f"Loading validation set from {args.golden_file}...")
        with open(args.golden_file, "r", encoding="utf-8") as f:
            val_data = json.load(f)
            val_cves = {item["cve_id"] for item in val_data}
    else:
        print(f"Warning: {args.golden_file} not found.")
        sys.exit(1)

    print("Retrieving mapping associations from database...")
    conn = sqlite3.connect(args.db_path)
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
    query_prefix = "Instruct: Given a vulnerability description, retrieve the matching compliance control\nQuery: "

    for cve_id, control_id, cve_desc, ctrl_title, ctrl_desc in rows:
        if cve_id in val_cves:
            excluded_count += 1
            continue

        formatted_query = f"{query_prefix}{cve_desc}"
        formatted_control = f"{control_id}: {ctrl_title}. {ctrl_desc}"
        train_examples.append(InputExample(texts=[formatted_query, formatted_control]))

    print(f"Loaded {len(train_examples)} training pairs (Excluded {excluded_count} validation pairs).")

    if not train_examples:
        print("Error: No training data available.")
        sys.exit(1)

    model_name = "Alibaba-NLP/gte-Qwen2-7B-instruct"
    print(f"Loading '{model_name}'...")

    model = SentenceTransformer(
        model_name,
        trust_remote_code=True,
        model_kwargs={
            "torch_dtype": dtype,
            "trust_remote_code": True
        },
        device=device
    )

    if model.tokenizer.pad_token is None:
        model.tokenizer.pad_token = model.tokenizer.eos_token

    print(f"Wrapping model in LoRA (r={args.lora_r}, alpha={args.lora_alpha})...")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="FEATURE_EXTRACTION"
    )

    model[0].auto_model = get_peft_model(model[0].auto_model, lora_config)
    model[0].auto_model.print_trainable_parameters()

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    print("Structuring validation dataset with GTE instructions...")
    queries = {}
    corpus = {}
    relevant_docs = {}

    for cid, title, desc in controls:
        corpus[cid] = f"{cid}: {title}. {desc}"

    for i, item in enumerate(val_data):
        q_id = f"q_{i}"
        queries[q_id] = f"{query_prefix}{item['desc']}"
        relevant_docs[q_id] = {item["true_control"]}

    evaluator = evaluation.InformationRetrievalEvaluator(
        queries, corpus, relevant_docs, 
        name="gte_qwen2_validation",
        show_progress_bar=True
    )

    print(f"\nFine-tuning Qwen2-7B LoRA adapters. Output will be saved to: {args.output_dir}")
    os.makedirs(os.path.dirname(args.output_dir), exist_ok=True)

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=args.epochs,
        warmup_steps=50,
        output_path=args.output_dir,
        show_progress_bar=True,
        evaluation_steps=200
    )

    print("\nFine-tuning complete. Qwen2 LoRA adapters saved successfully.")

if __name__ == "__main__":
    main()
