# Model Export & GGUF Conversion Guide

This guide details the process for exporting fine-tuned compliance mapping models (both the local `bge-large-en-v1.5` and the remote `gte-Qwen2-7B-instruct` LoRA adapters) and converting/quantizing them into the **GGUF** format for execution in LM Studio or other `llama.cpp`-based inference engines.

---

## 1. Prerequisites

To perform GGUF conversion and quantization, you will need to clone `llama.cpp` and install its python dependencies:

```powershell
# Clone llama.cpp repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Install required python packages for conversion
pip install -r requirements-convert-hf-to-gguf.txt
```

---

## 2. Converting Fine-Tuned BGE Large to GGUF

`train_embeddings.py` fine-tunes `bge-large-en-v1.5` and outputs standard Hugging Face Hugging Face weights to `models/bge-large-en-v1.5-fine-tuned`.

### Step 1: Convert directly to GGUF
Run the conversion script inside the `llama.cpp` directory pointing to your local output path:

```powershell
python convert_hf_to_gguf.py ../models/bge-large-en-v1.5-fine-tuned/ --outfile ../models/bge-large-en-v1.5-fine-tuned.gguf
```

### Step 2: Load into LM Studio
Move the output file `bge-large-en-v1.5-fine-tuned.gguf` to your LM Studio models directory (typically located at `~/.cache/lm-studio/models/` or configured via the UI) and load it using the embedding engine.

---

## 3. Merging & Converting Qwen2 7B LoRA to GGUF

`train_qwen_embeddings.py` outputs a **PEFT LoRA Adapter** (`models/gte-qwen2-7b-adjudicated-lora`). Because it is an adapter, it cannot be run standalone. It must be merged back into the base model before GGUF conversion.

### Step 1: Merge the LoRA adapter with the base model
Create a temporary script (e.g. `docs/scripts/merge_lora.py`) to merge weights using PyTorch and PEFT:

```python
# docs/scripts/merge_lora.py
import torch
from sentence_transformers import SentenceTransformer
from peft import PeftModel

base_model_name = "Alibaba-NLP/gte-Qwen2-7B-instruct"
lora_adapter_path = "models/gte-qwen2-7b-adjudicated-lora"
merged_output_path = "models/gte-qwen2-7b-merged"

print("Loading base model...")
base_model = SentenceTransformer(
    base_model_name,
    model_kwargs={"torch_dtype": torch.bfloat16, "trust_remote_code": True}
)

print("Loading LoRA adapter and merging weights...")
# Wrap the auto_model inside the SentenceTransformer's first module
peft_model = PeftModel.from_pretrained(base_model[0].auto_model, lora_adapter_path)
merged_model = peft_model.merge_and_unload()

# Replace auto_model with the merged model
base_model[0].auto_model = merged_model

print(f"Saving merged model to {merged_output_path}...")
base_model.save(merged_output_path)
print("[SUCCESS] Merged model saved.")
```

Run the merge:
```powershell
.venv\Scripts\python docs/scripts/merge_lora.py
```

### Step 2: Convert Merged Model to F16 GGUF
Using `llama.cpp`, convert the merged directory to a high-precision GGUF model:

```powershell
python convert_hf_to_gguf.py ../models/gte-qwen2-7b-merged/ --outfile ../models/gte-qwen2-7b-merged-f16.gguf
```

### Step 3: Quantize the GGUF (Highly Recommended for Speed)
To reduce memory footprint and increase inference speed on your remote machine, quantize the converted model (e.g. to `Q8_0` or `Q4_K_M`):

```powershell
# Navigate to llama.cpp build/bin directory (where llama-quantize executable is located)
# On Windows, this is typically llama-quantize.exe inside build/bin/Release/
./llama-quantize ../models/gte-qwen2-7b-merged-f16.gguf ../models/gte-qwen2-7b-merged-q8_0.gguf Q8_0
```

---

## 4. Automation Checklist (For future scripting)

To automate the pipeline from user adjudication thresholds to a loaded LM Studio model:

1. **Trigger:** Detect when new manual adjudications exceed threshold (e.g. 50 new mappings).
2. **Train:** Kick off training job `python train_embeddings.py` or `train_qwen_embeddings.py`.
3. **Merge (for LoRA):** Run Python script to execute `merge_and_unload()`.
4. **Convert:** Trigger `convert_hf_to_gguf.py` subprocess.
5. **Quantize:** Trigger `llama-quantize` subprocess.
6. **Deploy:** Copy the final GGUF file to LM Studio's model directory and reload the model service (via LM Studio's API/configuration commands).
