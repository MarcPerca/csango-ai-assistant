from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
import re

from app.knowledge import build_system_prompt
from app.memory import build_memory_context, clear_memory, maybe_remember_user_fact, save_message
from app.ollama_client import OllamaUnavailable, ask_ollama
from app.web_search import build_web_context, should_search_web


ROOT = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

def clean_answer_text(answer: str) -> str:
    replacements = {
        "autores romanos": "autores rumanos",
        "autor romano": "autor rumano",
        "Romanos": "Rumanos",
        "romanos": "rumanos",
        "Romaniano": "Rumano",
        "romaniano": "rumano",
        "Romanianos": "Rumanos",
        "romanianos": "rumanos",
        "Comisión Europea": "Consejo de Europa",
        "comisión europea": "Consejo de Europa",
        "European Commission": "Council of Europe",
        "european commission": "Council of Europe",
        "Organización para la Cooperación y el Desarrollo Económicos (OCDE)": "Consejo de Europa",
        "OCDE": "Consejo de Europa",
        "OECD": "Council of Europe",
        "la Consejo de Europa": "el Consejo de Europa",
        "La Consejo de Europa": "El Consejo de Europa",
        "no todos los hablantes de Csango hoy en día hablan el dialecto": "no todas las personas csango hablan hoy el dialecto",
        "no todos los hablantes de csango hoy en día hablan el dialecto": "no todas las personas csango hablan hoy el dialecto",
        "no todos los hablantes de Csango hablan el dialecto": "no todas las personas csango hablan el dialecto",
        "no todos los hablantes de csango hablan el dialecto": "no todas las personas csango hablan el dialecto",
    }

    cleaned = answer
    for wrong, right in replacements.items():
        cleaned = cleaned.replace(wrong, right)

    filler_patterns = [
        r"\s*pero no hay una comparaci[oó]n directa con la poblaci[oó]n total de Csangos para determinar un porcentaje\.?",
        r"\s*Sin embargo, no se proporciona una relaci[oó]n directa entre estos n[uú]meros y la proporci[oó]n de Csangos que hablan el dialecto\.?",
        r"\s*no se proporciona una relaci[oó]n directa entre estos n[uú]meros y la proporci[oó]n de Csangos que hablan el dialecto\.?",
    ]
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(
        r"no todos los hablantes de Cs[áa]ngos?\s+hablan el dialecto Csango",
        "no todas las personas csango hablan el dialecto",
        cleaned,
        flags=re.IGNORECASE,
    )

    return re.sub(r"[,;]\s*$", ".", cleaned).strip()


class AssistantHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/":
            self.send_file(ROOT / "templates" / "index.html", "text/html; charset=utf-8")
            return

        if path.startswith("/static/"):
            file_path = ROOT / unquote(path).lstrip("/")
            content_type = "text/plain; charset=utf-8"
            if file_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            if file_path.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            if file_path.suffix == ".svg":
                content_type = "image/svg+xml; charset=utf-8"
            if file_path.suffix.lower() in {".jpg", ".jpeg"}:
                content_type = "image/jpeg"
            if file_path.suffix.lower() == ".png":
                content_type = "image/png"
            self.send_file(file_path, content_type)
            return

        self.send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/reset":
            clear_memory()
            self.send_json({"status": "ok"})
            return

        if path != "/api/chat":
            self.send_json({"error": "Not found"}, status=404)
            return

        payload = self.read_json()
        user_message = str(payload.get("message", "")).strip()
        requested_web_search = bool(payload.get("web_search")) or should_search_web(user_message)
        if not user_message:
            self.send_json({"answer": "Please write a question to begin.", "using_ollama": False})
            return

        save_message("user", user_message)
        maybe_remember_user_fact(user_message)

        web_context = ""
        sources: list[dict[str, str]] = []
        if requested_web_search:
            try:
                web_context, sources = build_web_context(user_message)
            except Exception:
                web_context = ""
                sources = []

        memory_context = build_memory_context(user_message)
        messages = [
            {
                "role": "system",
                "content": build_system_prompt(
                    user_message,
                    extra_context=web_context,
                    memory_context=memory_context,
                ),
            },
            {"role": "user", "content": user_message},
        ]

        try:
            answer = clean_answer_text(ask_ollama(messages))
            using_ollama = True
        except OllamaUnavailable:
            answer = (
                "I cannot connect to the local AI engine right now. "
                "Check that Ollama is running and that the llama3.2:3b model is available."
            )
            using_ollama = False

        save_message("assistant", answer)
        self.send_json({"answer": answer, "using_ollama": using_ollama, "sources": sources})

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}

        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body)

    def send_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_json({"error": "Not found"}, status=404)
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: int = 200) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AssistantHandler)
    print(f"Csango Knowledge Assistant: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
