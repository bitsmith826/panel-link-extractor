import sys
import os
import re
import shutil
import getpass
import asyncio
from datetime import datetime
import qrcode
from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors import UserAlreadyParticipantError, SessionPasswordNeededError, RPCError, FloodWaitError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box

# Konfigurasi encoding konsol Windows agar karakter unicode/emoji tampil normal
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
import storage
from extractor import extract_links_from_message

console = Console()

TARGET_LIST = [
    {
        "name": "FirexPanel (Channel Backup)",
        "target": "https://t.me/+fHREaFYwZUwzODU1",
        "prefix": "firexpanel.com/"
    },
    {
        "name": "AnneBellaPanel (@annebellapanel)",
        "target": "@annebellapanel",
        "prefix": "annebellapanel.vercel.app/"
    },
    {
        "name": "RizzxAura Panel (@RIZZxPANEL)",
        "target": "@RIZZxPANEL",
        "prefix": "rizzxaura.vercel.app/"
    }
]

def print_banner(account_name: str = None, total_saved: int = 0):
    info_text = f"[bold cyan]Telegram Panel Link Extractor[/bold cyan]"
    if account_name:
        sub_info = f"[dim]Akun: [bold white]{account_name}[/bold white] | Total Link Tersimpan: [bold green]{total_saved}[/bold green][/dim]"
    else:
        sub_info = "[dim]Ekstraktor link panel otomatis dari channel Telegram[/dim]"
    
    console.print(Panel(f"{info_text}\n{sub_info}", border_style="cyan", expand=False, box=box.ROUNDED))

def validate_credentials():
    if not config.API_ID or not config.API_HASH or config.API_HASH == "your_api_hash_here":
        console.print(
            Panel(
                "[bold red]Error: API_ID atau API_HASH belum dikonfigurasi di file .env![/bold red]",
                title="[bold yellow]Konfigurasi Diperlukan[/bold yellow]",
                border_style="red"
            )
        )
        sys.exit(1)

def backup_session(client):
    try:
        os.makedirs("backups", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = f"{config.SESSION_NAME}.session"
        if os.path.exists(session_file):
            shutil.copy2(session_file, os.path.join("backups", f"{config.SESSION_NAME}_{timestamp}.session"))

        try:
            str_session = StringSession.save(client.session)
            if str_session:
                with open("session_backup.txt", "w", encoding="utf-8") as f:
                    f.write(f"# CADANGAN LOGIN TELEGRAM ANDA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
                    f.write(f"STRING_SESSION={str_session}\n")
        except Exception:
            pass
    except Exception:
        pass

async def resolve_target(client: TelegramClient, target_str: str):
    """Mendukung invite link (+hash) maupun public username (@username)."""
    target_str = str(target_str).strip()
    match = re.search(r'(?:t\.me/\+|t\.me/joinchat/)([a-zA-Z0-9_-]+)', target_str)
    
    if match:
        invite_hash = match.group(1)
        try:
            check = await client(CheckChatInviteRequest(invite_hash))
            if hasattr(check, 'chat') and check.chat:
                return check.chat
        except Exception:
            pass

        try:
            joined = await client(ImportChatInviteRequest(invite_hash))
            if joined.chats:
                return joined.chats[0]
        except UserAlreadyParticipantError:
            pass
        except Exception:
            pass

    cleaned = target_str.replace("https://t.me/", "")
    try:
        return await client.get_entity(cleaned)
    except Exception:
        return None

async def scrape_target(client: TelegramClient, target_info: dict, existing_urls: set):
    target_str = target_info["target"]
    target_name = target_info["name"]
    target_prefix = target_info["prefix"]

    entity = await resolve_target(client, target_str)
    if not entity:
        console.print(f"[bold red]✗ Gagal mengakses target:[/bold red] {target_name}")
        return 0, 0, 0

    group_title = getattr(entity, 'title', target_name)
    messages_scanned = 0
    new_links_saved = 0
    duplicate_skipped = 0

    # Tampilan progress bar bersih menggunakan Rich Progress
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        TextColumn("• [dim]{task.fields[scanned]} pesan dipindai[/dim]"),
        TextColumn("• [bold green]+{task.fields[new_links]} baru[/bold green]"),
        TextColumn("• [yellow]{task.fields[dupes]} duplikat[/yellow]"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task_id = progress.add_task(
            f"Memindai {group_title}...",
            scanned=0,
            new_links=0,
            dupes=0
        )

        batch_counter = 0
        try:
            async for msg in client.iter_messages(entity):
                messages_scanned += 1
                batch_counter += 1

                if batch_counter >= 25:
                    await asyncio.sleep(0.2)
                    batch_counter = 0

                progress.update(
                    task_id,
                    scanned=messages_scanned,
                    new_links=new_links_saved,
                    dupes=duplicate_skipped
                )

                text = msg.raw_text or msg.text or ""
                keyword_check = "rizzxaura" if "rizzx" in target_prefix else ("annebellapanel" if "annebella" in target_prefix else "firexpanel")
                if keyword_check not in text.lower():
                    has_entity_match = False
                    if msg.entities:
                        for ent in msg.entities:
                            if hasattr(ent, 'url') and ent.url and keyword_check in ent.url.lower():
                                has_entity_match = True
                                break
                    if not has_entity_match and getattr(msg, 'buttons', None):
                        for row in msg.buttons:
                            for btn in row:
                                if getattr(btn, 'url', None) and keyword_check in btn.url.lower():
                                    has_entity_match = True
                                    break
                    if not has_entity_match:
                        continue

                found_urls = extract_links_from_message(msg, target_prefix=target_prefix)
                if not found_urls:
                    continue

                date_str = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entries_to_save = []

                for url in found_urls:
                    if url in storage.seen_urls:
                        duplicate_skipped += 1
                        continue

                    new_links_saved += 1
                    entries_to_save.append({
                        "url": url,
                        "chat_id": utils.get_peer_id(entity),
                        "chat_title": group_title,
                        "message_id": msg.id,
                        "timestamp": date_str,
                        "snippet": text.strip()[:150]
                    })

                if entries_to_save:
                    await storage.save_extracted_links(entries_to_save)
                    progress.update(
                        task_id,
                        scanned=messages_scanned,
                        new_links=new_links_saved,
                        dupes=duplicate_skipped
                    )

        except FloodWaitError as e:
            console.print(f"[bold yellow]Telegram meminta jeda {e.seconds}s. Menunggu...[/bold yellow]")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            console.print(f"[bold red]Error saat membaca {group_title}:[/bold red] {e}")

    # Log rapi setelah selesai memindai channel ini
    console.print(
        f"  [bold green]✓[/bold green] [bold white]{group_title}[/bold white]: "
        f"[cyan]{messages_scanned}[/cyan] pesan dipindai | "
        f"[bold green]+{new_links_saved}[/bold green] link baru | "
        f"[yellow]{duplicate_skipped}[/yellow] duplikat"
    )

    return messages_scanned, new_links_saved, duplicate_skipped

async def main():
    console.clear()
    validate_credentials()
    existing_urls = storage.load_existing_urls()

    session_target = config.SESSION_NAME
    if config.STRING_SESSION:
        session_target = StringSession(config.STRING_SESSION)

    client = TelegramClient(
        session_target,
        config.API_ID,
        config.API_HASH,
        device_model="Desktop",
        system_version="Windows 10 x64",
        app_version="4.16.8",
        lang_code="en",
        system_lang_code="en"
    )

    await client.connect()
    if not await client.is_user_authorized():
        console.print("[bold red]Sesi belum login. Jalankan script untuk login terlebih dahulu.[/bold red]")
        sys.exit(1)

    backup_session(client)
    me = await client.get_me()

    print_banner(account_name=me.first_name, total_saved=len(existing_urls))

    # Menu Pilihan Target
    console.print("[bold cyan]Pilih Target Ekstraksi:[/bold cyan]")
    console.print("  [bold green]1.[/bold green] [bold]Semua 3 Target Sekaligus[/bold] (Firex + AnneBella + RizzxAura) [yellow](Default)[/yellow]")
    console.print("  [bold green]2.[/bold green] Hanya Channel [bold yellow]@RIZZxPANEL[/bold yellow] (rizzxaura.vercel.app)")
    console.print("  [bold green]3.[/bold green] Hanya Channel [bold yellow]@annebellapanel[/bold yellow] (annebellapanel.vercel.app)")
    console.print("  [bold green]4.[/bold green] Hanya Grup [bold yellow]FirexPanel[/bold yellow] (firexpanel.com)\n")

    choice = Prompt.ask("Pilih opsi", choices=["1", "2", "3", "4"], default="1")
    console.print()

    targets_to_run = []
    if choice == "1":
        targets_to_run = TARGET_LIST
    elif choice == "2":
        targets_to_run = [TARGET_LIST[2]]
    elif choice == "3":
        targets_to_run = [TARGET_LIST[1]]
    elif choice == "4":
        targets_to_run = [TARGET_LIST[0]]

    total_scanned = 0
    total_added = 0
    total_dupes = 0

    for item in targets_to_run:
        scanned, added, dupes = await scrape_target(client, item, existing_urls)
        total_scanned += scanned
        total_added += added
        total_dupes += dupes

    final_count = len(storage.seen_urls)
    
    # Ringkasan Laporan Akhir yang Rapi
    console.print()
    summary_table = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
    summary_table.add_column("Keterangan", style="bold white", width=34)
    summary_table.add_column("Nilai", style="bold cyan", justify="right")

    summary_table.add_row("Total Pesan Dipindai", f"{total_scanned} pesan")
    summary_table.add_row("Link Baru Ditambahkan", f"[bold green]+{total_added}[/bold green]")
    summary_table.add_row("Link Duplikat Diabaikan", f"[yellow]{total_dupes}[/yellow]")
    summary_table.add_row("Total Link Aktif di File", f"[bold green]{final_count} link[/bold green]")
    summary_table.add_row("File Output (TXT)", f"[cyan]{config.OUTPUT_FILE_TXT}[/cyan]")
    summary_table.add_row("File Output (JSON)", f"[cyan]{config.OUTPUT_FILE_JSON}[/cyan]")

    console.print(Panel(summary_table, title="[bold green]Ringkasan Ekstraksi Selesai[/bold green]", border_style="green", expand=False))
    console.print()

    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        console.print("\n[yellow]Proses dihentikan.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Terjadi kesalahan:[/bold red] {e}")
