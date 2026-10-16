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
1. **Data Handler** (`src/data_handler.py`): Memisahkan logika pengambilan data (saat ini menggunakan data mock-up, namun siap dihubungkan ke Database/API).
2. **Pricing Optimizer** (`src/pricing_optimizer.py`): Algoritma yang menghitung harga dinamis (*Dynamic Pricing*) berdasarkan harga dasar, skor lokasi, indeks permintaan (*demand*), dan margin profit. Mencegah *undercutting* atau harga terlalu mahal.
3. **Partner Matcher** (`src/partner_matcher.py`): Algoritma *scoring* yang mencocokkan aset dengan mitra berdasarkan kesesuaian tipe, kecukupan anggaran (budget), dan skor keandalan (reputasi).
4. **GUI (PyQt5)** (`main_gui.py`): Antarmuka desktop interaktif untuk memudahkan tim operasional melakukan simulasi tanpa harus mengerti kode program.

## 🚀 Cara Instalasi & Menjalankan

**1. Persiapan Environment (Direkomendasikan)**

**2. Instalasi Dependensi**
**3. Menjalankan Aplikasi**
- **Versi CLI (Terminal):** `python3 main.py`
- **Versi GUI (Desktop):** `python3 main_gui.py`
