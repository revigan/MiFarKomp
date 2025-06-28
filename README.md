# MiFarKomp - Aplikasi Kompresi File Modern

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Educational-yellow.svg)](LICENSE)

**MiFarKomp** adalah aplikasi web modern untuk kompresi file yang mendukung berbagai format file dengan algoritma kompresi yang canggih. Dibangun dengan Python Flask dan antarmuka web yang responsif menggunakan Tailwind CSS.

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Struktur Proyek](#-struktur-proyek)
- [Instalasi](#-instalasi)
- [Cara Menjalankan](#-cara-menjalankan)
- [Cara Penggunaan](#-cara-penggunaan)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Algoritma Kompresi](#-algoritma-kompresi)
- [API Endpoints](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Kontributor](#-kontributor)
- [Lisensi](#-lisensi)

## ✨ Fitur Utama

### 🖼️ Kompresi Gambar

- **Format yang Didukung:** JPG, JPEG, PNG, GIF, BMP
- **Fitur Kompresi:**
  - Resize otomatis berdasarkan level kompresi
  - Optimasi kualitas gambar
  - Pembersihan metadata (EXIF, ICC Profile)
  - Kompresi progresif untuk JPEG
  - Konversi format untuk optimasi (BMP → PNG)

### 📄 Kompresi PDF

- **Metode Utama:** Ghostscript (jika tersedia)
- **Fallback:** pikepdf untuk kompresi alternatif
- **Pengaturan Kompresi:**
  - `/screen` - Kompresi maksimal untuk tampilan layar
  - `/ebook` - Keseimbangan untuk e-book
  - `/printer` - Kualitas tinggi untuk cetak

### 📊 Kompresi Dokumen Office

- **Format yang Didukung:** DOCX, XLSX, PPTX
- **Fitur Kompresi:**
  - Kompresi gambar internal dalam dokumen
  - Optimasi XML dan metadata
  - Pengemasan ulang dengan kompresi ZIP tingkat tinggi
  - Penghapusan elemen yang tidak perlu

### 🔧 Algoritma Kompresi Klasik

- **Huffman Coding:** Kompresi lossless berbasis frekuensi karakter
- **Run Length Encoding (RLE):** Kompresi untuk data berulang
- **Tersedia di modul:** `kompresi/huffman.py` dan `kompresi/rle.py`

## 🛠️ Teknologi yang Digunakan

### Backend

- **Python 3.6+** - Bahasa pemrograman utama
- **Flask 2.0.1** - Web framework
- **Pillow 11.2.1** - Pemrosesan gambar
- **pikepdf** - Kompresi PDF
- **python-docx** - Pemrosesan dokumen Word
- **openpyxl** - Pemrosesan spreadsheet Excel
- **python-pptx** - Pemrosesan presentasi PowerPoint
- **PyPDF2** - Manipulasi PDF

### Frontend

- **HTML5** - Struktur halaman web
- **Tailwind CSS** - Framework CSS modern
- **JavaScript (Vanilla)** - Interaktivitas client-side
- **Font Awesome** - Ikon dan elemen visual

### Tools Eksternal (Opsional)

- **Ghostscript** - Kompresi PDF tingkat tinggi
- **LibreOffice** - Konversi dokumen Office

## 📁 Struktur Proyek

```
MiFarKomp/
├── app.py                 # Aplikasi utama Flask
├── requirements.txt       # Dependensi Python
├── README.md             # Dokumentasi proyek
├── kompresi/             # Modul algoritma kompresi
│   ├── huffman.py        # Implementasi Huffman Coding
│   └── rle.py           # Implementasi Run Length Encoding
├── templates/            # Template HTML
│   ├── index.html       # Halaman utama
│   ├── result.html      # Halaman hasil kompresi
│   └── about.html       # Halaman tentang
├── uploads/             # Folder file upload sementara
├── results/             # Folder hasil kompresi
└── __pycache__/         # Cache Python (otomatis)
```

## 🚀 Instalasi

### Prasyarat

- Python 3.6 atau lebih baru
- pip (package manager Python)
- Git (untuk clone repository)

### Langkah Instalasi

1. **Clone Repository**

   ```bash
   git clone https://github.com/username/MiFarKomp.git
   cd MiFarKomp
   ```

2. **Buat Virtual Environment (Direkomendasikan)**

   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instal Dependensi**

   ```bash
   pip install -r requirements.txt
   ```

4. **Instal Tools Eksternal (Opsional)**

   **Ghostscript (untuk kompresi PDF maksimal):**

   - Windows: Download dari [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html)
   - macOS: `brew install ghostscript`
   - Linux: `sudo apt-get install ghostscript`

   **LibreOffice (untuk konversi dokumen):**

   - Download dari [libreoffice.org](https://www.libreoffice.org/download/download-libreoffice/)

## ▶️ Cara Menjalankan

1. **Aktifkan Virtual Environment (jika menggunakan)**

   ```bash
   # Windows
   .\venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

2. **Jalankan Aplikasi**

   ```bash
   python app.py
   ```

3. **Akses Aplikasi**
   - Buka browser dan kunjungi: `http://localhost:5000`
   - Aplikasi akan berjalan di mode development

## 📖 Cara Penggunaan

### 1. Upload File

- Klik area upload atau seret file ke area yang disediakan
- Format yang didukung: JPG, PNG, PDF, DOCX, XLSX, PPTX

### 2. Pilih Level Kompresi

- **Rendah:** Kualitas terbaik, ukuran file tidak terlalu kecil
- **Sedang:** Keseimbangan antara kualitas dan ukuran (default)
- **Tinggi:** Ukuran file terkecil, kualitas mungkin menurun

### 3. Proses Kompresi

- Klik tombol "Upload & Kompresi"
- Tunggu proses selesai (akan ada indikator loading)

### 4. Download Hasil

- Lihat statistik kompresi di halaman hasil
- Klik "Download File" untuk mengunduh file yang sudah dikompresi

## 🏗️ Arsitektur Sistem

### Frontend (Client-Side)

```
Browser → HTML/CSS/JS → User Interface
```

**Komponen:**

- **HTML5:** Struktur halaman web
- **Tailwind CSS:** Styling dan responsivitas
- **JavaScript:** Interaktivitas, validasi form, drag-and-drop

### Backend (Server-Side)

```
Flask App → File Processing → Compression Algorithms → Results
```

**Komponen:**

- **Flask:** Web framework, routing, request handling
- **File Processing:** Upload handling, format detection
- **Compression Engine:** Pillow, Ghostscript, pikepdf
- **Session Management:** Menyimpan data sementara

### Alur Data

1. User upload file → Flask menerima request
2. File disimpan di `uploads/` folder
3. Backend mendeteksi format dan memilih algoritma
4. File diproses sesuai algoritma kompresi
5. Hasil disimpan di `results/` folder
6. Statistik kompresi dihitung dan ditampilkan
7. User dapat download file hasil

## 🔬 Algoritma Kompresi

### 1. Kompresi Gambar (Pillow)

```python
def compress_image(filepath, outdir, compression_level='medium'):
    # Resize gambar berdasarkan level kompresi
    # Optimasi kualitas (JPEG: 60-85, PNG: compress_level 6-9)
    # Pembersihan metadata
    # Konversi format jika diperlukan
```

**Pengaturan Level:**

- **Rendah:** Quality 85, max size 2048px
- **Sedang:** Quality 75, max size 1280px
- **Tinggi:** Quality 60, max size 800px

### 2. Kompresi PDF (Ghostscript + pikepdf)

```python
def compress_pdf_ghostscript(filepath, outdir, compression_level='medium'):
    # Cek ketersediaan Ghostscript
    # Jalankan perintah kompresi
    # Fallback ke pikepdf jika Ghostscript tidak tersedia
```

**Pengaturan PDF:**

- **Rendah:** `/printer` - Kualitas tinggi
- **Sedang:** `/ebook` - Keseimbangan
- **Tinggi:** `/screen` - Kompresi maksimal

### 3. Kompresi Dokumen Office

```python
def compress_office_images(filepath, outdir, office_type, compression_level):
    # Extract file Office (ZIP)
    # Kompresi gambar internal
    # Optimasi XML dan metadata
    # Re-package dengan kompresi ZIP tinggi
```

### 4. Algoritma Klasik (Huffman & RLE)

```python
# Huffman Coding
from kompresi.huffman import huffman_compress
compressed = huffman_compress('file.txt')

# Run Length Encoding
from kompresi.rle import rle_compress
compressed = rle_compress('file.txt')
```

## 🔌 API Endpoints

| Endpoint              | Method    | Deskripsi                  |
| --------------------- | --------- | -------------------------- |
| `/`                   | GET, POST | Halaman utama, upload file |
| `/result`             | GET       | Halaman hasil kompresi     |
| `/download`           | GET       | Download file hasil        |
| `/about`              | GET       | Halaman tentang aplikasi   |
| `/preview/<filename>` | GET       | Preview gambar (jika ada)  |

## 🐛 Troubleshooting

### Masalah Umum

**1. File tidak bisa diupload**

- Pastikan format file didukung
- Cek ukuran file (maksimal 50MB)
- Pastikan folder `uploads/` ada dan writable

**2. Kompresi gagal**

- Cek log terminal untuk error detail
- Pastikan semua dependensi terinstall
- Cek permission folder `results/`

**3. PDF tidak terkompres maksimal**

- Install Ghostscript dan pastikan path benar
- Cek versi Ghostscript (minimal 9.0)

**4. Aplikasi tidak bisa diakses**

- Pastikan port 5000 tidak digunakan aplikasi lain
- Cek firewall settings
- Pastikan Flask berjalan dengan benar

**5. Error "Module not found"**

- Aktifkan virtual environment
- Jalankan `pip install -r requirements.txt`
- Cek versi Python (minimal 3.6)

### Log dan Debug

```bash
# Jalankan dengan debug mode
python app.py

# Cek log di terminal untuk informasi detail
# Log akan menampilkan proses kompresi dan error jika ada
```

## 👥 Kontributor

**Tim Pengembang:**

- **Mohammad Farikhin** - Backend Developer
- **Mikholas Andi Wijayanto** - Frontend Developer & UI/UX Designer

**Kontribusi:**

- Backend: Python Flask, algoritma kompresi
- Frontend: HTML, CSS, JavaScript
- UI/UX: Desain antarmuka, responsivitas
- Dokumentasi: README, manual penggunaan

## 📄 Lisensi

Proyek ini dibuat untuk tujuan **edukasi dan pembelajaran**.

**Peringatan:**

- Jangan gunakan untuk data sensitif atau produksi
- Hasil kompresi mungkin tidak 100% optimal
- Backup file original sebelum kompresi

## 🤝 Kontribusi

Kontribusi sangat diterima! Untuk berkontribusi:

1. Fork repository
2. Buat branch fitur baru (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request


---

**Dibuat dengan ❤️ oleh Tim MiFarKomp**

_"Kompresi file jadi mudah dan efisien"_
