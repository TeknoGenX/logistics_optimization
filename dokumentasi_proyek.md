# 🚛 Sistem Optimasi Harga Aset & Seleksi Mitra (Logistik)

Aplikasi berbasis Python (CLI & GUI) yang dirancang untuk mendigitalisasi dan mengotomatisasi proses manual dalam penetapan harga sewa aset dan seleksi mitra di industri logistik.

---

## 📌 Konteks Bisnis

- **Industri:** Logistik
- **Latar Belakang:** Proses seleksi mitra dan penetapan harga sewa aset saat ini masih dilakukan secara manual, memakan waktu, dan belum terstandarisasi.
- **Core Problem:** Bagaimana mengoptimalkan proses penetapan harga aset dan seleksi mitra secara efisien dan berbasis data?
- **Dampak Masalah:** 
  - Kesulitan dalam memasarkan aset secara proaktif.
  - Potensi ketidaktepatan harga (*pricing error* / tidak mengikuti *demand* pasar).
  - Inefisiensi proses bisnis secara keseluruhan.
- **Opportunity Area:** 
  - *Pricing optimization model* (Model penetapan harga dinamis).
  - *Partner matching platform* (Sistem pencocokan mitra otomatis).
  - *Data-driven decision system* (Sistem pengambilan keputusan berbasis data).

---

## 🚀 Fitur Utama

1. **Dynamic Pricing Engine (`pricing_optimizer.py`)**
   Sistem secara otomatis menghitung harga optimal sewa aset berdasarkan harga dasar, skor strategis lokasi, indeks permintaan (*demand index*), dan target margin profit.
2. **AI-Scoring Partner Matcher (`partner_matcher.py`)**
   Sistem merekomendasikan mitra/vendor terbaik berdasarkan kesesuaian tipe aset, toleransi *budget* mitra, dan rekam jejak (*reliability score*) mitra.
3. **Modular Architecture**
   Logika bisnis dipisah dari antarmuka pengguna, memungkinkan sistem untuk di-skala-kan (diubah menjadi REST API atau Web App) di masa depan tanpa merombak algoritma inti.
4. **Desktop GUI (PyQt5)**
   Dilengkapi dengan antarmuka grafis yang *user-friendly* untuk tim operasional menampilkan data aset, data mitra, hasil optimasi, dan hasil seleksi hanya dengan beberapa klik.

---

## 📂 Struktur Direktori Proyek

```text
logistics_optimization/
│
├── src/
│   ├── __init__.py
│   ├── data_handler.py        # Modul penarik data aset dan mitra (Mock-up)
│   ├── pricing_optimizer.py   # Modul algoritma penetapan harga dinamis
│   └── partner_matcher.py     # Modul algoritma seleksi & pencocokan mitra
│
├── requirements.txt           # Daftar dependensi library Python
├── main.py                    # Aplikasi utama versi Terminal / CLI
├── main_gui.py                # Aplikasi utama versi Desktop / GUI (PyQt5)
└── README.md                  # Dokumentasi proyek
```

---

## 🛠️ Instalasi & Persiapan Lingkungan

Proyek ini dibangun dan diuji pada lingkungan Linux (Kali Linux). Disarankan menggunakan *Virtual Environment* (venv) agar tidak mengganggu dependensi sistem.

1. **Clone/Buat Direktori Proyek**
   ```bash
   mkdir -p logistics_optimization
   cd logistics_optimization
   ```

2. **Buat & Aktifkan Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependensi**
   Pastikan Anda sudah berada di dalam environment `(venv)`, lalu jalankan:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Cara Penggunaan

### 1. Menjalankan Versi Terminal (CLI)
Gunakan versi ini jika Anda ingin menjalankan skrip di *server environment* tanpa antarmuka grafis.
```bash
python3 main.py
```
*Output akan langsung tercetak di terminal, menampilkan harga optimal baru dan daftar mitra yang direkomendasikan dengan skor kecocokan > 50%.*

### 2. Menjalankan Versi Desktop (GUI)
Gunakan versi ini untuk pengalaman pengguna (*User Experience*) yang interaktif.
```bash
python3 main_gui.py
```
**Langkah Penggunaan GUI:**
1. Klik tombol **"1. Load Data"** untuk memuat data *mock-up* ke dalam tabel.
2. Klik tombol **"2. Hitung Dynamic Pricing"** untuk melihat perubahan dan penetapan harga aset terbaru.
3. Klik tombol **"3. Cari Mitra Terbaik"** untuk melihat hasil seleksi mitra berbasis *AI-scoring*.

---
*Dikembangkan sebagai prototipe solusi sistem terintegrasi (Data-driven decision system).*