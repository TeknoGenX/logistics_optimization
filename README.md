# 🚛 Sistem Optimasi Harga Aset & Seleksi Mitra (Logistik)

Sistem berbasis Python ini dirancang untuk mendigitalisasi dan mengotomatisasi proses bisnis di industri logistik, khususnya dalam **Penetapan Harga Aset** dan **Seleksi Mitra**.

## 📊 Latar Belakang Bisnis
- **Industri:** Logistik
- **Kondisi Saat Ini:** Proses seleksi mitra dan penetapan harga sewa aset masih dilakukan secara manual dan belum terstandarisasi.
- **Core Problem:** Bagaimana mengoptimalkan proses penetapan harga aset dan seleksi mitra secara efisien dan berbasis data?
- **Dampak Masalah:** Kesulitan dalam memasarkan aset secara proaktif, potensi ketidaktepatan harga, serta inefisiensi proses bisnis.
- **Opportunity Area (Solusi):** Pembangunan model optimasi harga (Pricing optimization model), platform pencocokan mitra (Partner matching platform), dan sistem pengambilan keputusan berbasis data (Data-driven decision system).

## 🛠️ Fitur Utama
Sistem ini dibangun dengan arsitektur **Modular**:
1. **Data Handler & Database SQLite** (`src/data_handler.py`): Mengelola persistensi data aset, mitra, dan riwayat audit logs ke SQLite (`logistics.db`). Mendukung fitur **Import Data Massal** dari file Excel (.xlsx) dan CSV (.csv) dengan mekanisme *upsert* cerdas.
2. **Pricing Optimizer** (`src/pricing_optimizer.py`): Algoritma yang menghitung harga dinamis (*Dynamic Pricing*) berdasarkan harga dasar, skor lokasi, indeks permintaan (*demand*), dan margin profit. Mencegah *undercutting* atau harga terlalu mahal.
3. **Partner Matcher & Exclusive 1-to-1 Assignment** (`src/partner_matcher.py`): Algoritma *scoring* cerdas yang mencocokkan aset dengan mitra berdasarkan kesesuaian tipe, anggaran, dan skor reputasi. Dilengkapi engine **Optimasi Alokasi Eksklusif 1-ke-1** berbasis *Hungarian Bipartite Matching* (anti *double-booking*) dengan opsi objektif (*score*, *revenue*, *deal_value*) dan metode (*Hungarian* vs *Greedy*).
4. **Financial & KPI Dashboard** (`src/financial_calculator.py`): Modul ringkasan eksekutif untuk menghitung total proyeksi pendapatan, kenaikan margin (uplift), estimasi biaya operasional terperinci (BBM, perawatan, depresiasi, overhead), margin laba bersih (**Net Profit Margin**), metrik utilisasi alokasi eksklusif, rasio keterisian aset, dan rata-rata skor kualitas mitra.
5. **GUI Desktop Interaktif (PyQt5)** (`main_gui.py`): Antarmuka desktop modern dengan kartu KPI eksekutif, grafik analitik 3-panel (*Matplotlib*), slider ganda *What-If Analysis*, **Tab & Kontrol Alokasi Eksklusif 1-ke-1**, **Panel & Dialog Pengaturan Bobot Algoritma Matching**, pencarian live, ekspor laporan multi-sheet Excel (`Alokasi_Eksklusif`, `Rekomendasi_Mitra`, `Harga_Optimal`, `Ringkasan_Finansial`) dan CSV, manajemen CRUD, dan tombol impor massal.

## 📥 Format File Impor Data Massal
Sistem menerima file spreadsheet **.xlsx**, **.xls**, atau **.csv** dengan normalisasi kolom otomatis:
- **Data Aset:** `asset_id`, `asset_type`, `capacity_tons`, `base_price`, `location_score`, `demand_index`
- **Data Mitra:** `partner_id`, `partner_name` (atau `name`), `req_type` (atau `requirement_type`), `budget`, `reliability_score`

## 🚀 Cara Instalasi & Menjalankan

**1. Persiapan Virtual Environment (Direkomendasikan)**
```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Instalasi Dependensi**
```bash
pip install -r requirements.txt
```

**3. Menjalankan Aplikasi**
- **Versi CLI (Terminal):** `python3 main.py`
- **Versi GUI (Desktop):** `python3 main_gui.py`
- **Menjalankan Pengujian (Tests):** `python3 run_tests.py`

