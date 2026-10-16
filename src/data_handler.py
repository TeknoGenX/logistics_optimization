import pandas as pd
import sqlite3
from datetime import datetime

DB_FILE = "logistics.db"

def init_db():
    """Inisialisasi database SQLite, buat tabel jika belum ada, dan isi data awal."""
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
    
    # Jika tabel assets kosong, masukkan data awal
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        initial_assets = [
            ('AST-001', 'Warehouse', 5000, 10000000, 0.9, 1.2),
            ('AST-002', 'Truck', 20, 2500000, 0.7, 1.0),
            ('AST-003', 'Cold Storage', 1000, 15000000, 0.85, 1.5)
        ]
        cursor.executemany("INSERT INTO assets VALUES (?,?,?,?,?,?)", initial_assets)
        
    # Jika tabel partners kosong, masukkan data awal
    cursor.execute("SELECT COUNT(*) FROM partners")
    if cursor.fetchone()[0] == 0:
        initial_partners = [
            ('PTN-101', 'Logistik Cepat', 'Warehouse', 11500000, 0.95),
            ('PTN-102', 'Trans Nusantara', 'Truck', 2000000, 0.80),
            ('PTN-103', 'Segar ColdChain', 'Cold Storage', 20000000, 0.90),
            ('PTN-104', 'Agro Makmur', 'Warehouse', 10500000, 0.85)
        ]
        cursor.executemany("INSERT INTO partners VALUES (?,?,?,?,?)", initial_partners)
        
    conn.commit()
    conn.close()

def log_activity(action_type, description):
    """Mencatat aktivitas pengguna ke dalam tabel audit_logs dengan timestamp saat ini."""
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO assets (asset_id, asset_type, capacity_tons, base_price, location_score, demand_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['asset_id'], data['asset_type'], data['capacity_tons'], data['base_price'], data['location_score'], data['demand_index']))
        conn.commit()
        success, msg = True, "Sukses"
        log_activity("TAMBAH ASET", f"Menambahkan aset baru ID: {data['asset_id']} ({data['asset_type']})")
    except sqlite3.IntegrityError:
        success, msg = False, f"Aset dengan ID {data['asset_id']} sudah ada di database!"
    finally:
        conn.close()
    return success, msg

def save_partner_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO partners (partner_id, partner_name, req_type, budget, reliability_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['partner_id'], data['partner_name'], data['req_type'], data['budget'], data['reliability_score']))
        conn.commit()
        success, msg = True, "Sukses"
        log_activity("TAMBAH MITRA", f"Menambahkan mitra baru: {data['partner_name']} (ID: {data['partner_id']})")
    except sqlite3.IntegrityError:
        success, msg = False, f"Mitra dengan ID {data['partner_id']} sudah ada di database!"
    finally:
        conn.close()
    return success, msg

def update_asset_in_db(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
            log_activity("EDIT ASET", f"Memperbarui data aset ID: {data['asset_id']}")
        else:
            success, msg = False, "Aset tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()
    return success, msg

def update_partner_in_db(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
            log_activity("EDIT MITRA", f"Memperbarui data mitra ID: {data['partner_id']}")
        else:
            success, msg = False, "Mitra tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()
    return success, msg

def delete_asset_from_db(asset_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Aset berhasil dihapus."
            log_activity("HAPUS ASET", f"Menghapus aset ID: {asset_id}")
        else:
            success, msg = False, "Aset tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()
    return success, msg

def delete_partner_from_db(partner_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM partners WHERE partner_id = ?", (partner_id,))
        conn.commit()
        if cursor.rowcount > 0:
            success, msg = True, "Mitra berhasil dihapus."
            log_activity("HAPUS MITRA", f"Menghapus mitra ID: {partner_id}")
        else:
            success, msg = False, "Mitra tidak ditemukan."
    except Exception as e:
        success, msg = False, f"Terjadi kesalahan: {str(e)}"
    finally:
        conn.close()
    return success, msg