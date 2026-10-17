import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Pastikan platform GUI diset ke offscreen agar dapat berjalan di lingkungan headless/CI
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
import src.data_handler as dh
from main_gui import LogisticsApp, AlgorithmSettingsDialog

class TestLogisticsAppGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Inisialisasi QApplication sekali untuk seluruh test suite
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        # Gunakan database terisolasi untuk pengujian GUI
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.temp_dir.name, "gui_test_logistics.db")
        self.original_db_file = dh.DB_FILE
        dh.DB_FILE = self.test_db_path
        dh.init_db()

        self.window = LogisticsApp()

    def tearDown(self):
        self.window.close()
        dh.DB_FILE = self.original_db_file
        self.temp_dir.cleanup()

    @patch('main_gui.QMessageBox.information')
    def test_load_data_workflow(self, mock_info):
        """Uji alur pemuatan data aset dan mitra ke dalam tabel."""
        self.window.load_data()
        self.assertIsNotNone(self.window.assets_df)
        self.assertIsNotNone(self.window.partners_df)
        self.assertGreater(self.window.tab_assets.rowCount(), 0)
        self.assertGreater(self.window.tab_partners.rowCount(), 0)
        self.assertTrue(self.window.btn_optimize.isEnabled())
        self.assertTrue(self.window.btn_add_asset.isEnabled())

    @patch('main_gui.QMessageBox.information')
    def test_search_filter(self, mock_info):
        """Uji fitur pencarian / filter pada tabel aset dan mitra."""
        self.window.load_data()
        
        # Cari tipe 'Truck'
        self.window.search_assets.setText("Truck")
        self.assertEqual(self.window.tab_assets.rowCount(), 1)
        
        # Reset pencarian
        self.window.search_assets.setText("")
        self.assertEqual(self.window.tab_assets.rowCount(), len(self.window.assets_df))

        # Filter mitra
        self.window.search_partners.setText("Logistik Cepat")
        self.assertEqual(self.window.tab_partners.rowCount(), 1)

    @patch('main_gui.QMessageBox.information')
    def test_pricing_and_matching_workflow(self, mock_info):
        """Uji eksekusi Dynamic Pricing, Partner Matching, dan Slider What-If Analysis."""
        self.window.load_data()
        
        # 1. Jalankan Dynamic Pricing
        self.window.optimize_pricing()
        self.assertIsNotNone(self.window.optimized_df)
        self.assertEqual(self.window.tab_pricing.rowCount(), len(self.window.assets_df))
        self.assertTrue(self.window.btn_match.isEnabled())
        self.assertTrue(self.window.slider_margin.isEnabled())

        # 2. Jalankan Partner Matching
        self.window.match_partners()
        self.assertIsNotNone(self.window.matching_df)
        self.assertGreater(self.window.tab_matches.rowCount(), 0)
        self.assertTrue(self.window.btn_export.isEnabled())

        # 3. Ubah Slider Margin Profit (What-If Analysis)
        self.window.slider_margin.setValue(25)
        self.assertIn("25%", self.window.lbl_slider_val.text())
        # Pastikan tabel harga dan rekomendasi mitra terhitung ulang secara reaktif
        self.assertIsNotNone(self.window.optimized_df)

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getSaveFileName')
    def test_export_report_excel(self, mock_file_dialog, mock_info):
        """Uji ekspor laporan hasil optimasi ke file Excel (.xlsx)."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()

        export_path = os.path.join(self.temp_dir.name, "test_report.xlsx")
        mock_file_dialog.return_value = (export_path, "Excel Files (*.xlsx)")

        self.window.export_report()
        self.assertTrue(os.path.exists(export_path))

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getSaveFileName')
    def test_export_report_csv(self, mock_file_dialog, mock_info):
        """Uji ekspor laporan rekomendasi ke file CSV (.csv)."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()

        export_path = os.path.join(self.temp_dir.name, "test_report.csv")
        mock_file_dialog.return_value = (export_path, "CSV Files (*.csv)")

        self.window.export_report()
        self.assertTrue(os.path.exists(export_path))

    @patch('main_gui.QMessageBox.warning')
    def test_empty_selection_guard(self, mock_warn):
        """Uji perlindungan saat tombol edit/hapus ditekan tanpa memilih baris tabel."""
        self.window.tab_assets.setCurrentCell(-1, -1)
        self.window.open_edit_asset_form()
        mock_warn.assert_called()

        mock_warn.reset_mock()
        self.window.tab_partners.setCurrentCell(-1, -1)
        self.window.open_edit_partner_form()
        mock_warn.assert_called()

    @patch('main_gui.QMessageBox.information')
    def test_table_cells_non_editable(self, mock_info):
        """Pastikan sel-sel tabel read-only dan tidak memiliki flag Qt.ItemIsEditable."""
        from PyQt5.QtCore import Qt
        self.window.load_data()
        item = self.window.tab_assets.item(0, 0)
        self.assertIsNotNone(item)
        self.assertEqual(int(item.flags() & Qt.ItemIsEditable), 0)

    @patch('main_gui.QMessageBox.information')
    def test_state_reset_on_reload(self, mock_info):
        """Uji apakah memuat ulang data (load_data) mereset hasil kalkulasi sebelumnya."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()
        self.assertIsNotNone(self.window.optimized_df)
        self.assertIsNotNone(self.window.matching_df)

        # Klik load_data lagi
        self.window.load_data()
        self.assertIsNone(self.window.optimized_df)
        self.assertIsNone(self.window.matching_df)
        self.assertEqual(self.window.tab_pricing.rowCount(), 0)
        self.assertEqual(self.window.tab_matches.rowCount(), 0)

    def test_audit_logs_populated_on_startup(self):
        """Pastikan tab log audit langsung terinisialisasi dan tersinkronisasi saat aplikasi dibuka."""
        self.assertIsNotNone(self.window.logs_df)
        self.assertEqual(self.window.tab_logs.rowCount(), len(self.window.logs_df))

    @patch('main_gui.QMessageBox.warning')
    def test_empty_data_guards(self, mock_warn):
        """Uji pesan peringatan jika tombol optimasi / matching ditekan saat data kosong."""
        # Belum load data, self.assets_df masih None
        self.window.optimize_pricing()
        mock_warn.assert_called()

        mock_warn.reset_mock()
        self.window.match_partners()
        mock_warn.assert_called()

    @patch('main_gui.QMessageBox.information')
    def test_kpi_dashboard_updates(self, mock_info):
        """Uji apakah kartu KPI Dashboard memperbarui metrik secara reaktif."""
        # 1. State awal
        self.assertIn("Rp 0", self.window.lbl_kpi_rev_val.text())
        self.assertIn("0.0%", self.window.lbl_kpi_uplift_val.text())

        # 2. Setelah Load Data
        self.window.load_data()
        self.assertIn("Rp 27.500.000", self.window.lbl_kpi_rev_val.text())

        # 3. Setelah Dynamic Pricing
        self.window.optimize_pricing()
        self.assertIn("Rp 34.843.000", self.window.lbl_kpi_rev_val.text())
        self.assertIn("%", self.window.lbl_kpi_uplift_val.text())
        self.assertTrue(self.window.lbl_kpi_uplift_val.text().startswith("+"))

        # 4. Setelah Match Partners
        self.window.match_partners()
        self.assertIn("3 / 3", self.window.lbl_kpi_match_val.text())
        self.assertIn("92.8%", self.window.lbl_kpi_quality_val.text())

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getOpenFileName')
    def test_import_assets_gui_action(self, mock_dialog, mock_info):
        """Uji fungsionalitas tombol Import Aset pada antarmuka GUI."""
        csv_file = os.path.join(self.temp_dir.name, "gui_import_assets.csv")
        data = {
            'asset_id': ['AST-GUI-1', 'AST-GUI-2'],
            'asset_type': ['Truck', 'Van'],
            'capacity_tons': [10.0, 3.5],
            'base_price': [5000000.0, 2000000.0],
            'location_score': [0.8, 0.9],
            'demand_index': [1.1, 1.2]
        }
        pd.DataFrame(data).to_csv(csv_file, index=False)
        mock_dialog.return_value = (csv_file, "Spreadsheet Files (*.xlsx *.xls *.csv)")

        self.window.import_assets_action()
        self.assertIsNotNone(self.window.assets_df)
        self.assertIn('AST-GUI-1', self.window.assets_df['asset_id'].values)
        self.assertEqual(self.window.tabs.currentIndex(), 0)
        mock_info.assert_called()

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getOpenFileName')
    def test_import_partners_gui_action(self, mock_dialog, mock_info):
        """Uji fungsionalitas tombol Import Mitra pada antarmuka GUI."""
        csv_file = os.path.join(self.temp_dir.name, "gui_import_partners.csv")
        data = {
            'partner_id': ['PTN-GUI-1'],
            'partner_name': ['Mitra GUI Testing'],
            'req_type': ['Truck'],
            'budget': [7000000.0],
            'reliability_score': [0.9]
        }
        pd.DataFrame(data).to_csv(csv_file, index=False)
        mock_dialog.return_value = (csv_file, "Spreadsheet Files (*.xlsx *.xls *.csv)")

        self.window.import_partners_action()
        self.assertIsNotNone(self.window.partners_df)
        self.assertIn('PTN-GUI-1', self.window.partners_df['partner_id'].values)
        self.assertEqual(self.window.tabs.currentIndex(), 1)
        mock_info.assert_called()

    @patch('main_gui.QMessageBox.warning')
    @patch('main_gui.QFileDialog.getOpenFileName')
    def test_import_dialog_canceled_or_failed(self, mock_dialog, mock_warn):
        """Uji penanganan saat dialog file dibatalkan atau file tidak valid."""
        # 1. User membatalkan dialog (path kosong)
        mock_dialog.return_value = ("", "")
        self.window.import_assets_action()
        mock_warn.assert_not_called()

        # 2. File tidak valid
        mock_dialog.return_value = ("file_tidak_ada.csv", "Spreadsheet Files (*.xlsx *.xls *.csv)")
        self.window.import_assets_action()
        mock_warn.assert_called()

    def test_algorithm_settings_dialog_sync_and_defaults(self):
        """Uji fungsionalitas AlgorithmSettingsDialog (auto-sync slider, reset, get_config)."""
        dialog = AlgorithmSettingsDialog(weight_budget=0.7, weight_reliability=0.3, min_score_threshold=50.0)
        self.assertEqual(dialog.slider_budget.value(), 70)
        self.assertEqual(dialog.slider_reliability.value(), 30)
        self.assertEqual(dialog.slider_threshold.value(), 50)

        # Ubah slider budget -> slider reliability harus tersinkronisasi otomatis (total 100%)
        dialog.slider_budget.setValue(80)
        self.assertEqual(dialog.slider_reliability.value(), 20)
        self.assertEqual(dialog.spin_reliability.value(), 20)

        cfg = dialog.get_config()
        self.assertAlmostEqual(cfg['weight_budget'], 0.8)
        self.assertAlmostEqual(cfg['weight_reliability'], 0.2)
        self.assertEqual(cfg['min_score_threshold'], 50.0)

        # Uji reset ke default
        dialog.reset_defaults()
        self.assertEqual(dialog.slider_budget.value(), 70)
        self.assertEqual(dialog.slider_reliability.value(), 30)
        self.assertEqual(dialog.slider_threshold.value(), 50)
        dialog.close()

    @patch('main_gui.QMessageBox.information')
    @patch.object(AlgorithmSettingsDialog, 'exec_', return_value=QDialog.Accepted)
    def test_algorithm_settings_gui_workflow(self, mock_exec, mock_info):
        """Uji dialog pengaturan bobot algoritma dan penerapannya ke aplikasi."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()

        # Simulasikan membuka dialog dan mengubah bobot
        with patch.object(AlgorithmSettingsDialog, 'get_config', return_value={
            'weight_budget': 0.5,
            'weight_reliability': 0.5,
            'min_score_threshold': 70.0
        }):
            self.window.open_algorithm_settings()

        self.assertEqual(self.window.weight_budget, 0.5)
        self.assertEqual(self.window.weight_reliability, 0.5)
        self.assertEqual(self.window.min_score_threshold, 70.0)
        self.assertEqual(self.window.slider_quick_thresh.value(), 70)
        self.assertIn("Anggaran 50%", self.window.lbl_matching_config.text())
        self.assertIn("Reliabilitas 50%", self.window.lbl_matching_config.text())
        mock_info.assert_called()

    @patch('main_gui.QMessageBox.information')
    def test_quick_threshold_slider_reactive(self, mock_info):
        """Uji slider ambang batas cepat (quick threshold) pada tab rekomendasi secara reaktif."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()
        initial_count = self.window.tab_matches.rowCount()
        self.assertGreater(initial_count, 0)

        # Naikkan threshold ke batas tinggi (>98%) sehingga hasil rekomendasi tersaring ketat
        self.window.slider_quick_thresh.setValue(98)
        self.assertEqual(self.window.min_score_threshold, 98.0)
        self.assertIn(">98%", self.window.lbl_quick_thresh_val.text())
        self.assertLessEqual(self.window.tab_matches.rowCount(), initial_count)

        # Turunkan kembali ke 0% sehingga semua calon mitra yang cocok tipe asetnya lolos
        self.window.slider_quick_thresh.setValue(0)
        self.assertEqual(self.window.min_score_threshold, 0.0)
        self.assertGreaterEqual(self.window.tab_matches.rowCount(), initial_count)

    @patch('main_gui.QMessageBox.information')
    def test_search_matches_filter(self, mock_info):
        """Uji filter pencarian pada tab Rekomendasi Mitra."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()
        total_rows = self.window.tab_matches.rowCount()
        self.assertGreater(total_rows, 1)

        # Filter berdasarkan ID aset 'AST-001'
        self.window.search_matches.setText("AST-001")
        self.assertGreater(self.window.tab_matches.rowCount(), 0)
        self.assertLessEqual(self.window.tab_matches.rowCount(), total_rows)

        # Reset pencarian
        self.window.search_matches.setText("")
        self.assertEqual(self.window.tab_matches.rowCount(), total_rows)

    @patch('main_gui.QMessageBox.information')
    def test_operational_cost_slider_workflow(self, mock_info):
        """Uji slider simulasi biaya operasional dan pembaruan KPI laba bersih."""
        self.window.load_data()
        self.window.optimize_pricing()
        
        # Default cost_ratio adalah 0.35 (35%)
        self.assertEqual(self.window.cost_ratio, 0.35)
        self.assertIn("35%", self.window.lbl_cost_slider_val.text())
        self.assertIn("65.0%", self.window.lbl_kpi_net_val.text())

        # Ubah slider biaya operasional ke 45%
        self.window.slider_cost.setValue(45)
        self.assertEqual(self.window.cost_ratio, 0.45)
        self.assertIn("45%", self.window.lbl_cost_slider_val.text())
        self.assertIn("55.0%", self.window.lbl_kpi_net_val.text())

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getSaveFileName')
    def test_export_excel_financial_summary_sheet(self, mock_file_dialog, mock_info):
        """Uji apakah ekspor Excel menghasilkan sheet Ringkasan_Finansial dengan rincian biaya dan laba bersih."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.match_partners()

        export_path = os.path.join(self.temp_dir.name, "excel_with_financial_summary.xlsx")
        mock_file_dialog.return_value = (export_path, "Excel Files (*.xlsx)")

        self.window.export_report()
        self.assertTrue(os.path.exists(export_path))

        # Baca kembali menggunakan openpyxl / pandas untuk memastikan sheet Ringkasan_Finansial tersedia
        with pd.ExcelFile(export_path) as xl:
            self.assertIn('Ringkasan_Finansial', xl.sheet_names)
            self.assertIn('Rekomendasi_Mitra', xl.sheet_names)
            self.assertIn('Harga_Optimal', xl.sheet_names)

        df_summary = pd.read_excel(export_path, sheet_name='Ringkasan_Finansial')
        self.assertIn('Metrik', df_summary.columns)
        self.assertIn('Nilai', df_summary.columns)

    @patch('main_gui.QMessageBox.information')
    def test_exclusive_assignment_gui_workflow(self, mock_info):
        """Uji alur kerja GUI untuk Alokasi Eksklusif 1-ke-1 (Hungarian Bipartite Matching)."""
        self.window.load_data()
        self.window.optimize_pricing()

        self.assertTrue(self.window.btn_assign.isEnabled())
        
        # Eksekusi alokasi eksklusif
        self.window.run_exclusive_assignment()
        self.assertIsNotNone(self.window.assignment_df)
        self.assertGreater(self.window.tab_assignment.rowCount(), 0)
        self.assertIn("Aset Teralokasi:", self.window.lbl_strip_ratio.text())
        self.assertTrue(self.window.btn_export.isEnabled())

        # Uji filter pencarian pada tab alokasi
        self.window.search_assignment.setText("Warehouse")
        self.assertGreaterEqual(self.window.tab_assignment.rowCount(), 1)
        self.window.search_assignment.setText("")
        self.assertEqual(self.window.tab_assignment.rowCount(), len(self.window.assignment_df))

    @patch('main_gui.QMessageBox.information')
    @patch('main_gui.QFileDialog.getSaveFileName')
    def test_export_excel_with_exclusive_assignment_sheet(self, mock_file_dialog, mock_info):
        """Uji ekspor Excel menyertakan sheet Alokasi_Eksklusif saat alokasi dijalankan."""
        self.window.load_data()
        self.window.optimize_pricing()
        self.window.run_exclusive_assignment()

        export_path = os.path.join(self.temp_dir.name, "excel_with_assignment.xlsx")
        mock_file_dialog.return_value = (export_path, "Excel Files (*.xlsx)")

        self.window.export_report()
        self.assertTrue(os.path.exists(export_path))

        with pd.ExcelFile(export_path) as xl:
            self.assertIn('Alokasi_Eksklusif', xl.sheet_names)

        df_assign = pd.read_excel(export_path, sheet_name='Alokasi_Eksklusif')
        self.assertIn('asset_id', df_assign.columns)
        self.assertIn('allocation_status', df_assign.columns)

if __name__ == '__main__':
    unittest.main()


