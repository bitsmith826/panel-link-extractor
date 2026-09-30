import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Set
import config

file_lock = asyncio.Lock()
seen_urls: Set[str] = set()

def load_existing_urls() -> Set[str]:
    """
    Memuat SEMUA link yang sudah pernah tersimpan di extracted_links.txt
    maupun extracted_links.json ke dalam memory set untuk mencegah duplikat.
    """
    global seen_urls
    seen_urls.clear()

    # 1. Baca dari file TXT
    if os.path.exists(config.OUTPUT_FILE_TXT):
        try:
            with open(config.OUTPUT_FILE_TXT, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned = line.strip()
                    if cleaned and cleaned.startswith("http"):
                        seen_urls.add(cleaned)
        except Exception:
            pass

    # 2. Baca dari file JSON
    if os.path.exists(config.OUTPUT_FILE_JSON):
        try:
            with open(config.OUTPUT_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "url" in item:
                            seen_urls.add(item["url"].strip())
        except Exception:
            pass

    return seen_urls

async def save_extracted_links(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    HANYA menyimpan link yang BELUM PERNAH ADA di database/file.
    Jika link sudah ada di file, dipastikan DIABAIKAN (tidak dimasukkan ganda).
    """
    if not entries:
        return []

    async with file_lock:
        to_save: List[Dict[str, Any]] = []
        for entry in entries:
            url = entry.get("url", "").strip()
            if not url:
                continue

            # VALIDASI KETAT: Jika sudah ada di file/cache, jangan masukkan lagi!
            if url in seen_urls:
                continue

            # Tandai sudah pernah tersimpan
            seen_urls.add(url)
            to_save.append(entry)

        if not to_save:
            return []

        # 1. Simpan ke TXT (Format murni 1 link per baris, terurut A-Z)
        if config.OUTPUT_FORMAT in ("txt", "both"):
            sorted_all_urls = sorted(list(seen_urls))
            with open(config.OUTPUT_FILE_TXT, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted_all_urls) + "\n")

        # 2. Simpan ke JSON (Metadata lengkap, terurut A-Z)
        if config.OUTPUT_FORMAT in ("json", "both"):
            existing_data = []
            if os.path.exists(config.OUTPUT_FILE_JSON):
                try:
                    with open(config.OUTPUT_FILE_JSON, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = []
                except Exception:
                    existing_data = []

            existing_data.extend(to_save)
            # Urutkan berdasarkan URL
            existing_data.sort(key=lambda x: x.get("url", ""))
            with open(config.OUTPUT_FILE_JSON, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

        return to_save
