import os
import re
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

import storage

console = Console()

DOMAINS = {
    "1": ("FirexPanel", "https://firexpanel.com"),
    "2": ("AnneBellaPanel", "https://annebellapanel.vercel.app"),
    "3": ("RizzxAura", "https://rizzxaura.vercel.app"),
}

DEFAULT_SAMPLE_PATH = r"C:\Users\Administrator\Downloads\arxpays jio.py"

def clean_database_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        cleaned = "https://" + cleaned
    elif cleaned.startswith("http://"):
        cleaned = "https://" + cleaned[7:]
    cleaned = cleaned.rstrip("/")
    return cleaned

def encode_single_panel(db_url: str, auth_key: str, domain_base: str) -> str:
    clean_url = clean_database_url(db_url)
    clean_key = auth_key.strip() or clean_url
    raw_payload = f"{clean_url}|||{clean_key}".encode("utf-8")
    b64 = base64.b64encode(raw_payload).decode("utf-8")
    return f"{domain_base}/?s={b64}"

def encode_multi_panel(panels: List[Tuple[str, str]], domain_base: str) -> str:
    data = []
    for db_url, auth_key in panels:
        clean_url = clean_database_url(db_url)
        clean_key = auth_key.strip() or clean_url
        data.append({"url": clean_url, "key": clean_key})
    
    json_str = json.dumps(data, separators=(',', ':'))
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"{domain_base}/?m={b64}"

def parse_panels_from_text(content: str) -> List[Tuple[str, str]]:
    """
    Mengekstrak pasangan (url, key) dari berbagai format teks:
    1. Python tuple list: ("https://...firebase...", "key")
    2. Format pipe: https://... ||| key
    3. Format CSV/koma: https://..., key
    """
    results: List[Tuple[str, str]] = []
    seen = set()

    # Pattern 1: Format Python tuple ("https://...", "...")
    tuple_pattern = re.compile(
        r'\(\s*["\'](https?://[^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)'
    )
    for u, k in tuple_pattern.findall(content):
        u_clean = clean_database_url(u)
        k_clean = k.strip()
        if (u_clean, k_clean) not in seen:
            seen.add((u_clean, k_clean))
            results.append((u_clean, k_clean))

    if results:
        return results

    # Pattern 2: Baris per baris (pipe atau koma)
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        if "|||" in line:
            parts = line.split("|||", 1)
            u, k = parts[0].strip(), parts[1].strip()
        elif "," in line:
            parts = line.split(",", 1)
            u, k = parts[0].strip(), parts[1].strip()
        elif "\t" in line:
            parts = line.split("\t", 1)
            u, k = parts[0].strip(), parts[1].strip()
        else:
            u, k = line, line
        
        if "firebase" in u.lower() or u.startswith("http"):
            u_clean = clean_database_url(u)
            k_clean = k.strip()
            if (u_clean, k_clean) not in seen:
                seen.add((u_clean, k_clean))
                results.append((u_clean, k_clean))

    return results

def parse_panels_from_file(file_path: str) -> List[Tuple[str, str]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
    content = path.read_text(encoding="utf-8", errors="ignore")
    return parse_panels_from_text(content)

async def run_panel_generator():
    console.print(
        Panel(
            "[bold cyan]Web Panel Link Generator[/bold cyan]\n"
            "[dim]Konversi database RTDB & Key menjadi URL Web Panel (Firex / AnneBella / RizzxAura)[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
            expand=False
        )
    )

    # 1. Pilih Sumber Input
    console.print("[bold yellow]Pilih Sumber Input Panel:[/bold yellow]")
    has_sample = os.path.exists(DEFAULT_SAMPLE_PATH)
    if has_sample:
        console.print(f"  [bold green]1.[/bold green] File arxpays jio ([dim]{DEFAULT_SAMPLE_PATH}[/dim]) [bold cyan](Terdeteksi)[/bold cyan]")
    else:
        console.print("  [bold green]1.[/bold green] Parse dari File Python / Teks (masukkan path file)")
    console.print("  [bold green]2.[/bold green] Input Manual 1 Panel (URL Firebase + Auth Key)")
    console.print("  [bold green]3.[/bold green] Tempel / Paste Daftar Panel (Multiple baris)\n")

    input_choice = Prompt.ask("Pilih opsi input", choices=["1", "2", "3"], default="1")

    panels: List[Tuple[str, str]] = []

    if input_choice == "1":
        default_p = DEFAULT_SAMPLE_PATH if has_sample else ""
        file_path = Prompt.ask("Masukkan path file", default=default_p).strip('"').strip("'")
        try:
            panels = parse_panels_from_file(file_path)
            console.print(f"[bold green]✓ Berhasil menemukan {len(panels)} panel database dari file![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Gagal membaca file:[/bold red] {e}")
            return

    elif input_choice == "2":
        db_url = Prompt.ask("Masukkan Firebase RTDB URL (cth: https://xxx-default-rtdb.firebaseio.com)")
        auth_key = Prompt.ask("Masukkan Auth Key / Secret (tekan Enter jika sama dengan URL)", default=db_url)
        panels = [(db_url.strip(), auth_key.strip())]

    elif input_choice == "3":
        console.print("[yellow]Ketik atau tempel daftar panel (tekan Enter 2x atau ketik END untuk selesai):[/yellow]")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END" or (not line.strip() and lines and not lines[-1].strip()):
                    break
                lines.append(line)
            except EOFError:
                break
        raw_text = "\n".join(lines)
        panels = parse_panels_from_text(raw_text)
        console.print(f"[bold green]✓ Berhasil mem-parse {len(panels)} panel database![/bold green]")

    if not panels:
        console.print("[bold red]Tidak ada data panel yang valid untuk diproses.[/bold red]")
        return

    # 2. Pilih Target Domain Web
    console.print("\n[bold yellow]Pilih Target Domain Web Panel:[/bold yellow]")
    console.print("  [bold green]1.[/bold green] FirexPanel ([cyan]https://firexpanel.com[/cyan])")
    console.print("  [bold green]2.[/bold green] AnneBellaPanel ([cyan]https://annebellapanel.vercel.app[/cyan])")
    console.print("  [bold green]3.[/bold green] RizzxAura Panel ([cyan]https://rizzxaura.vercel.app[/cyan])")
    console.print("  [bold green]4.[/bold green] Semua 3 Domain Sekaligus\n")

    domain_choice = Prompt.ask("Pilih domain", choices=["1", "2", "3", "4"], default="1")
    selected_domains = []
    if domain_choice == "4":
        selected_domains = [d[1] for d in DOMAINS.values()]
    else:
        selected_domains = [DOMAINS[domain_choice][1]]

    # 3. Pilih Format URL
    console.print("\n[bold yellow]Pilih Format URL Hasil:[/bold yellow]")
    console.print("  [bold green]1.[/bold green] [bold]Single Panel (?s=)[/bold] - 1 URL per database (Standar)")
    console.print("  [bold green]2.[/bold green] [bold]Multi Panel (?m=)[/bold] - Menggabungkan semua database dalam 1 link")
    console.print("  [bold green]3.[/bold green] [bold]Keduanya[/bold] (Single Panel + Multi Panel)\n")

    format_choice = Prompt.ask("Pilih format", choices=["1", "2", "3"], default="1")

    # 4. Generate Links
    generated_single_links: List[str] = []
    generated_multi_links: List[str] = []

    for dom in selected_domains:
        if format_choice in ("1", "3"):
            for u, k in panels:
                link = encode_single_panel(u, k, dom)
                generated_single_links.append(link)

        if format_choice in ("2", "3"):
            CHUNK_SIZE = 20
            if len(panels) > CHUNK_SIZE:
                for i in range(0, len(panels), CHUNK_SIZE):
                    chunk = panels[i:i + CHUNK_SIZE]
                    multi_link = encode_multi_panel(chunk, dom)
                    generated_multi_links.append(multi_link)
            else:
                multi_link = encode_multi_panel(panels, dom)
                generated_multi_links.append(multi_link)

    all_generated = generated_single_links + generated_multi_links

    # 5. Tampilkan Preview Hasil
    console.print()
    preview_table = Table(box=box.ROUNDED, border_style="cyan")
    preview_table.add_column("No", style="dim", width=4)
    preview_table.add_column("Tipe", style="bold yellow", width=14)
    preview_table.add_column("URL Web Panel", style="bold green")

    preview_count = min(len(all_generated), 8)
    for idx in range(preview_count):
        link = all_generated[idx]
        tipe = "Multi (?m=)" if "?m=" in link else "Single (?s=)"
        short_link = link if len(link) <= 75 else link[:72] + "..."
        preview_table.add_row(str(idx + 1), tipe, short_link)

    console.print(preview_table)
    if len(all_generated) > preview_count:
        console.print(f"[dim]... dan {len(all_generated) - preview_count} link lainnya.[/dim]")

    # 6. Simpan ke File
    output_filename = "generated_panels.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for link in all_generated:
            f.write(link + "\n")

    console.print(f"\n[bold green]✓ Berhasil membuat {len(all_generated)} link panel![/bold green]")
    console.print(f"  [cyan]File tersimpan:[/cyan] [bold white]{output_filename}[/bold white]")

    # 7. Integrasi Opsional ke extracted_links.txt & JSON
    if Confirm.ask("\nTambahkan link ini ke koleksi utama (extracted_links.txt & .json)?", default=True):
        entries_to_save: List[Dict[str, Any]] = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for link in all_generated:
            if link not in storage.seen_urls:
                entries_to_save.append({
                    "url": link,
                    "chat_id": 0,
                    "chat_title": "Web Panel Generator",
                    "message_id": 0,
                    "timestamp": now_str,
                    "snippet": f"Generated from {len(panels)} database panels"
                })

        if entries_to_save:
            saved_entries = await storage.save_extracted_links(entries_to_save)
            console.print(f"[bold green]✓ +{len(saved_entries)} link baru berhasil ditambahkan dan disortir A-Z ke extracted_links.txt![/bold green]")
        else:
            console.print("[yellow]Semua link yang di-generate sudah ada di koleksi (duplikat diabaikan).[/yellow]")

    console.print()
