import unittest
import os
import tempfile
import sqlite3
import pandas as pd
import src.data_handler as dh

class TestDataHandler(unittest.TestCase):
    def setUp(self):
        # Buat temporary database file khusus untuk testing agar tidak mengotori database utama
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.temp_dir.name, "test_logistics.db")
        self.original_db_file = dh.DB_FILE
        dh.DB_FILE = self.test_db_path

    def tearDown(self):
        # Kembalikan path DB asli dan bersihkan temporary directory
        dh.DB_FILE = self.original_db_file
        self.temp_dir.cleanup()

    def test_init_db_and_seeding(self):
        """Uji inisialisasi database dan seeding data awal."""
        dh.init_db()
        self.assertTrue(os.path.exists(self.test_db_path))

        # Cek data awal yang di-seed
        assets = dh.load_assets_data()
        partners = dh.load_partners_data()
        self.assertEqual(len(assets), 3)
        self.assertEqual(len(partners), 4)

        # Hapus data aset dan jalankan init_db lagi
        dh.delete_asset_from_db('AST-001')
        dh.init_db()

        # Pastikan tidak terjadi re-seeding otomatis (karena flag app_meta 'seeded')
        assets_after = dh.load_assets_data()
        self.assertEqual(len(assets_after), 2)

    def test_asset_crud_lifecycle(self):
        """Uji siklus hidup data aset: Create, Read, Update, Delete."""
        new_asset = {
            'asset_id': 'AST-TEST',
            'asset_type': 'Warehouse',
            'capacity_tons': 1200.0,
            'base_price': 8000000.0,
            'location_score': 0.85,
            'demand_index': 1.1
        }
        # 1. Create
        success, msg = dh.save_asset_to_db(new_asset)
        self.assertTrue(success)

        # 2. Read
        assets = dh.load_assets_data()
        self.assertIn('AST-TEST', assets['asset_id'].values)

        # 3. Duplicate ID prevention
        dup_success, dup_msg = dh.save_asset_to_db(new_asset)
        self.assertFalse(dup_success)
        self.assertIn('sudah ada', dup_msg)

        # 4. Update
        updated_asset = new_asset.copy()
        updated_asset['base_price'] = 9500000.0
        upd_success, upd_msg = dh.update_asset_in_db(updated_asset)
        self.assertTrue(upd_success)
        
        assets_updated = dh.load_assets_data()
        val = assets_updated.loc[assets_updated['asset_id'] == 'AST-TEST', 'base_price'].iloc[0]
        self.assertEqual(val, 9500000.0)

        # 5. Delete
        del_success, del_msg = dh.delete_asset_from_db('AST-TEST')
        self.assertTrue(del_success)
        assets_final = dh.load_assets_data()
        self.assertNotIn('AST-TEST', assets_final['asset_id'].values)

    def test_partner_crud_lifecycle(self):
        """Uji siklus hidup data mitra: Create, Read, Update, Delete."""
        new_partner = {
            'partner_id': 'PTN-TEST',
            'partner_name': 'Mitra Uji Coba',
            'req_type': 'Truck',
            'budget': 3500000.0,
            'reliability_score': 0.88
        }
        # 1. Create
        success, msg = dh.save_partner_to_db(new_partner)
        self.assertTrue(success)

        # 2. Read
        partners = dh.load_partners_data()
        self.assertIn('PTN-TEST', partners['partner_id'].values)

        # 3. Duplicate ID prevention
        dup_success, dup_msg = dh.save_partner_to_db(new_partner)
        self.assertFalse(dup_success)

        # 4. Update
        updated_partner = new_partner.copy()
        updated_partner['budget'] = 4000000.0
        upd_success, upd_msg = dh.update_partner_in_db(updated_partner)
        self.assertTrue(upd_success)

        partners_updated = dh.load_partners_data()
        val = partners_updated.loc[partners_updated['partner_id'] == 'PTN-TEST', 'budget'].iloc[0]
        self.assertEqual(val, 4000000.0)

        # 5. Delete
        del_success, del_msg = dh.delete_partner_from_db('PTN-TEST')
        self.assertTrue(del_success)
        partners_final = dh.load_partners_data()
        self.assertNotIn('PTN-TEST', partners_final['partner_id'].values)

    def test_audit_logging(self):
        """Uji pencatatan riwayat aktivitas ke tabel audit_logs."""
        dh.log_activity("TEST_ACTION", "Testing log activity")
        logs = dh.load_audit_logs()
        self.assertFalse(logs.empty)
        first_log = logs.iloc[0]
        self.assertEqual(first_log['Aksi'], 'TEST_ACTION')
        self.assertEqual(first_log['Keterangan'], 'Testing log activity')

    def test_import_assets_csv_and_upsert(self):
        """Uji impor massal data aset dari CSV dengan logika upsert."""
        dh.init_db()
        # Initial: AST-001 ada
        csv_file = os.path.join(self.temp_dir.name, "assets_test.csv")
        data = {
            'Asset ID': ['AST-001', 'AST-999'],
            'Asset Type': ['Warehouse', 'Cold Storage'],
            'Capacity Tons': [2500, 800],
            'Base Price': [20000000, 9000000],
            'Location Score': [0.95, 0.88],
            'Demand Index': [1.3, 1.1]
        }
        pd.DataFrame(data).to_csv(csv_file, index=False)

        success, msg, new_c, upd_c, err_c = dh.import_assets_from_file(csv_file)
        self.assertTrue(success)
        self.assertEqual(new_c, 1)
        self.assertEqual(upd_c, 1)
        self.assertEqual(err_c, 0)

        assets = dh.load_assets_data()
        ast001 = assets[assets['asset_id'] == 'AST-001'].iloc[0]
        self.assertEqual(ast001['base_price'], 20000000.0)
        self.assertIn('AST-999', assets['asset_id'].values)

    def test_import_assets_xlsx(self):
        """Uji impor massal data aset dari Excel (.xlsx)."""
        dh.init_db()
        xlsx_file = os.path.join(self.temp_dir.name, "assets_test.xlsx")
        data = {
            'asset_id': ['AST-EXCEL-1'],
            'asset_type': ['Truck'],
            'capacity_tons': [15.0],
            'base_price': [4500000.0],
            'location_score': [0.82],
            'demand_index': [1.05]
        }
        pd.DataFrame(data).to_excel(xlsx_file, index=False, engine='openpyxl')

        success, msg, new_c, upd_c, err_c = dh.import_assets_from_file(xlsx_file)
        self.assertTrue(success)
        self.assertEqual(new_c, 1)
        assets = dh.load_assets_data()
        self.assertIn('AST-EXCEL-1', assets['asset_id'].values)

    def test_import_assets_validation_errors(self):
        """Uji penanganan berbagai kondisi error pada import aset."""
        # 1. File tidak ada
        success, msg, _, _, _ = dh.import_assets_from_file("non_existent_file.csv")
        self.assertFalse(success)
        self.assertIn("tidak ditemukan", msg)

        # 2. Format salah (.txt)
        txt_file = os.path.join(self.temp_dir.name, "invalid.txt")
        with open(txt_file, "w") as f:
            f.write("hello")
        success, msg, _, _, _ = dh.import_assets_from_file(txt_file)
        self.assertFalse(success)
        self.assertIn("tidak didukung", msg)

        # 3. File kosong
        empty_csv = os.path.join(self.temp_dir.name, "empty.csv")
        pd.DataFrame().to_csv(empty_csv, index=False)
        success, msg, _, _, _ = dh.import_assets_from_file(empty_csv)
        self.assertFalse(success)

        # 4. Kolom wajib hilang
        bad_col_csv = os.path.join(self.temp_dir.name, "bad_col.csv")
        pd.DataFrame({'asset_id': ['AST-1'], 'random_col': [123]}).to_csv(bad_col_csv, index=False)
        success, msg, _, _, _ = dh.import_assets_from_file(bad_col_csv)
        self.assertFalse(success)
        self.assertIn("Kolom wajib tidak lengkap", msg)

    def test_import_partners_csv_and_upsert(self):
        """Uji impor massal data mitra dari CSV dengan logika upsert."""
        dh.init_db()
        csv_file = os.path.join(self.temp_dir.name, "partners_test.csv")
        data = {
            'Partner ID': ['PTN-101', 'PTN-999'],
            'Partner Name': ['PT Logistik Cepat Baru', 'PT Mitra Perkasa'],
            'Req Type': ['Warehouse', 'Truck'],
            'Budget': [25000000, 6000000],
            'Reliability Score': [0.98, 0.85]
        }
        pd.DataFrame(data).to_csv(csv_file, index=False)

        success, msg, new_c, upd_c, err_c = dh.import_partners_from_file(csv_file)
        self.assertTrue(success)
        self.assertEqual(new_c, 1)
        self.assertEqual(upd_c, 1)

        partners = dh.load_partners_data()
        ptn101 = partners[partners['partner_id'] == 'PTN-101'].iloc[0]
        self.assertEqual(ptn101['partner_name'], 'PT Logistik Cepat Baru')
        self.assertEqual(ptn101['budget'], 25000000.0)
        self.assertIn('PTN-999', partners['partner_id'].values)

    def test_import_partners_xlsx(self):
        """Uji impor massal data mitra dari Excel (.xlsx)."""
        dh.init_db()
        xlsx_file = os.path.join(self.temp_dir.name, "partners_test.xlsx")
        data = {
            'partner_id': ['PTN-EXCEL-1'],
            'partner_name': ['PT Excel Express'],
            'req_type': ['Fleet'],
            'budget': [8000000.0],
            'reliability_score': [0.91]
        }
        pd.DataFrame(data).to_excel(xlsx_file, index=False, engine='openpyxl')

        success, msg, new_c, upd_c, err_c = dh.import_partners_from_file(xlsx_file)
        self.assertTrue(success)
        self.assertEqual(new_c, 1)
        partners = dh.load_partners_data()
        self.assertIn('PTN-EXCEL-1', partners['partner_id'].values)

    def test_import_partners_validation_errors(self):
        """Uji penanganan berbagai kondisi error pada import mitra."""
        # 1. File tidak ada
        success, msg, _, _, _ = dh.import_partners_from_file("non_existent_partners.csv")
        self.assertFalse(success)

        # 2. Kolom hilang
        bad_csv = os.path.join(self.temp_dir.name, "bad_partners.csv")
        pd.DataFrame({'partner_id': ['PTN-1']}).to_csv(bad_csv, index=False)
        success, msg, _, _, _ = dh.import_partners_from_file(bad_csv)
        self.assertFalse(success)
        self.assertIn("Kolom wajib tidak lengkap", msg)

if __name__ == '__main__':
    unittest.main()

