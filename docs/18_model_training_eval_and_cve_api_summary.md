# Model Training, Evaluation Benchmarks, and CVE API Specification

This document provides a unified, succinct summary of AutoRMF's AI model training architecture, golden validation set evaluation metrics, and the commercial CVE API service.

---

## 1. AI Model Training Architecture

AutoRMF utilizes a specialized, domain-tuned contrastive embedding model to map vulnerability descriptions (CVE summaries and scan finding titles) to security and compliance controls (NIST SP 800-53 Rev 5 / CMMC).

### 1.1 Base Model & Training Mechanics
* **Base Model:** `BAAI/bge-base-en-v1.5` (768-dimension dense vector space, 512 token context window).
* **Loss Function:** `MultipleNegativesRankingLoss` (MNRL) via `sentence-transformers`, using in-batch negatives for high-efficiency contrastive representation learning.
* **Training Corpus:** Pairs extracted from `CveMetadatas` joined to `NistControls` via `CweControlMaps` and expert-reviewed auditor mappings.
* **Data Contamination Safeguards:** Training scripts explicitly isolate all queries present in [`golden_validation_set.json`](file:///c:/repos/AutoRMF/docs/scripts/golden_validation_set.json) prior to fine-tuning.
* **Training Script:** [`docs/scripts/train_embeddings.py`](file:///c:/repos/AutoRMF/docs/scripts/train_embeddings.py) (includes `InformationRetrievalEvaluator` per epoch).

### 1.2 Model Conversion & In-Process Hosting
* **Quantization & GGUF Conversion:** Fine-tuned Hugging Face weights are converted to GGUF format (`bge-base-en-v1.5-fine-tuned.gguf`) using `llama.cpp`. See [`docs/12_model_conversion_guide.md`](file:///c:/repos/AutoRMF/docs/12_model_conversion_guide.md).
* **In-Process Engine Hosting:** Loaded directly in-process within ASP.NET Core (`AutoRMF.Engine`) using **`LLamaSharp`** (`v0.27.0`) via [`LlamaEmbeddingsService`](file:///c:/repos/AutoRMF/src/AutoRMF.Engine/Services/LlamaEmbeddingsService.cs#L41).
* **Disk Caching:** Precomputes and caches 1,196 NIST control vector embeddings into [`nist_control_embeddings_cache.json`](file:///c:/repos/AutoRMF/src/AutoRMF.Engine/Services/LlamaEmbeddingsService.cs#L103) for fast container startup (<5ms).

---

## 2. Evaluation Results & Architectural Decisions

Model retrieval performance is continuously benchmarked against a 2,000-item validation suite ([`golden_validation_set.json`](file:///c:/repos/AutoRMF/docs/scripts/golden_validation_set.json)) measuring **Hit Rate @ K** and **Mean Reciprocal Rank (MRR)**.

### 2.1 Retrieval Performance Benchmarks

| Architecture / Model Variant | Strict HR@1 | Strict HR@3 | Strict MRR | Parent Roll-up HR@1 | Parent Roll-up HR@3 | Parent Roll-up MRR |
|---|---|---|---|---|---|---|
| **`gte-qwen2-7b-instruct`** *(Zero-Shot)* | 0.1% | 0.4% | 0.003 | 0.4% | 1.1% | 0.007 |
| **`bge-large-en-v1.5`** *(Zero-Shot)* | 0.3% | 0.9% | 0.005 | 8.4% | 18.6% | 0.127 |
| **`bge-base-en-v1.5`** *(Fine-Tuned)* | **77.5%** | **82.2%** | **0.795** | **82.0%** | **87.2%** | **0.842** |

### 2.2 Reranking & Hybrid Search Findings
* **LLM Reranking (Qwen2.5-7B-Instruct):** Combining the fine-tuned model with a downstream LLM reranker *decreased* Strict HR@1 from **77.5% to 72.0%**. General-purpose LLM reasoning introduced noise compared to dedicated contrastive embeddings.
* **Hybrid Search (Dense + BM25 Okapi RRF):** Sparse BM25 keyword matching caused Strict HR@1 to drop to **13.7%**. Cross-domain vocabulary mismatch (e.g., *buffer overflow* vs *system integrity policy*) poisoned dense vector rankings.
* **Architectural Decision:** Pure dense retrieval with the domain-fine-tuned embedding model is the optimal and selected architecture.

---

## 3. CVE API Service Architecture (`AutoRMF.CveApi`)

`AutoRMF.CveApi` is a standalone ASP.NET Core / Azure Functions microservice providing external API access to CVE metadata, vulnerability definitions, and NIST control mappings.

### 3.1 Key Endpoints
* **CVE Metadata & Mapping Lookup:** `GET /api/v1/cve/{id}` - Returns CVSS metrics, CWE tags, and mapped NIST SP 800-53 controls.
* **Batch CVE Search:** `POST /api/v1/cve/search` - Supports multi-cve queries and confidence-filtered control retrieval.
* **Offline Data Ingestion Sync:** 
  - `POST /api/cves/upsert`: Bulk ingestion of daily CVE definitions for air-gapped deployments.
  - `POST /api/mappings/precomputed/upsert`: Bulk sync of static pre-computed control mappings ([`docs/14_production_deployment_and_cve_ingestion.md`](file:///c:/repos/AutoRMF/docs/14_production_deployment_and_cve_ingestion.md#2-ingestion-apis-offline--air-gapped-sync)).

### 3.2 Security & Monetization Architecture
* **Database Backend:** Standalone PostgreSQL container (`autormf-cve-db`) running schema `autormf_cve`.
* **API Key & Auth:** Requests authenticated via `X-API-Key` header or OAuth2 Bearer tokens.
* **Rate Limiting:** Managed in-memory via sliding window limiter (`SlidingWindowRateLimiter`).
* **Stripe Billing Integration:** Integrated subscription tiers (`Free`, `Pro Monthly` @ $199/mo, `Pro Annual` @ $159/mo) managed via `StripeBillingService` webhook processing.

---

## 4. Key Reference Documents

* **Static Mapping & ML Design:** [`docs/10_static_mapping_and_ml_pipeline_design.md`](file:///c:/repos/AutoRMF/docs/10_static_mapping_and_ml_pipeline_design.md)
* **Model Retraining & Overfitting Safeguards:** [`docs/13_model_retraining_and_overfitting_safeguards.md`](file:///c:/repos/AutoRMF/docs/13_model_retraining_and_overfitting_safeguards.md)
* **Production Deployment & CVE Ingestion:** [`docs/14_production_deployment_and_cve_ingestion.md`](file:///c:/repos/AutoRMF/docs/14_production_deployment_and_cve_ingestion.md)
* **Model Export & GGUF Conversion:** [`docs/12_model_conversion_guide.md`](file:///c:/repos/AutoRMF/docs/12_model_conversion_guide.md)
* **Evaluation Scripts:** [`docs/scripts/evaluate_mappings.py`](file:///c:/repos/AutoRMF/docs/scripts/evaluate_mappings.py)
