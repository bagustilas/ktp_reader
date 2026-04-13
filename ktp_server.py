#!/usr/bin/env python3
"""
=======================================================
  HTTP SERVER - KTP Reader Identik PT. INTI
=======================================================
  Dibuat oleh  : Bagus Tilas
  GitHub       : https://github.com/bagustilas
  Date         : 13/04/2026
  version      : 1.0.0  

  Jalankan:
    python ktp_http_server.py
=======================================================
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime
import logging
import urllib.parse
import base64
import os

# ─────────────────────────────────────────
#  LOAD .env MANUAL (tanpa library dotenv)
# ─────────────────────────────────────────
def load_env(path=".env"):
    """Baca file .env dan set ke os.environ jika belum ada."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)

load_env()

# ─────────────────────────────────────────
#  KONFIGURASI  (ambil dari env, ada default)
# ─────────────────────────────────────────
HOST      = os.environ.get("KTP_HOST", "0.0.0.0")
PORT      = int(os.environ.get("KTP_PORT", "8080"))
SERVER_IP = os.environ.get("KTP_SERVER_IP", "169.254.112.97")

LOG_FILE  = os.environ.get("KTP_LOG_FILE", "ktp_data.json")
LOG_HTTP  = os.environ.get("KTP_LOG_HTTP", "server.log")
FOTO_DIR  = os.environ.get("KTP_FOTO_DIR", "foto_ktp")

# Buat folder foto jika belum ada
os.makedirs(FOTO_DIR, exist_ok=True)

# ─────────────────────────────────────────
#  SETUP LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_HTTP, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
#  LABEL FIELD KTP
# ─────────────────────────────────────────
LABEL = {
    "nik"            : "NIK",
    "nama"           : "Nama Lengkap",
    "ttl"            : "Tempat/Tgl Lahir",
    "tanggal_lahir"  : "Tanggal Lahir",
    "jenis_kelamin"  : "Jenis Kelamin",
    "alamat"         : "Alamat",
    "rt_rw"          : "RT / RW",
    "kelurahan"      : "Kelurahan / Desa",
    "kecamatan"      : "Kecamatan",
    "kabupaten"      : "Kab / Kota",
    "provinsi"       : "Provinsi",
    "agama"          : "Agama",
    "status"         : "Status Perkawinan",
    "pekerjaan"      : "Pekerjaan",
    "kewarganegaraan": "Kewarganegaraan",
    "berlaku"        : "Berlaku Hingga",
}

# Field yang berisi foto (Base64) — tidak disimpan ke JSON
FIELD_FOTO = {"foto", "photo", "image", "gambar", "picture", "img", "foto_ktp"}

# ─────────────────────────────────────────
#  SIMPAN FOTO BASE64 KE FILE
# ─────────────────────────────────────────
def simpan_foto(base64_str: str, nik: str = "") -> str:
    """Decode Base64 dan simpan sebagai file JPG. Kembalikan path file."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]

        img_bytes = base64.b64decode(base64_str)

        waktu_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nama_file = f"{nik}_{waktu_str}.jpg" if nik else f"foto_{waktu_str}.jpg"
        path_file = os.path.join(FOTO_DIR, nama_file)

        with open(path_file, "wb") as f:
            f.write(img_bytes)

        log.info(f"📸 Foto KTP disimpan → {path_file}")
        return path_file

    except Exception as e:
        log.error(f"❌ Gagal decode foto: {e}")
        return ""

# ─────────────────────────────────────────
#  SIMPAN DATA KTP KE JSON
# ─────────────────────────────────────────
def simpan_data(data: dict, path_foto: str = ""):
    """
    Append satu record KTP ke file JSON.
    Struktur file: array JSON  →  [ {...}, {...}, ... ]
    Field foto (Base64) diganti dengan path file-nya.
    """
    # ── Bangun record bersih (tanpa raw Base64) ──────────
    record = {}
    for key, val in data.items():
        if key.lower() in FIELD_FOTO:
            record[key] = f"[BASE64 - lihat {path_foto}]" if path_foto else "[BASE64]"
        else:
            record[key] = val

    # Tambahkan metadata
    record["_waktu_baca"] = datetime.datetime.now().isoformat()
    if path_foto:
        record["_path_foto"] = path_foto

    # ── Baca array yang sudah ada (jika file eksis) ───────
    records = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    records = json.loads(content)
                    if not isinstance(records, list):
                        # File rusak / bukan array — backup lalu mulai baru
                        backup = LOG_FILE + ".bak"
                        os.rename(LOG_FILE, backup)
                        log.warning(f"⚠️  Format JSON tidak valid, di-backup ke {backup}")
                        records = []
        except json.JSONDecodeError as e:
            backup = LOG_FILE + ".bak"
            os.rename(LOG_FILE, backup)
            log.warning(f"⚠️  JSON decode error ({e}), di-backup ke {backup}")
            records = []

    # ── Append & tulis ulang ──────────────────────────────
    records.append(record)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    log.info(f"✅ Data KTP disimpan → {LOG_FILE}  (total: {len(records)} record)")

# ─────────────────────────────────────────
#  TAMPILKAN DATA KTP DI TERMINAL
# ─────────────────────────────────────────
def tampilkan_data(data: dict, path_foto: str = ""):
    print("\n" + "="*55)
    print("        📇  DATA KTP-el DITERIMA")
    print("="*55)
    for key, val in data.items():
        if key.lower() in FIELD_FOTO:
            print(f"  {'Foto KTP':<22}: [BASE64 {len(val)} karakter]")
        else:
            nama_field = LABEL.get(key.lower(), key.upper())
            print(f"  {nama_field:<22}: {val}")
    if path_foto:
        print(f"  {'Path Foto':<22}: {path_foto}")
    print("="*55 + "\n")

# ─────────────────────────────────────────
#  PROSES DATA KTP
# ─────────────────────────────────────────
def proses_data(data: dict):
    path_foto = ""
    nik = ""

    for key, val in data.items():
        if key.lower() == "nik":
            nik = str(val)
            break

    for key, val in data.items():
        if key.lower() in FIELD_FOTO and val:
            path_foto = simpan_foto(str(val), nik)
            break

    tampilkan_data(data, path_foto)
    simpan_data(data, path_foto)

# ─────────────────────────────────────────
#  HTTP REQUEST HANDLER
# ─────────────────────────────────────────
class KTPHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Logging sudah ditangani oleh `log`

    # ── POST ────────────────────────────────────────────
    def do_POST(self):
        client_ip = self.client_address[0]
        log.info(f"📥 POST dari {client_ip} → {self.path}")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        data_ktp = {}
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                data_ktp = json.loads(body)
                log.info("  Format: JSON")
            except Exception:
                data_ktp = {"raw": body}
        elif "application/x-www-form-urlencoded" in content_type:
            parsed = urllib.parse.parse_qs(body)
            data_ktp = {k: v[0] for k, v in parsed.items()}
            log.info("  Format: Form URL Encoded")
        else:
            try:
                data_ktp = json.loads(body)
                log.info("  Format: JSON (auto-detect)")
            except Exception:
                data_ktp = {"raw": body}
                log.info("  Format: Raw Text")

        if data_ktp:
            proses_data(data_ktp)

        self._kirim_json(200, {
            "status" : "success",
            "message": "Data KTP berhasil diterima",
            "waktu"  : datetime.datetime.now().isoformat()
        })

    # ── GET ─────────────────────────────────────────────
    def do_GET(self):
        client_ip = self.client_address[0]
        log.info(f"📥 GET dari {client_ip} → {self.path}")
        self._kirim_json(200, {
            "status" : "online",
            "server" : f"{SERVER_IP}:{PORT}",
            "waktu"  : datetime.datetime.now().isoformat(),
            "info"   : "KTP HTTP Server aktif ✅"
        })

    # ── Helper ──────────────────────────────────────────
    def _kirim_json(self, kode: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(kode)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("   🖥️   KTP HTTP SERVER - PT. INTI Identik")
    print("="*55)
    print(f"  IP Server  : {SERVER_IP}")
    print(f"  Port       : {PORT}")
    print(f"  Endpoint   : POST http://{SERVER_IP}:{PORT}/")
    print(f"  Log KTP    : {LOG_FILE}")
    print(f"  Foto KTP   : {FOTO_DIR}/")
    print(f"  Waktu      : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)
    print("  ✅ Server aktif, menunggu data dari KTP Reader...")
    print("  🛑 Tekan Ctrl+C untuk menghentikan\n")

    server = HTTPServer((HOST, PORT), KTPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan.")
        server.server_close()

if __name__ == "__main__":
    main()