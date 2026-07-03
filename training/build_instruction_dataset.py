from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "training" / "out"


SEED_QUESTIONS = [
    "Who are the Csango?",
    "Where do the Csango live?",
    "What language is associated with the Csango?",
    "What role does Roman Catholic religion play in Csango identity?",
    "What does the Csango assistant know about population estimates?",
    "Quienes son los Csango?",
    "Donde viven los Csango?",
    "Que idioma se asocia con los Csango?",
    "Que tradiciones culturales son importantes para los Csango?",
]


def load_context() -> str:
    profile = DATA_DIR / "profile.json"
    notes = DATA_DIR / "notes.md"
    parts = []
    if profile.exists():
        parts.append("Profile:\n" + profile.read_text(encoding="utf-8"))
    if notes.exists():
        parts.append("Notes:\n" + notes.read_text(encoding="utf-8")[:6000])
    return "\n\n".join(parts).strip()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    context = load_context()
    output_path = OUT_DIR / "csango_instructions.jsonl"
    with output_path.open("w", encoding="utf-8") as file:
        for question in SEED_QUESTIONS:
            item = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a concise cultural assistant. Use only the provided context.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion:\n{question}",
                    },
                    {
                        "role": "assistant",
                        "content": "Answer using the context. Replace this generated draft with a reviewed answer before serious fine-tuning.",
                    },
                ]
            }
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
