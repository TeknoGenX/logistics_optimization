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
   Sistem merekomendasikan mitra/vendor terbaik berdasarkan kesesuaian tipe aset, toleransi *budget* mitra, dan rekam jejak (*reliability score*) mitra. Mendukung kustomisasi pembobotan multi-kriteria dan ambang batas kelayakan secara dinamis.
3. **Executive Financial Dashboard & KPI Metrics (`financial_calculator.py`)**
   Menghitung proyeksi pendapatan optimal, potensi kenaikan revenue (uplift %), rincian biaya operasional (BBM, pemeliharaan, depresiasi, overhead), estimasi laba bersih (**Net Profit**) beserta margin laba bersih (%), rasio keterisian aset terpasangkan (*matching ratio*), dan rata-rata skor kualitas mitra secara reaktif.
4. **Import Data Massal Excel & CSV (`data_handler.py`)**
   Mendukung pemuatan data aset dan mitra massal dari file `.xlsx`, `.xls`, dan `.csv` dengan normalisasi header fleksibel serta mekanisme *upsert* cerdas (memperbarui baris ID lama dan menyisipkan baris ID baru).
5. **Database Relasional SQLite & Audit Trail**
   Penyimpanan permanen di `logistics.db` untuk aset, mitra, dan log aktivitas operasional (*audit trail*) secara real-time.
6. **Modular Architecture**
   Logika bisnis dipisah dari antarmuka pengguna, memungkinkan sistem untuk di-skala-kan (diubah menjadi REST API atau Web App) di masa depan tanpa merombak algoritma inti.
7. **Optimasi Alokasi Eksklusif 1-ke-1 (`partner_matcher.py`)**
   Menyelesaikan masalah *Maximum Weight Bipartite Matching* menggunakan algoritma Hungarian (*Kuhn-Munkres*) dan heuristik *Greedy* untuk memasangkan tepat 1 aset ke 1 mitra terbaik tanpa bentrok (*anti double-booking*). Mendukung pemilihan objektif optimasi (*Skor Kecocokan*, *Revenue Optimal*, dan *Deal Value*) serta jaminan fallback murni Python.
8. **Desktop GUI (PyQt5) Interaktif**
   Dilengkapi antarmuka modern dengan 5 kartu ringkasan KPI (termasuk Net Profit), grafik analitik 3-panel (*Matplotlib*), slider interaktif *What-If Analysis* (Margin Pricing & Rasio Biaya Operasional), **Panel & Tab Alokasi Eksklusif 1-ke-1**, **Panel Kontrol Bobot & Threshold Algoritma Seleksi Mitra**, pencarian instan, ekspor multi-sheet Excel (`Alokasi_Eksklusif`, `Rekomendasi_Mitra`, `Harga_Optimal`, `Ringkasan_Finansial`) / CSV, dan integrasi tombol impor.


---

## 📂 Struktur Direktori Proyek

```text
logistics_optimization/
│
├── src/
│   ├── __init__.py
│   ├── data_handler.py            # Modul database SQLite dan penarik data aset & mitra
│   ├── pricing_optimizer.py       # Modul algoritma penetapan harga dinamis
│   ├── partner_matcher.py         # Modul algoritma seleksi & pencocokan mitra
│   └── financial_calculator.py    # Modul analisis finansial & KPI proyeksi pendapatan
│
├── tests/                         # Direktori Unit & Integration Tests otomatis
│   ├── __init__.py
│   ├── test_pricing_optimizer.py      # Pengujian dynamic pricing engine
│   ├── test_partner_matcher.py        # Pengujian AI scoring partner matching
│   ├── test_data_handler.py           # Pengujian operasi database SQLite terisolasi
│   ├── test_financial_calculator.py   # Pengujian kalkulator metrik finansial & KPI
│   └── test_gui.py                    # Pengujian headless antarmuka grafis PyQt5
│
├── requirements.txt               # Daftar dependensi library Python
├── run_tests.py                   # Script test runner otomatis untuk seluruh test suite
├── main.py                        # Aplikasi utama versi Terminal / CLI
├── main_gui.py                    # Aplikasi utama versi Desktop / GUI (PyQt5)
└── README.md                      # Dokumentasi proyek
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
1. Klik tombol **"1. Load Data"** untuk memuat data dari database SQLite ke dalam tabel.
2. Gunakan tombol **"📥 Import Aset"** atau **"📥 Import Mitra"** untuk mengunggah data massal dari file `.xlsx` atau `.csv`. Sistem akan melakukan *upsert* otomatis dan memperbarui tabel serta kartu KPI.
3. Klik tombol **"2. Jalankan Dynamic Pricing"** untuk melihat perubahan dan penetapan harga aset terbaru.
4. Sesuaikan **Slider Margin Profit (What-If Analysis)** untuk simulasi profit dinamis (0% - 50%).
5. Klik tombol **"3. Jalankan Partner Matching"** untuk melihat hasil seleksi mitra berbasis *AI-scoring*.
6. Klik **"💾 Export Laporan Excel/CSV"** untuk menyimpan hasil kalkulasi dan rekomendasi.

### 3. Menjalankan Pengujian Otomatis (Automated Tests)
Gunakan skrip test runner untuk menjalankan seluruh pengujian unit dan integrasi:
```bash
python3 run_tests.py
```
atau menggunakan modul `unittest` bawaan Python:
```bash
python3 -m unittest discover tests
```

---
*Dikembangkan sebagai prototipe solusi sistem terintegrasi (Data-driven decision system).*