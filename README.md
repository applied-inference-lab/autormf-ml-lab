# Applied Inference Lab: Compliance Control Embedding Stack

An open-source machine learning framework for mapping technical software vulnerabilities (CVE descriptions) to formal cybersecurity compliance controls (NIST SP 800-53 Rev 5 and CMMC).

Developed by James Pusateri (Middle Coast Software Inc.) and published under the Applied Inference Lab initiative.

## Overview

Correlating technical vulnerability scans with regulatory compliance frameworks is a persistent operational bottleneck in cybersecurity compliance programs. Technical vulnerability descriptions (such as memory corruption, buffer overflows, or authentication bypasses) inhabit a different vocabulary space than administrative compliance controls (such as flaw remediation, boundary protection, or audit logging).

This repository provides the complete model generation, contrastive fine-tuning, evaluation, and GGUF quantization pipeline developed for AutoRMF. Middle Coast Software Inc. has elected to open source this architecture as a contribution to the cybersecurity and machine learning communities.

## Key Empirical Findings

Evaluating standard approaches against an isolated 2,000-sample golden validation dataset revealed critical insights that contradict common enterprise search assumptions:

1. Zero-shot foundation models fail: Off-the-shelf embedding models (such as BGE-Large and GTE-Qwen2-7B) achieve less than 1.0% strict top-1 accuracy out of the box.
2. Domain contrastive fine-tuning succeeds: Fine-tuning a compact 110-million parameter encoder (BGE-Base) using Multiple Negatives Ranking Loss (MNRL) increases strict top-1 retrieval to 77.45% and parent control roll-up top-3 retrieval to 87.15%.
3. Generative LLM reranking degrades accuracy: Using a 7-billion parameter generative model (Qwen2.5-7B-Instruct) downstream of dense retrieval reduced top-1 accuracy from 77.45% to 72.00%, as the general-purpose model over-indexed on secondary operational cues.
4. Lexical hybrid search causes rank collapse: Fusing sparse BM25 Okapi keyword matching with dense embeddings using Reciprocal Rank Fusion (RRF) caused strict top-1 accuracy to plummet from 77.45% to 13.65% due to lexical rank poisoning across mismatched vocabularies.

## Benchmark Results

All evaluations were conducted against the full NIST SP 800-53 Rev 5 catalog (1,196 controls) using an isolated 2,000-sample validation dataset.

| **Model / Architecture** | **Strict HR@1** | **Strict HR@3** | **Strict MRR** | **Parent HR@1** | **Parent HR@3** | **Parent MRR** |
|---|---|---|---|---|---|---|
| gte-Qwen2-7B-instruct (Zero-Shot) | 0.10% | 0.40% | 0.0030 | 0.40% | 1.10% | 0.0070 |
| bge-large-en-v1.5 (Zero-Shot) | 0.30% | 0.90% | 0.0050 | 8.40% | 18.60% | 0.1270 |
| bge-base-en-v1.5 (Fine-Tuned) | 77.45% | 82.15% | 0.7947 | 81.95% | 87.15% | 0.8422 |
| BGE-Base + Qwen2.5 Reranker | 72.00% | 80.00% | 0.7600 | 82.00% | 86.00% | 0.8400 |
| BGE-Base + BM25 Hybrid (RRF) | 13.65% | 58.10% | 0.3305 | 21.95% | 66.25% | 0.4155 |

## Repository Structure

```
├── data/
│   ├── autormf.db                     # Standalone SQLite database containing control catalogs and mappings
│   ├── golden_validation_set.json     # Isolated 2,000-item evaluation benchmark
│   ├── nist_seed.json                 # NIST SP 800-53 Rev 5 control catalog
│   ├── cwe_seed.json                  # Common Weakness Enumeration to NIST mappings
│   └── sp800-53r5-control-catalog.csv # Reference control catalog export
├── docs/
│   ├── 10_static_mapping_and_ml_pipeline_design.md
│   ├── 12_model_conversion_guide.md
│   ├── 13_model_retraining_and_overfitting_safeguards.md
│   └── 18_model_training_eval_and_cve_api_summary.md
├── models/
│   └── nist_control_embeddings_cache.json
├── scripts/
│   ├── init_db.py                     # SQLite database generator from catalog seeds
│   ├── train_embeddings.py            # BGE-Base contrastive fine-tuning with MNRL
│   ├── train_qwen_embeddings.py       # High-capacity GTE-Qwen2-7B LoRA adapter fine-tuning
│   ├── evaluate_local_model.py        # Local evaluation suite for SentenceTransformers
│   ├── evaluate_mappings.py           # Comparative evaluation harness for HTTP endpoints
│   ├── test_reranker.py               # Local Cross-Encoder and remote LLM reranking testbed
│   ├── test_hybrid_search.py          # Dense + BM25 Reciprocal Rank Fusion testbed
│   ├── offline_rag_mapper.py          # Batch FAISS vector retrieval script
│   ├── generate_cve_mappings.py       # Delta-aware mapping generation pipeline
│   ├── merge_lora.py                  # LoRA adapter weight merger for GGUF export
│   └── run_eval.ps1                   # Automated evaluation runner
├── requirements.txt
├── LICENSE
└── README.md
```

## Environment Setup

All scripts require Python 3.10 or later and should be executed within a virtual environment.

### 1. Create and Activate Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Verify Database Setup

If `data/autormf.db` is present, it is ready for immediate use. To initialize or verify the schema from catalog seed files:
```powershell
python scripts/init_db.py
```

## Running the Evaluation Suite

To evaluate the fine-tuned model against the 2,000-sample golden validation dataset:
```powershell
python scripts/evaluate_local_model.py --model-path models/bge-base-en-v1.5-fine-tuned
```

To run the automated PowerShell evaluation runner:
```powershell
.\scripts\run_eval.ps1
```

## Reproducing Architecture Experiments

### Testing Downstream LLM Reranking
To reproduce the reranking experiment using a local Cross-Encoder:
```powershell
python scripts/test_reranker.py local
```

To test with a remote OpenAI-compatible server hosting an instruction model (such as Qwen2.5-7B-Instruct):
```powershell
python scripts/test_reranker.py remote --lm-studio-url http://localhost:1234/v1/chat/completions --llm-model-name qwen2.5-7b-instruct
```

### Testing Hybrid Lexical Search (BM25 + Dense)
To reproduce the hybrid search experiment demonstrating lexical rank dilution:
```powershell
python scripts/test_hybrid_search.py --rrf-k 60
```

## Training and Fine-Tuning

### Fine-Tuning BGE-Base with Multiple Negatives Ranking Loss
```powershell
python scripts/train_embeddings.py --output-dir models/bge-base-en-v1.5-fine-tuned --epochs 3 --batch-size 8
```

The script automatically isolates all queries present in `data/golden_validation_set.json` to prevent evaluation data leakage.

### Fine-Tuning GTE-Qwen2-7B with LoRA
For high-capacity environments (such as machines with unified memory or high-memory GPUs):
```powershell
python scripts/train_qwen_embeddings.py --output-dir models/gte-qwen2-7b-adjudicated-lora --epochs 3 --batch-size 32
```

To merge LoRA weights back into the base architecture for export:
```powershell
python scripts/merge_lora.py --adapter-path models/gte-qwen2-7b-adjudicated-lora --output-path models/gte-qwen2-7b-merged
```

## Model Quantization and In-Process Hosting

To convert fine-tuned Hugging Face weights to GGUF format for low-memory, in-process inference via llama.cpp or LLamaSharp:

1. Clone llama.cpp:
```powershell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
pip install -r requirements-convert-hf-to-gguf.txt
```

2. Convert weights to GGUF:
```powershell
python convert_hf_to_gguf.py ../models/bge-base-en-v1.5-fine-tuned/ --outfile ../models/bge-base-en-v1.5-fine-tuned.gguf
```

3. Quantize to Q8_0 precision:
```powershell
./llama-quantize ../models/bge-base-en-v1.5-fine-tuned.gguf ../models/bge-base-en-v1.5-fine-tuned-q8_0.gguf Q8_0
```

For comprehensive conversion details, consult `docs/12_model_conversion_guide.md`.

## License and Attribution

This project is licensed under the Apache License, Version 2.0. See the `LICENSE` file for details.

Copyright 2026 Middle Coast Software Inc.
