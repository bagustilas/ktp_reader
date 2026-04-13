# 📇 KTP HTTP Server — PT. INTI Identik

Server HTTP ringan berbasis Python untuk **menerima, memproses, dan menyimpan data KTP-el** yang dikirim oleh perangkat KTP Reader. Data disimpan dalam format **JSON** dan foto KTP disimpan sebagai file JPG terpisah.

---

## ✨ Fitur

- Menerima data KTP via **POST** (JSON atau Form URL Encoded)
- Menyimpan semua record ke satu file **`ktp_data.json`** (struktur array, append otomatis)
- Foto & tanda tangan Base64 di-**decode** dan disimpan sebagai file JPG di folder `foto_ktp/`
- Konfigurasi server (host, port, path file) lewat file **`.env`** — tanpa library tambahan
- Log aktivitas HTTP tersimpan di **`server.log`**
- Auto-recovery jika file JSON rusak (backup otomatis ke `ktp_data.json.bak`)

---

## 📁 Struktur Folder

```
project/
├── ktp_http_server.py   # Script utama
├── .env                 # Konfigurasi (buat dari .env.example)
├── .env.example         # Template konfigurasi
├── ktp_data.json        # Database JSON (dibuat otomatis)
├── server.log           # Log aktivitas server (dibuat otomatis)
└── foto_ktp/            # Folder penyimpanan foto KTP (dibuat otomatis)
    └── {NIK}_{timestamp}.jpg
```

---

## ⚙️ Konfigurasi `.env`

Salin `.env.example` menjadi `.env` lalu sesuaikan:

```bash
cp .env.example .env
```

Isi file `.env`:

```env
# Server
KTP_HOST       = 0.0.0.0
KTP_PORT       = 8080
KTP_SERVER_IP  = 169.254.112.97

# File & Folder
KTP_LOG_FILE   = ktp_data.json
KTP_LOG_HTTP   = server.log
KTP_FOTO_DIR   = foto_ktp
```

> **Catatan:** Jika file `.env` tidak ada, server tetap berjalan menggunakan nilai default di atas.

> **Keamanan:** Tambahkan `.env` ke `.gitignore` agar tidak ter-commit ke repository.

```gitignore
# .gitignore
.env
ktp_data.json
foto_ktp/
server.log
```

---

## 🚀 Menjalankan Server

### Prasyarat

- Python 3.7+
- Tidak memerlukan library eksternal (hanya standard library)

### Jalankan

```bash
python ktp_http_server.py
```

Output saat server aktif:

```
=======================================================
   🖥️   KTP HTTP SERVER - PT. INTI Identik
=======================================================
  IP Server  : 169.254.112.97
  Port       : 8080
  Endpoint   : POST http://169.254.112.97:8080/
  Log KTP    : ktp_data.json
  Foto KTP   : foto_ktp/
  Waktu      : 2026-04-13 14:00:00
=======================================================
  ✅ Server aktif, menunggu data dari KTP Reader...
  🛑 Tekan Ctrl+C untuk menghentikan
```

---

## 📡 API Endpoint

### `GET /`

Cek status server.

**Response:**
```json
{
  "status": "online",
  "server": "169.254.112.97:8080",
  "waktu": "2026-04-13T14:00:00.000000",
  "info": "KTP HTTP Server aktif ✅"
}
```

---

### `POST /`

Kirim data KTP dari perangkat reader.

**Headers:**
```
Content-Type: application/json
```

**Body (contoh):**
```json
{
  "nik": "3375042106920003",
  "namaLengkap": "BAGUS TILAS HIDAYATULLAH",
  "jenisKelamin": "LAKI-LAKI",
  "tempatLahir": "PEKALONGAN",
  "tanggalLahir": "21-6-1992",
  "agama": "ISLAM",
  "foto": "/9j/4AAQSkZJRgAB..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Data KTP berhasil diterima",
  "waktu": "2026-04-13T14:02:34.123456"
}
```

---

## 💾 Format Penyimpanan JSON

File `ktp_data.json` berstruktur sebagai **array of objects**. Setiap kali data masuk, satu record baru ditambahkan (append).

```json
[
  {
    "nik": "3375042106920003",
    "namaLengkap": "BAGUS TILAS HIDAYATULLAH",
    "jenisKelamin": "LAKI-LAKI",
    "tempatLahir": "PEKALONGAN",
    "tanggalLahir": "21-6-1992",
    "agama": "ISLAM",
    "foto": "[BASE64 - lihat foto_ktp/3375042106920003_20260413_140234.jpg]",
    "_waktu_baca": "2026-04-13T14:02:34.123456",
    "_path_foto": "foto_ktp/3375042106920003_20260413_140234.jpg"
  }
]
```

> Field `foto` dan `ttd` **tidak disimpan** sebagai Base64 di JSON — nilainya diganti dengan path file foto yang sudah disimpan.

---

## 🖼️ Penyimpanan Foto

Foto dan tanda tangan (Base64) otomatis di-decode dan disimpan sebagai file JPG:

```
foto_ktp/{NIK}_{YYYYMMDD}_{HHMMSS}.jpg
```

Contoh: `foto_ktp/3375042106920003_20260413_140234.jpg`

Field yang dikenali sebagai foto: `foto`, `photo`, `image`, `gambar`, `picture`, `img`, `foto_ktp`.

---

## 🔒 Keamanan

| Aspek | Keterangan |
|---|---|
| Konfigurasi sensitif | Disimpan di `.env`, tidak di-hardcode |
| Data Base64 | Tidak tersimpan di JSON, hanya path file-nya |
| File `.env` | Wajib masuk `.gitignore` |
| Log foto | Terpisah dari log data teks |

---

## 🛠️ Pengembangan

### Menguji dengan `curl`

```bash
# Cek status server
curl http://169.254.112.97:8080/

# Kirim data KTP (JSON)
curl -X POST http://169.254.112.97:8080/ \
  -H "Content-Type: application/json" \
  -d '{"nik":"3375042106920003","namaLengkap":"BUDI SANTOSO"}'
```

### Menguji dengan Python

```python
import requests

data = {
    "nik": "3375042106920003",
    "namaLengkap": "BUDI SANTOSO",
    "jenisKelamin": "LAKI-LAKI"
}

response = requests.post("http://169.254.112.97:8080/", json=data)
print(response.json())
```

---

## 👤 Author

**Bagus Tilas**
GitHub: [github.com/bagustilas](https://github.com/bagustilas)

---

*Dibuat untuk PT. INTI Identik — KTP Reader Integration*