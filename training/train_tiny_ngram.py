from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = ROOT / "data" / "notes.md"
OUT_DIR = ROOT / "training" / "out"
MODEL_PATH = OUT_DIR / "tiny_ngram_model.json"


def train(text: str, n: int = 5) -> dict[str, list[str]]:
    model: dict[str, list[str]] = defaultdict(list)
    padded = "\n" * n + text
    for index in range(len(padded) - n):
        prefix = padded[index : index + n]
        next_char = padded[index + n]
        model[prefix].append(next_char)
    return dict(model)


def generate(model: dict[str, list[str]], prompt: str, n: int = 5, length: int = 500) -> str:
    state = ("\n" * n + prompt)[-n:]
    output = [prompt]
    for _ in range(length):
        choices = model.get(state)
        if not choices:
            state = random.choice(list(model.keys()))
            choices = model[state]
        next_char = random.choice(choices)
        output.append(next_char)
        state = (state + next_char)[-n:]
    return "".join(output)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = NOTES_PATH.read_text(encoding="utf-8")
    model = train(text)
    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {MODEL_PATH}")
    print(generate(model, "Csango", length=300))


if __name__ == "__main__":
    main()
