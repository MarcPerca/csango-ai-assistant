# Free deployment notes

This project can be deployed without paid APIs.

## Option 1: Local demo

```powershell
python server.py
```

Open `http://127.0.0.1:8000`.

## Option 2: Hugging Face Space with Docker

Create a free Hugging Face Space, select Docker, and push this repository.

The included `Dockerfile` starts the Python web server on port `7860`.

Important: free CPU Spaces are best for the interface, memory, retrieval, and web-search demo. Running a strong local LLM inside a free CPU Space may be too slow. For the full local AI version, keep using Ollama on your computer.

## Option 3: Free VM or personal server

Run:

```bash
docker build -t csango-ai-assistant .
docker run -p 7860:7860 csango-ai-assistant
```

For Ollama on another machine, set:

```bash
OLLAMA_URL=http://your-ollama-host:11434
```

No paid API key is required.
