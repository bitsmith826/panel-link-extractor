# Telegram Panel Link Extractor

Telegram Scraper & Listener berbasis **Python (Telethon)** untuk mengekstrak link panel secara otomatis dari channel / grup Telegram (seperti **FirexPanel**, **AnneBellaPanel**, dan **RizzxAura**), termasuk link yang tersembunyi di dalam tag spoiler, blockquote, inline buttons, maupun teks biasa tanpa format.

---

## 🚀 Fitur Utama

- **Multi-Channel Targeted Scraper**:
  - Mengekstrak riwayat pesan dari channel / grup target spesifik.
  - Mendukung grup privat (via link undangan `https://t.me/+...`) maupun channel publik (seperti `@annebellapanel` dan `@RIZZxPANEL`).
  - Target default:
    1. **FirexPanel** (`https://firexpanel.com/...`)
    2. **AnneBellaPanel** (`https://annebellapanel.vercel.app/...`)
    3. **RizzxAura Panel** (`https://rizzxaura.vercel.app/...`)
- **Ekstraksi Cerdas & Mendalam**:
  - Mengambil link dari format teks biasa (*unformatted plaintext*).
  - Mengambil link dari teks tersembunyi (*spoiler formatting* / `MessageEntitySpoiler`).
  - Mengambil link dari *blockquote*, *inline buttons*, dan *hyperlink entities*.
- **Normalisasi URL Otomatis**:
  - Memastikan seluruh link diawali dengan protokol `https://`.
  - Menghapus prefix `www.` jika ada.
  - Memfilter dan membuang link kosong / beranda (hanya mengambil link dengan path / parameter aktif).
- **Validasi Anti-Duplikat Ketat (Deduplikasi)**:
  - Link yang sudah ada di file output tidak akan pernah dimasukkan ulang.
  - Output diurutkan secara alfabetis (A-Z) setiap kali disimpan.
- **Web Panel Generator (Fitur Baru)**:
  - Mengonversi data database Firebase RTDB dan Auth Key menjadi URL Web Panel siap klik.
  - Mendukung domain **FirexPanel**, **AnneBellaPanel**, dan **RizzxAura**.
  - Mendukung format **Single Panel (`?s=`)** maupun **Multi Panel (`?m=`)**.
  - Dapat langsung membaca file script (seperti `arxpays jio.py`), input manual, atau paste teks.
  - Opsi sinkronisasi otomatis ke koleksi `extracted_links.txt` dan `extracted_links.json`.
- **Keamanan Akun Berlapis (Anti-Ban & Anti-Flood)**:
  - Penyamaran identitas resmi Telegram Desktop Windows 10.
  - Pacing / jeda aman saat memindai pesan untuk menghindari pembatasan Telegram.
  - Pencadangan sesi otomatis dalam bentuk file `.session` dan portable `StringSession`.

---

## 📋 Persyaratan

- **Python 3.8+**
- **Kredensial Telegram API** (`API_ID` & `API_HASH` dari [my.telegram.org](https://my.telegram.org)).

---

## 🛠️ Langkah Instalasi

1. **Clone repository ini**:
   ```bash
   git clone https://github.com/bitsmith826/panel-link-extractor.git
   cd panel-link-extractor
   ```

2. **Buat dan aktifkan Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi file `.env`**:
   Salin `.env.example` menjadi `.env`:
   ```bash
   copy .env.example .env
   ```
   Buka file `.env` lalu masukkan `API_ID` dan `API_HASH` Anda.

---

## 💻 Cara Menjalankan

Jalankan script menggunakan terminal:
```powershell
.\venv\Scripts\python main.py
```
*(atau klik dua kali file `start.bat` di Windows)*

### Menu Utama:
```text
PILIH MENU UTAMA:
  1. Ekstrak Link Panel dari Telegram (Scraper & Listener)
  2. Buat / Generate Link Web Panel (dari File DB/Key atau Manual)
  0. Keluar
```

- **Jika memilih Menu 1 (Ekstraksi Telegram)**:
  ```text
  Pilih Target Ekstraksi Telegram:
    1. Semua 3 Target Sekaligus (Firex + AnneBella + RizzxAura) (Default)
    2. Hanya Channel @RIZZxPANEL (rizzxaura.vercel.app)
    3. Hanya Channel @annebellapanel (annebellapanel.vercel.app)
    4. Hanya Grup FirexPanel (firexpanel.com)
  ```
- **Jika memilih Menu 2 (Web Panel Generator)**:
  - Membaca file `.py` / list panel (otomatis mendeteksi `arxpays jio.py` atau file lain).
  - Memilih domain tujuan (`firexpanel.com`, `annebellapanel.vercel.app`, `rizzxaura.vercel.app`, atau semuanya).
  - Memilih format Single (`?s=`) atau Multi (`?m=`).
  - Menyimpan hasil ke `generated_panels.txt` serta opsi simpan langsung ke `extracted_links.txt`.

---

## 📁 Format Output

### 1. `extracted_links.txt`
Format bersih **1 link per baris** (terurut rapi A-Z):
```text
https://annebellapanel.vercel.app/?m=W3sidXJsIjoiaHR0cHM6Ly...
https://annebellapanel.vercel.app/?s=aHR0cHM6Ly93aGl0aGV4...
https://firexpanel.com/?s=aHR0cHM6Ly9jYWxsbWV2aWxsZW4x...
https://firexpanel.com/?s=aHR0cHM6Ly9yYW1hLWViOGNjLWRl...
https://rizzxaura.vercel.app/?s=aHR0cHM6Ly9kaXNjb3Jk...
```

### 2. `extracted_links.json`
Menyimpan riwayat lengkap beserta metadata pesan (ID pesan, tanggal, nama grup, dan potongan teks):
```json
[
  {
    "url": "https://rizzxaura.vercel.app/?s=...",
    "chat_id": -1002345678901,
    "chat_title": "RIZZ'S PANNEL",
    "message_id": 142,
    "timestamp": "2026-10-01 10:35:12",
    "snippet": "https://rizzxaura.vercel.app/?s=..."
  }
]
```

---

## 🔒 Keamanan & Kerahasiaan Sesi
File sesi Telegram (`.session`), cadangan sesi (`session_backup.txt`, `backups/`), dan data `.env` **sudah otomatis diabaikan di `.gitignore`** sehingga aman dari kebocoran saat di-push ke GitHub.
