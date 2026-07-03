from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_profile() -> dict:
    profile_path = DATA_DIR / "profile.json"
    if not profile_path.exists():
        return {}

    with profile_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_notes() -> str:
    notes_path = DATA_DIR / "notes.md"
    if not notes_path.exists():
        return ""

    notes = notes_path.read_text(encoding="utf-8").strip()
    source_marker = "Source: Wikipedia"
    if source_marker in notes:
        notes = notes[notes.index(source_marker) :]

    return notes


def extract_keywords(user_message: str) -> set[str]:
    stopwords = {
        "about",
        "como",
        "con",
        "cual",
        "cuál",
        "del",
        "donde",
        "dónde",
        "from",
        "how",
        "las",
        "los",
        "que",
        "qué",
        "son",
        "the",
        "una",
        "what",
        "where",
        "who",
    }
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in user_message)
    keywords = {word for word in cleaned.split() if len(word) > 2 and word not in stopwords}

    location_triggers = {"donde", "dónde", "viven", "residen", "where", "live", "living", "located"}
    identity_triggers = {"que", "qué", "quienes", "quiénes", "who", "what"}
    language_triggers = {"lengua", "idioma", "language", "dialect", "dialecto"}
    population_triggers = {"poblacion", "población", "population", "census", "speakers"}
    flag_triggers = {"bandera", "flag", "colores", "colors", "dibujos", "symbols", "simbolos", "creo", "created", "adopted"}
    history_triggers = {
        "aparecieron",
        "aparecio",
        "aparece",
        "año",
        "cuando",
        "origen",
        "origin",
        "appeared",
        "first",
        "mention",
        "mencion",
        "historia",
        "history",
    }

    if any(trigger in cleaned for trigger in location_triggers):
        keywords.update({"moldavia", "bacau", "bacău", "transylvania", "villages", "oituz"})
    if any(trigger in cleaned for trigger in identity_triggers):
        keywords.update({"ethnic", "hungarians", "romanian", "moldavia", "catholic"})
    if any(trigger in cleaned for trigger in language_triggers):
        keywords.update({"language", "dialect", "dialecto", "hungarian", "hungaro", "húngaro", "romanian", "speakers", "hablantes", "13"})
    if any(trigger in cleaned for trigger in flag_triggers):
        keywords.update({"flag", "bandera", "council", "adopted", "sun", "crescent", "cross", "red", "black", "silver"})
    if any(trigger in cleaned for trigger in history_triggers):
        keywords.update({"1234", "1562", "1587", "1588", "1780", "middle", "sources", "perugia", "cuman", "peter", "zold", "origin"})
    if is_speaker_percentage_question(user_message):
        keywords.update({"speakers", "hablantes", "dialect", "dialecto", "estimate", "60000", "70000", "13"})
    elif any(trigger in cleaned for trigger in population_triggers) or "%" in user_message:
        keywords.update({"population", "census", "speakers", "estimate", "4208", "829", "2011", "0", "68", "13"})

    return keywords


def is_speaker_percentage_question(user_message: str) -> bool:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in user_message)
    asks_percent = "%" in user_message or "porcentaje" in cleaned or "percentage" in cleaned
    asks_language = any(word in cleaned for word in ["habla", "hablan", "speaker", "speakers", "dialecto", "dialect", "idioma", "language"])
    return asks_percent and asks_language


def is_origin_or_first_mention_question(user_message: str) -> bool:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in user_message)
    asks_when = any(word in cleaned for word in ["año", "cuando", "aparecieron", "aparecio", "aparece", "first", "when", "appeared", "mention"])
    asks_csango = "csango" in cleaned or "csangos" in cleaned
    return asks_when and asks_csango


def detect_response_language(user_message: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in user_message)
    words = set(cleaned.split())

    spanish_markers = {
        "cual",
        "cuanto",
        "dime",
        "donde",
        "etnia",
        "habla",
        "hablan",
        "idioma",
        "lengua",
        "porcentaje",
        "que",
        "quien",
        "quienes",
        "son",
        "viven",
    }
    english_markers = {
        "about",
        "are",
        "dialect",
        "do",
        "english",
        "ethnicity",
        "how",
        "language",
        "live",
        "many",
        "now",
        "percent",
        "percentage",
        "romania",
        "speak",
        "speakers",
        "tell",
        "that",
        "the",
        "this",
        "teh",
        "what",
        "where",
        "who",
        "wats",
    }

    spanish_score = len(words & spanish_markers)
    english_score = len(words & english_markers)

    if english_score > spanish_score:
        return "English"
    return "Spanish"


def build_question_guidance(user_message: str) -> str:
    if is_origin_or_first_mention_question(user_message):
        return """
Question-specific guidance:
- The user is asking when the Csango appeared or when they are first mentioned.
- Explain the distinction clearly.
- The source mentions a medieval reference from 14 November 1234 in the Cuman bishopric describing Vallah, Hungarians and Germans who came from the Hungarian Kingdom.
- The source also says the name "Csango" appeared relatively recently and was first used in 1780 by Peter Zold.
- Do not say there is no information. Say that the answer depends on whether the user means historical presence or the first use of the name.
- Keep the answer concise.
""".strip()

    if not is_speaker_percentage_question(user_message):
        return ""

    return """
Question-specific guidance:
- The user is asking for the percentage of Csango people who speak the Csango dialect.
- The source excerpts do not provide that exact percentage.
- Do not use the 0.68% or 0.13% census figures as the answer; they refer to ethnic self-identification in Bacau County, not language ability.
- Do not discuss native vs non-native speakers unless a source excerpt explicitly says that.
- Give a very short answer in 2 or 3 sentences only.
- Do not add filler phrases such as "no direct relationship is provided" or repeated explanations.
- In Spanish, start with: "Según la información disponible, no se sabe el porcentaje exacto".
- Mention only: available figures are about 13,000 speakers in one source and an older 2001 Council of Europe estimate of 60,000 to 70,000 speakers; it is reasonable to infer that not all Csango people speak the dialect today.
- Never write that "not all Csango speakers speak the dialect"; that is illogical. Say "not all Csango people speak the dialect".
""".strip()


def split_notes_into_chunks(notes: str) -> list[str]:
    chunks = []
    current = []

    for line in notes.splitlines():
        stripped = line.strip()
        looks_like_heading = stripped and not stripped.startswith("- ") and len(stripped) < 80
        if looks_like_heading and current:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append("\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def tokenize(text: str) -> set[str]:
    stopwords = {
        "about",
        "como",
        "con",
        "cual",
        "cuál",
        "del",
        "donde",
        "dónde",
        "from",
        "how",
        "las",
        "los",
        "que",
        "qué",
        "son",
        "the",
        "una",
        "what",
        "where",
        "who",
    }
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return {word for word in cleaned.split() if len(word) > 2 and word not in stopwords}


def retrieve_relevant_notes(user_message: str, limit: int = 4) -> str:
    notes = load_notes()
    if not notes:
        return ""

    keywords = extract_keywords(user_message)
    query_tokens = tokenize(user_message)
    if not keywords and not query_tokens:
        return notes[:3500]

    scored_chunks = []
    for chunk in split_notes_into_chunks(notes):
        text = chunk.lower()
        chunk_tokens = tokenize(chunk)
        keyword_score = sum(1 for keyword in keywords if keyword in text)
        overlap = len(query_tokens & chunk_tokens)
        union = len(query_tokens | chunk_tokens) or 1
        vector_score = overlap / union
        score = keyword_score + vector_score
        if score:
            scored_chunks.append((score, chunk))

    if not scored_chunks:
        return notes[:3500]

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    selected = [chunk for _, chunk in scored_chunks[:limit]]
    return "\n\n---\n\n".join(selected)[:4500]


def build_context(user_message: str = "", extra_context: str = "", memory_context: str = "") -> str:
    profile = load_profile()
    notes = retrieve_relevant_notes(user_message)
    question_guidance = build_question_guidance(user_message)

    parts = []
    if question_guidance:
        parts.append(question_guidance)
    if profile:
        parts.append("Structured knowledge:\n" + json.dumps(profile, ensure_ascii=False, indent=2))
    if notes:
        parts.append("Relevant source excerpts:\n" + notes)
    if memory_context:
        parts.append("Conversation memory:\n" + memory_context)
    if extra_context:
        parts.append("External web context:\n" + extra_context)

    return "\n\n".join(parts).strip()


def build_system_prompt(user_message: str = "", extra_context: str = "", memory_context: str = "") -> str:
    context = build_context(user_message, extra_context=extra_context, memory_context=memory_context)
    response_language = detect_response_language(user_message)

    return f"""
You are a local cultural AI assistant created to answer questions about the Csango, also known as Csángó.

Language instruction:
- The user's current message is in {response_language}.
- Answer only in {response_language}.
- Do not switch languages inside the answer.

Rules:
- Answer in the same language as the user's current message: Spanish or English. If the user requests another language, use it.
- In Spanish, translate "Romanian/Romanians" as "rumano/rumanos", never as "romano", "romanos", "romaniano", or "romanianos".
- Use a clear, respectful, educational tone.
- Answer only about the Csango: history, culture, language, identity, customs, religion, population, and context.
- If the user asks something unrelated to the Csango, politely redirect the conversation.
- Use the provided source excerpts as your evidence.
- Do not invent regions, villages, organizations, numbers, citations, or sources that are not present in the provided context.
- Do not calculate percentages unless the provided context explicitly gives a percentage.
- If the user asks for the percentage of people who speak Csango, do not answer with census percentages about ethnic self-identification. Those are different data.
- If no exact speaker percentage is provided, say so clearly first. You may then add a cautious inference, clearly marked as an inference, based on available speaker counts and notes about minority language use.
- Do not confuse the Council of Europe with the European Commission. If mentioning the 60,000 to 70,000 speaker figure, describe it as an older 2001 estimate from the Council of Europe.
- If the provided context is not enough to answer accurately, say that the available information does not specify it.
- Do not mention "knowledge base", "Wikipedia", or uploaded/added information unless the user asks for sources.
- Avoid stereotypes, offensive generalizations, or absolute claims about an ethnic group.
- Keep answers concise by default: 2 to 4 short paragraphs, unless the user asks for more detail.
- Always finish with a complete sentence. Do not stop mid-sentence.

Context:
{context if context else "No cultural context has been loaded yet."}

Final language rule:
The final answer must be written only in {response_language}. If the excerpts are in another language, translate the information into {response_language}. Do not include sentences in any other language.
""".strip()
