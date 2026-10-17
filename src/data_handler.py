import os
import pandas as pd
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "logistics.db")

def init_db():
    """Inisialisasi database SQLite, buat tabel jika belum ada, dan isi data awal satu kali."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Buat tabel aset
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY,
            asset_type TEXT,
            capacity_tons REAL,
            base_price REAL,
            location_score REAL,
            demand_index REAL
        )
    ''')
    
    # Buat tabel mitra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partners (
            partner_id TEXT PRIMARY KEY,
            partner_name TEXT,
            req_type TEXT,
            budget REAL,
            reliability_score REAL
        )
    ''')

    # Buat tabel log audit aktivitas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action_type TEXT,
            description TEXT
        )
    ''')

    # Buat tabel metadata untuk mencatat status inisialisasi data awal (seeding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute("SELECT value FROM app_meta WHERE key = 'seeded'")
    is_seeded = cursor.fetchone() is not None

    if not is_seeded:
        # Jika tabel assets kosong saat pertama kali inisialisasi, masukkan data awal
        cursor.execute("SELECT COUNT(*) FROM assets")
        if cursor.fetchone()[0] == 0:
            initial_assets = [
                ('AST-001', 'Warehouse', 5000, 10000000, 0.9, 1.2),
                ('AST-002', 'Truck', 20, 2500000, 0.7, 1.0),
                ('AST-003', 'Cold Storage', 1000, 15000000, 0.85, 1.5)
            ]
            cursor.executemany("INSERT INTO assets VALUES (?,?,?,?,?,?)", initial_assets)
            
        # Jika tabel partners kosong saat pertama kali inisialisasi, masukkan data awal
        cursor.execute("SELECT COUNT(*) FROM partners")
        if cursor.fetchone()[0] == 0:
            initial_partners = [
                ('PTN-101', 'Logistik Cepat', 'Warehouse', 11500000, 0.95),
                ('PTN-102', 'Trans Nusantara', 'Truck', 2000000, 0.80),
                ('PTN-103', 'Segar ColdChain', 'Cold Storage', 20000000, 0.90),
                ('PTN-104', 'Agro Makmur', 'Warehouse', 10500000, 0.85)
            ]
            cursor.executemany("INSERT INTO partners VALUES (?,?,?,?,?)", initial_partners)

        cursor.execute("INSERT INTO app_meta (key, value) VALUES ('seeded', '1')")
        
    conn.commit()
    conn.close()

def log_activity(action_type, description):
    """Mencatat aktivitas pengguna ke dalam tabel audit_logs dengan timestamp saat ini."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO audit_logs (timestamp, action_type, description) VALUES (?, ?, ?)", 
                   (timestamp, action_type, description))
    conn.commit()
    conn.close()

def load_audit_logs():
    """Membaca seluruh riwayat log audit dari database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id AS 'Log ID', timestamp AS 'Waktu', action_type AS 'Aksi', description AS 'Keterangan' FROM audit_logs ORDER BY id DESC", conn)
    conn.close()
    return df

def load_assets_data():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM assets", conn)
    conn.close()
    return df

def load_partners_data():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM partners", conn)
    conn.close()
    return df

def save_asset_to_db(data):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute('''
            INSERT INTO assets (asset_id, asset_type, capacity_tons, base_price, location_score, demand_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['asset_id'], data['asset_type'], data['capacity_tons'], data['base_price'], data['location_score'], data['demand_index']))
        conn.commit()
        success, msg = True, "Sukses"
    except sqlite3.IntegrityError:
        success, msg = False, f"Aset dengan ID {data['asset_id']} sudah ada di database!"
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("TAMBAH ASET", f"Menambahkan aset baru ID: {data['asset_id']} ({data['asset_type']})")
    return success, msg

def save_partner_to_db(data):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute('''
            INSERT INTO partners (partner_id, partner_name, req_type, budget, reliability_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['partner_id'], data['partner_name'], data['req_type'], data['budget'], data['reliability_score']))
        conn.commit()
        success, msg = True, "Sukses"
    except sqlite3.IntegrityError:
        success, msg = False, f"Mitra dengan ID {data['partner_id']} sudah ada di database!"
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("TAMBAH MITRA", f"Menambahkan mitra baru: {data['partner_name']} (ID: {data['partner_id']})")
    return success, msg

def update_asset_in_db(data):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute('''
            UPDATE assets 
            SET asset_type = ?, capacity_tons = ?, base_price = ?, location_score = ?, demand_index = ?
            WHERE asset_id = ?
        ''', (data['asset_type'], data['capacity_tons'], data['base_price'], 
              data['location_score'], data['demand_index'], data['asset_id']))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Aset berhasil diperbarui."
        else:
            success, msg = False, "Aset tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("EDIT ASET", f"Memperbarui data aset ID: {data['asset_id']}")
    return success, msg

def update_partner_in_db(data):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute('''
            UPDATE partners 
            SET partner_name = ?, req_type = ?, budget = ?, reliability_score = ?
            WHERE partner_id = ?
        ''', (data['partner_name'], data['req_type'], data['budget'], 
              data['reliability_score'], data['partner_id']))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Mitra berhasil diperbarui."
        else:
            success, msg = False, "Mitra tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("EDIT MITRA", f"Memperbarui data mitra ID: {data['partner_id']}")
    return success, msg

def delete_asset_from_db(asset_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Aset berhasil dihapus."
        else:
            success, msg = False, "Aset tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("HAPUS ASET", f"Menghapus aset ID: {asset_id}")
    return success, msg

def delete_partner_from_db(partner_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    success, msg = False, ""
    try:
        cursor.execute("DELETE FROM partners WHERE partner_id = ?", (partner_id,))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Mitra berhasil dihapus."
        else:
            success, msg = False, "Mitra tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()

    if success:
        log_activity("HAPUS MITRA", f"Menghapus mitra ID: {partner_id}")
    return success, msg

def import_assets_from_file(file_path):
    """
    Mengimpor data aset massal dari file Excel (.xlsx) atau CSV (.csv) ke dalam database SQLite.
    Mendukung upsert: baris dengan ID baru akan di-INSERT, baris dengan ID yang sudah ada akan di-UPDATE.
    """
    init_db()
    if not os.path.exists(file_path):
        return False, f"File {file_path} tidak ditemukan.", 0, 0, 0

    lower_path = file_path.lower()
    try:
        if lower_path.endswith('.xlsx') or lower_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif lower_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return False, "Format file tidak didukung. Harap gunakan file .xlsx atau .csv.", 0, 0, 0
    except Exception as e:
        return False, f"Gagal membaca file: {str(e)}", 0, 0, 0

    if df.empty:
        return False, "File yang diimpor tidak memiliki data (kosong).", 0, 0, 0

    # Normalisasi nama kolom: huruf kecil, trim spasi, ganti spasi dengan underscore
    normalized_cols = {col: str(col).strip().lower().replace(" ", "_") for col in df.columns}
    df = df.rename(columns=normalized_cols)

    required_cols = {'asset_id', 'asset_type', 'capacity_tons', 'base_price', 'location_score', 'demand_index'}
    missing = required_cols - set(df.columns)
    if missing:
        return False, f"Kolom wajib tidak lengkap pada file. Kolom yang hilang: {', '.join(sorted(missing))}", 0, 0, 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_count = 0
    updated_count = 0
    error_count = 0

    try:
        for _, row in df.iterrows():
            asset_id = str(row['asset_id']).strip()
            if not asset_id or asset_id.lower() == 'nan':
                error_count += 1
                continue

            asset_type = str(row['asset_type']).strip()
            try:
                capacity = float(row['capacity_tons'])
                price = float(row['base_price'])
                loc_score = float(row['location_score'])
                demand = float(row['demand_index'])
            except (ValueError, TypeError):
                error_count += 1
                continue

            cursor.execute("SELECT 1 FROM assets WHERE asset_id = ?", (asset_id,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute('''
                    UPDATE assets 
                    SET asset_type = ?, capacity_tons = ?, base_price = ?, location_score = ?, demand_index = ?
                    WHERE asset_id = ?
                ''', (asset_type, capacity, price, loc_score, demand, asset_id))
                updated_count += 1
            else:
                cursor.execute('''
                    INSERT INTO assets (asset_id, asset_type, capacity_tons, base_price, location_score, demand_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (asset_id, asset_type, capacity, price, loc_score, demand))
                new_count += 1

        conn.commit()
    except Exception as e:
        return False, f"Terjadi kesalahan saat memproses database: {str(e)}", new_count, updated_count, error_count
    finally:
        conn.close()

    total_success = new_count + updated_count
    if total_success > 0:
        filename = os.path.basename(file_path)
        log_activity("IMPORT ASET", f"Impor {total_success} data aset dari {filename} ({new_count} baru, {updated_count} diperbarui)")
        msg = f"Berhasil mengimpor {total_success} data aset ({new_count} baru, {updated_count} diperbarui)."
        if error_count > 0:
            msg += f" {error_count} baris diabaikan karena data tidak valid."
        return True, msg, new_count, updated_count, error_count
    else:
        return False, f"Tidak ada data valid yang dapat diimpor. {error_count} baris bermasalah.", 0, 0, error_count

def import_partners_from_file(file_path):
    """
    Mengimpor data mitra massal dari file Excel (.xlsx) atau CSV (.csv) ke dalam database SQLite.
    Mendukung upsert: baris dengan ID baru akan di-INSERT, baris dengan ID yang sudah ada akan di-UPDATE.
    """
    init_db()
    if not os.path.exists(file_path):
        return False, f"File {file_path} tidak ditemukan.", 0, 0, 0

    lower_path = file_path.lower()
    try:
        if lower_path.endswith('.xlsx') or lower_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif lower_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return False, "Format file tidak didukung. Harap gunakan file .xlsx atau .csv.", 0, 0, 0
    except Exception as e:
        return False, f"Gagal membaca file: {str(e)}", 0, 0, 0

    if df.empty:
        return False, "File yang diimpor tidak memiliki data (kosong).", 0, 0, 0

    # Normalisasi kolom
    normalized_cols = {col: str(col).strip().lower().replace(" ", "_") for col in df.columns}
    df = df.rename(columns=normalized_cols)

    # Antisipasi alias kolom
    if 'req_type' not in df.columns and 'requirement_type' in df.columns:
        df['req_type'] = df['requirement_type']
    if 'partner_name' not in df.columns and 'name' in df.columns:
        df['partner_name'] = df['name']

    required_cols = {'partner_id', 'partner_name', 'req_type', 'budget', 'reliability_score'}
    missing = required_cols - set(df.columns)
    if missing:
        return False, f"Kolom wajib tidak lengkap pada file. Kolom yang hilang: {', '.join(sorted(missing))}", 0, 0, 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_count = 0
    updated_count = 0
    error_count = 0

    try:
        for _, row in df.iterrows():
            partner_id = str(row['partner_id']).strip()
            partner_name = str(row['partner_name']).strip()
            if not partner_id or partner_id.lower() == 'nan' or not partner_name or partner_name.lower() == 'nan':
                error_count += 1
                continue

            req_type = str(row['req_type']).strip()
            try:
                budget = float(row['budget'])
                rel_score = float(row['reliability_score'])
            except (ValueError, TypeError):
                error_count += 1
                continue

            cursor.execute("SELECT 1 FROM partners WHERE partner_id = ?", (partner_id,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute('''
                    UPDATE partners 
                    SET partner_name = ?, req_type = ?, budget = ?, reliability_score = ?
                    WHERE partner_id = ?
                ''', (partner_name, req_type, budget, rel_score, partner_id))
                updated_count += 1
            else:
                cursor.execute('''
                    INSERT INTO partners (partner_id, partner_name, req_type, budget, reliability_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (partner_id, partner_name, req_type, budget, rel_score))
                new_count += 1

        conn.commit()
    except Exception as e:
        return False, f"Terjadi kesalahan saat memproses database: {str(e)}", new_count, updated_count, error_count
    finally:
        conn.close()

    total_success = new_count + updated_count
    if total_success > 0:
        filename = os.path.basename(file_path)
        log_activity("IMPORT MITRA", f"Impor {total_success} data mitra dari {filename} ({new_count} baru, {updated_count} diperbarui)")
        msg = f"Berhasil mengimpor {total_success} data mitra ({new_count} baru, {updated_count} diperbarui)."
        if error_count > 0:
            msg += f" {error_count} baris diabaikan karena data tidak valid."
        return True, msg, new_count, updated_count, error_count
    else:
        return False, f"Tidak ada data valid yang dapat diimpor. {error_count} baris bermasalah.", 0, 0, error_count