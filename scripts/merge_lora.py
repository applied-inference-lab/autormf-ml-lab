# scripts/merge_lora.py
import os
import sys
import argparse
import torch

try:
    from sentence_transformers import SentenceTransformer
    from peft import PeftModel
except ImportError:
    print("Error: 'sentence-transformers' or 'peft' library is not installed.")
    print("Please install them: pip install sentence-transformers peft torch")
    sys.exit(1)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_BASE = "Alibaba-NLP/gte-Qwen2-7B-instruct"
DEFAULT_ADAPTER = os.path.join(REPO_ROOT, "models", "gte-qwen2-7b-adjudicated-lora")
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "models", "gte-qwen2-7b-merged")

def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter weights into base SentenceTransformer model.")
    parser.add_argument("--base-model", default=DEFAULT_BASE, help="Hugging Face base model name or path.")
    parser.add_argument("--adapter-path", default=DEFAULT_ADAPTER, help="Path to fine-tuned LoRA adapter.")
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT, help="Destination directory for merged model.")
    args = parser.parse_args()

    if not os.path.exists(args.adapter_path):
        print(f"Error: LoRA adapter directory not found at {args.adapter_path}")
        sys.exit(1)

    print(f"Loading base model: {args.base_model}...")
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    base_model = SentenceTransformer(
        args.base_model,
        model_kwargs={"torch_dtype": dtype, "trust_remote_code": True}
    )

    print(f"Loading LoRA adapter from {args.adapter_path} and merging weights...")
    peft_model = PeftModel.from_pretrained(base_model[0].auto_model, args.adapter_path)
    merged_model = peft_model.merge_and_unload()

    base_model[0].auto_model = merged_model

    print(f"Saving merged weights to {args.output_path}...")
    os.makedirs(args.output_path, exist_ok=True)
    base_model.save(args.output_path)
    print("Merge complete. Merged model is ready for GGUF conversion with llama.cpp.")

if __name__ == "__main__":
    main()
