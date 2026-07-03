from __future__ import annotations

"""
Free local LoRA fine-tuning entry point.

Install optional dependencies first:
python -m pip install torch transformers datasets peft accelerate trl

Then create reviewed data:
python training/build_instruction_dataset.py

Then run:
python training/finetune_lora.py
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "training" / "out" / "csango_instructions.jsonl"
OUTPUT_DIR = ROOT / "training" / "out" / "csango-lora"
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def main() -> None:
    try:
        from datasets import load_dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        raise SystemExit(
            "Missing optional free dependencies. Run: "
            "python -m pip install torch transformers datasets peft accelerate trl"
        ) from exc

    if not DATASET_PATH.exists():
        raise SystemExit("Run training/build_instruction_dataset.py first.")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    dataset = load_dataset("json", data_files=str(DATASET_PATH), split="train")

    def format_example(example: dict) -> dict:
        text = tokenizer.apply_chat_template(example["messages"], tokenize=False)
        return {"text": text}

    dataset = dataset.map(format_example)
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )
    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=1,
        logging_steps=1,
        save_strategy="epoch",
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        peft_config=peft_config,
        args=args,
        max_seq_length=1024,
    )
    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    print(f"Wrote LoRA adapter to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
