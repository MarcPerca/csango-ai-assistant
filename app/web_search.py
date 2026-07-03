from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
import re


USER_AGENT = "Mozilla/5.0 (compatible; CsangoKnowledgeAssistant/1.0)"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._in_link = False
        self._current_href = ""
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("class") == "result__a":
            href = attrs_dict.get("href") or ""
            if href.startswith("http"):
                self._in_link = True
                self._current_href = href
                self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_link:
            title = " ".join("".join(self._current_text).split())
            if title and self._current_href:
                self.results.append(SearchResult(title=title, url=self._current_href, snippet=""))
            self._in_link = False
            self._current_href = ""
            self._current_text = []


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            cleaned = " ".join(data.split())
            if len(cleaned) > 40:
                self.text.append(cleaned)


def fetch_text(url: str, timeout: int = 8) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return ""
        html = response.read(800_000).decode("utf-8", errors="ignore")

    parser = TextExtractor()
    parser.feed(html)
    return " ".join(parser.text)


def search_duckduckgo(query: str, limit: int = 4) -> list[SearchResult]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=10) as response:
        html = response.read(400_000).decode("utf-8", errors="ignore")

    parser = DuckDuckGoParser()
    parser.feed(html)
    return parser.results[:limit]


def summarize_text_for_query(text: str, query: str, max_chars: int = 900) -> str:
    words = {
        word
        for word in re.split(r"\W+", query.lower())
        if len(word) > 3
    }
    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored = []
    for sentence in sentences:
        lowered = sentence.lower()
        score = sum(1 for word in words if word in lowered)
        if score and 60 <= len(sentence) <= 500:
            scored.append((score, sentence.strip()))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = " ".join(sentence for _, sentence in scored[:4])
    if not selected:
        selected = text[:max_chars]
    return selected[:max_chars].strip()


def should_search_web(message: str) -> bool:
    lowered = message.lower()
    triggers = (
        "busca en web",
        "buscar en web",
        "internet",
        "web",
        "actual",
        "reciente",
        "latest",
        "today",
        "source",
        "fuente",
    )
    return any(trigger in lowered for trigger in triggers)


def build_web_context(query: str, limit: int = 3) -> tuple[str, list[dict[str, str]]]:
    results = search_duckduckgo(query, limit=limit)
    sources = []
    context_parts = []
    for index, result in enumerate(results, start=1):
        try:
            page_text = fetch_text(result.url)
        except Exception:
            page_text = ""

        summary = summarize_text_for_query(page_text, query) if page_text else result.snippet
        if not summary:
            continue

        domain = urlparse(result.url).netloc
        sources.append({"title": result.title, "url": result.url, "domain": domain})
        context_parts.append(f"[{index}] {result.title}\nURL: {result.url}\nExcerpt: {summary}")

    return "\n\n".join(context_parts), sources
