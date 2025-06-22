# MiFarKomp

Aplikasi ini merupakan alat kompresi file sederhana yang mendukung beberapa algoritma kompresi seperti Huffman dan Run Length Encoding (RLE). Proyek ini dibuat untuk tujuan pembelajaran dan demonstrasi teknik kompresi data.

## Struktur Direktori

- `app.py` : File utama aplikasi.
- `kompresi/` : Berisi modul algoritma kompresi (`huffman.py`, `rle.py`).
- `results/` : Hasil file yang telah dikompresi atau didekompresi.
- `templates/` : Template HTML untuk tampilan web.
- `uploads/` : Tempat file yang diunggah oleh pengguna.
- `requirements.txt` : Daftar dependensi Python.

## Cara Menjalankan

1. Pastikan Python sudah terinstal di sistem Anda.
2. Install dependensi dengan perintah:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi dengan perintah:
   ```bash
   python app.py
   ```
4. Akses aplikasi melalui browser di alamat yang tertera pada terminal (biasanya `http://localhost:5000`).

## Fitur

- Kompresi dan dekompresi file menggunakan algoritma Huffman dan RLE.
- Antarmuka web sederhana untuk mengunggah dan mengunduh file.

## Catatan

- Proyek ini untuk tujuan edukasi. Jangan gunakan untuk data sensitif atau produksi.
