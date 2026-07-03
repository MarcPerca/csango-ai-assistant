# Csango Knowledge Assistant

Csango Knowledge Assistant is an AI chatbot focused on the Csango people, their history, identity, language, culture, religion, population, and regional context.

The project runs in the browser and uses a Python backend connected to Ollama. It includes an editable knowledge base, so the assistant can answer using project-specific information instead of relying only on the model's general knowledge.

## Features

- Chat-style web interface
- Python backend with no external Python dependencies
- Local AI model execution with Ollama
- Editable knowledge base in `data/notes.md` and `data/profile.json`
- Local retrieval system that selects relevant text before generating an answer
- SQLite conversation memory in `data/memory.sqlite3`
- Optional free web search mode from the chat interface
- Tiny local training script for an educational small model
- Optional LoRA fine-tuning script using free open-source tools
- English and Spanish responses depending on the user's question
- Csango flag and cultural images in the interface

## Requirements

- Python 3.10 or newer
- Ollama installed
- An Ollama model downloaded locally

Recommended model:

```powershell
ollama pull llama3.2:3b
```

If your computer has limited RAM, start with a small model such as `llama3.2:3b` or `phi3:mini`.

## How To Run

1. Check that Ollama is installed:

```powershell
ollama --version
```

2. Download the model:

```powershell
ollama pull llama3.2:3b
```

3. Start the app:

```powershell
python server.py
```

4. Open the app in your browser:

```text
http://127.0.0.1:8000
```

## Changing The Model

By default, the app uses:

```text
llama3.2:3b
```

You can change the model with an environment variable:

```powershell
$env:OLLAMA_MODEL="phi3:mini"
python server.py
```

## Knowledge Base

The project uses two editable files:

- `data/notes.md`: source notes, texts, and cultural information
- `data/profile.json`: structured data

When a user asks a question, the backend searches these files, selects relevant fragments, and sends them to the AI model as context.

This is a simple RAG-style approach. It does not use embeddings or a vector database, but it still allows the assistant to answer from a custom knowledge base.

## Memory

The app saves messages and simple user facts in SQLite:

```text
data/memory.sqlite3
```

Use the reset endpoint or the UI flow to clear memory:

```text
POST /api/reset
```

## Web Search

The composer includes a `Web` toggle. When enabled, the backend performs a free web search, fetches public pages, extracts relevant text, and sends the excerpts to the model as extra context.

No paid search API key is required. Results depend on public website availability and may fail if a site blocks automated access.

## Training A Tiny Model

This project includes a tiny educational n-gram model trainer. It is not a ChatGPT-quality model, but it demonstrates the full train/save/generate loop for free:

```powershell
python training/train_tiny_ngram.py
```

The output is written to:

```text
training/out/tiny_ngram_model.json
```

## Fine-Tuning

Create a starter instruction dataset:

```powershell
python training/build_instruction_dataset.py
```

Then install optional free dependencies:

```powershell
python -m pip install torch transformers datasets peft accelerate trl
```

Run the LoRA script:

```powershell
python training/finetune_lora.py
```

This uses open-source tooling and does not require a paid API. You may still need enough local RAM/VRAM or a free notebook runtime.

## Free Deployment

See `DEPLOY_FREE.md`.

The included `Dockerfile` runs the app on port `7860`, which is suitable for free Docker-based demos such as Hugging Face Spaces.

## Project Structure

```text
csango-ai-assistant/
|-- app/
|   |-- knowledge.py
|   `-- ollama_client.py
|-- data/
|   |-- notes.md
|   `-- profile.json
|-- static/
|   |-- app.js
|   `-- styles.css
|-- templates/
|   `-- index.html
|-- server.py
`-- README.md
```

## Possible Improvements

- Add document upload support
- Add stronger embeddings and vector search for a more advanced RAG system
- Expand the knowledge base with more verified sources
- Add automated tests
