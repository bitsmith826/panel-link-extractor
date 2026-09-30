import re
from typing import List, Set
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

# Regex untuk firexpanel.com
FIREXPANEL_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?firexpanel\.com/[^\s<>"\'`\(\)\[\]\{\}]+',
    re.IGNORECASE
)

# Regex untuk annebellapanel.vercel.app
ANNEBELLA_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?annebellapanel\.vercel\.app/[^\s<>"\'`\(\)\[\]\{\}]+',
    re.IGNORECASE
)

# Regex umum untuk semua URL
GENERAL_URL_REGEX = re.compile(
    r'(?:https?://|www\.)[^\s<>"\'`\(\)\[\]\{\}]+|'
    r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?::[0-9]{1,5})?(?:/[^\s<>"\'`\(\)\[\]\{\}]*)?|'
    r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::[0-9]{1,5})(?:/[^\s<>"\'`\(\)\[\]\{\}]*)?',
    re.IGNORECASE
)

def clean_url(url: str) -> str:
    cleaned = url.strip()
    trailing_chars = ".,;:!?)]}\"\'>"
    while cleaned and cleaned[-1] in trailing_chars:
        cleaned = cleaned[:-1]
    return cleaned

def normalize_panel_url(url: str, domain_target: str = None) -> str:
    """
    Normalisasi URL:
    1. Pastikan diawali https://
    2. Hapus www.
    3. Pastikan ada parameter/path setelah domain (bukan link kosong).
    """
    cleaned = clean_url(url)
    if not cleaned:
        return ""

    if cleaned.startswith("http://"):
        cleaned = "https://" + cleaned[7:]
    elif not cleaned.startswith("https://"):
        cleaned = "https://" + cleaned

    cleaned = cleaned.replace("://www.", "://")

    # Validasi FirexPanel
    if "firexpanel.com" in cleaned.lower():
        if cleaned in ("https://firexpanel.com", "https://firexpanel.com/"):
            return ""
        if not cleaned.startswith("https://firexpanel.com/"):
            return ""
        suffix = cleaned[len("https://firexpanel.com/"):].strip()
        if not suffix:
            return ""
        return cleaned

    # Validasi AnneBellaPanel
    if "annebellapanel.vercel.app" in cleaned.lower():
        if cleaned in ("https://annebellapanel.vercel.app", "https://annebellapanel.vercel.app/"):
            return ""
        if not cleaned.startswith("https://annebellapanel.vercel.app/"):
            return ""
        suffix = cleaned[len("https://annebellapanel.vercel.app/"):].strip()
        if not suffix:
            return ""
        return cleaned

    return cleaned if not domain_target else ""

def extract_links_from_message(message, target_prefix: str = None) -> List[str]:
    """
    Mengekstrak dan menormalisasi URL dari pesan Telegram.
    Mendukung teks biasa, teks tersembunyi (spoiler), blockquote, maupun hyperlink entities.
    """
    found_links: Set[str] = set()
    text = message.raw_text or message.text or ""

    # 1. Ekstrak dari Entities (termasuk hyperlink terselubung)
    if message.entities:
        for entity in message.entities:
            if isinstance(entity, MessageEntityTextUrl):
                if entity.url:
                    found_links.add(clean_url(entity.url))
            elif isinstance(entity, MessageEntityUrl):
                try:
                    raw_bytes = text.encode("utf-16-le")
                    start = entity.offset * 2
                    end = (entity.offset + entity.length) * 2
                    url_text = raw_bytes[start:end].decode("utf-16-le")
                    found_links.add(clean_url(url_text))
                except Exception:
                    pass

    # 2. Ekstrak langsung dengan Regex dari teks mentah (termasuk di dalam spoiler / blockquote)
    if text:
        if target_prefix and "annebella" in target_prefix.lower():
            matches = ANNEBELLA_REGEX.findall(text)
        elif target_prefix and "firex" in target_prefix.lower():
            matches = FIREXPANEL_REGEX.findall(text)
        else:
            matches = (
                FIREXPANEL_REGEX.findall(text) +
                ANNEBELLA_REGEX.findall(text) +
                GENERAL_URL_REGEX.findall(text)
            )

        for match in matches:
            cleaned = clean_url(match)
            if cleaned:
                found_links.add(cleaned)

    # 3. Normalisasi & Validasi Link
    normalized_results: Set[str] = set()
    for raw_url in found_links:
        valid_url = normalize_panel_url(raw_url, domain_target=target_prefix)
        if valid_url:
            normalized_results.add(valid_url)

    return sorted(list(normalized_results))
