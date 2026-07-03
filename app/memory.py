from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "memory.sqlite3"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            content TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def save_message(role: str, content: str) -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, int(time.time())),
        )
        connection.commit()


def recent_messages(limit: int = 8) -> list[dict[str, str]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM messages
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def clear_memory() -> None:
    with connect() as connection:
        connection.execute("DELETE FROM messages")
        connection.execute("DELETE FROM memories")
        connection.commit()


def maybe_remember_user_fact(message: str) -> None:
    cleaned = " ".join(message.strip().split())
    lowered = cleaned.lower()
    triggers = (
        "me llamo ",
        "mi nombre es ",
        "i am ",
        "my name is ",
        "estoy construyendo ",
        "quiero construir ",
        "my project is ",
    )
    if not any(trigger in lowered for trigger in triggers):
        return

    fact = cleaned[:500]
    with connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO memories (kind, content, created_at) VALUES (?, ?, ?)",
            ("user_fact", fact, int(time.time())),
        )
        connection.commit()


def relevant_memories(user_message: str, limit: int = 5) -> list[str]:
    words = {
        word
        for word in "".join(char.lower() if char.isalnum() else " " for char in user_message).split()
        if len(word) > 3
    }
    with connect() as connection:
        rows = connection.execute(
            "SELECT content FROM memories ORDER BY id DESC LIMIT 50"
        ).fetchall()

    scored = []
    for row in rows:
        content = row["content"]
        text = content.lower()
        score = sum(1 for word in words if word in text)
        if score or not words:
            scored.append((score, content))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [content for _, content in scored[:limit]]


def build_memory_context(user_message: str) -> str:
    recent = recent_messages()
    remembered = relevant_memories(user_message)
    parts = []
    if remembered:
        parts.append("Long-term user memories:\n" + "\n".join(f"- {item}" for item in remembered))
    if recent:
        parts.append("Recent conversation:\n" + json.dumps(recent, ensure_ascii=False, indent=2))
    return "\n\n".join(parts).strip()
