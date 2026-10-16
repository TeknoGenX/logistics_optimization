import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
                             QTabWidget, QHeaderView, QMessageBox, QDialog, QFormLayout, 
                             QLineEdit, QComboBox, QDoubleSpinBox, QFileDialog, QLabel, QSlider, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# Import Matplotlib untuk integrasi GUI PyQt5
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Import modul bisnis 
from src.data_handler import (load_assets_data, load_partners_data, load_audit_logs, log_activity,
                              save_asset_to_db, save_partner_to_db, 
                              delete_asset_from_db, delete_partner_from_db,
                              update_asset_in_db, update_partner_in_db)
from src.pricing_optimizer import PricingOptimizer
from src.partner_matcher import PartnerMatcher

# --- STYLESHEET PUBLIKASI (MODERN CORPORATE THEME) ---
MODERN_STYLE = """
QMainWindow {
    background-color: #f4f6f9;
}
QTabWidget::pane {
    border: 1px solid #dcdcdc;
    background: white;
    border-radius: 6px;
}
QTabBar::tab {
    background: #e4e7eb;
    color: #4a5568;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #007bff;
    color: white;
}
QTabBar::tab:hover {
    background: #cbd5e0;
}
QTableWidget {
    background-color: white;
    alternate-background-color: #f8fafc;
    gridline-color: #e2e8f0;
    selection-background-color: #bee3f8;
    selection-color: #1a202c;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    font-size: 13px;
}
QHeaderView::section {
    background-color: #2d3748;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
    color: #2d3748;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #edf2f7;
    border-color: #a0aec0;
}
QPushButton:pressed {
    background-color: #e2e8f0;
}
QLineEdit {
    padding: 8px;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    background: white;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #007bff;
}
QLabel {
    font-size: 13px;
    color: #2d3748;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #cbd5e0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
    color: #2d3748;
}
"""

# --- KELAS DIALOG FORM ---
class AddAssetDialog(QDialog):
    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.is_edit = edit_data is not None
        self.setWindowTitle("Edit Aset" if self.is_edit else "Tambah Aset Baru")
        self.resize(350, 280)
        
        layout = QFormLayout(self)
        
        self.id_input = QLineEdit()
        if self.is_edit:
            self.id_input.setText(str(edit_data.get('asset_id', '')))
            self.id_input.setReadOnly(True)
            self.id_input.setStyleSheet("background-color: #e9ecef; color: #6c757d;")
            
        self.type_input = QComboBox()
        self.type_input.addItems(['Warehouse', 'Truck', 'Cold Storage'])
        if self.is_edit:
            self.type_input.setCurrentText(str(edit_data.get('asset_type', 'Warehouse')))
        
        self.capacity_input = QDoubleSpinBox()
        self.capacity_input.setMinimum(0.1)
        self.capacity_input.setMaximum(10000)
        self.capacity_input.setValue(10.0)
        if self.is_edit:
            self.capacity_input.setValue(float(edit_data.get('capacity_tons', 10.0)))
            
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(1000)
        self.price_input.setMaximum(100000000)
        self.price_input.setSingleStep(1000000)
        self.price_input.setValue(1000000)
        if self.is_edit:
            self.price_input.setValue(float(edit_data.get('base_price', 1000000)))
            
        self.location_input = QDoubleSpinBox()
        self.location_input.setMinimum(0.01)
        self.location_input.setMaximum(1.0)
        self.location_input.setSingleStep(0.1)
        self.location_input.setValue(0.8)
        if self.is_edit:
            self.location_input.setValue(float(edit_data.get('location_score', 0.8)))
            
        self.demand_input = QDoubleSpinBox()
        self.demand_input.setMinimum(0.1)
        self.demand_input.setMaximum(2.0)
        self.demand_input.setSingleStep(0.1)
        self.demand_input.setValue(1.0)
        if self.is_edit:
            self.demand_input.setValue(float(edit_data.get('demand_index', 1.0)))
        
        layout.addRow("Asset ID:", self.id_input)
        layout.addRow("Tipe Aset:", self.type_input)
        layout.addRow("Kapasitas (Ton):", self.capacity_input)
        layout.addRow("Harga Dasar (Rp):", self.price_input)
        layout.addRow("Skor Lokasi (0-1.0):", self.location_input)
        layout.addRow("Indeks Demand:", self.demand_input)
        
        self.btn_save = QPushButton("Simpan Perubahan" if self.is_edit else "Simpan Aset")
        self.btn_save.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 10px;")
        self.btn_save.clicked.connect(self.accept)
        layout.addRow(self.btn_save)

    def get_data(self):
        return {
            'asset_id': self.id_input.text(),
            'asset_type': self.type_input.currentText(),
            'capacity_tons': self.capacity_input.value(),
            'base_price': self.price_input.value(),
            'location_score': self.location_input.value(),
            'demand_index': self.demand_input.value()
        }

class AddPartnerDialog(QDialog):
    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.is_edit = edit_data is not None
        self.setWindowTitle("Edit Mitra" if self.is_edit else "Tambah Mitra Baru")
        self.resize(350, 230)
        
        layout = QFormLayout(self)
        
        self.id_input = QLineEdit()
        if self.is_edit:
            self.id_input.setText(str(edit_data.get('partner_id', '')))
            self.id_input.setReadOnly(True)
            self.id_input.setStyleSheet("background-color: #e9ecef; color: #6c757d;")
            
        self.name_input = QLineEdit()
        if self.is_edit:
            self.name_input.setText(str(edit_data.get('partner_name', '')))
        
        self.req_type_input = QComboBox()
        self.req_type_input.addItems(['Warehouse', 'Truck', 'Cold Storage'])
        if self.is_edit:
            self.req_type_input.setCurrentText(str(edit_data.get('req_type', 'Warehouse')))
        
        self.budget_input = QDoubleSpinBox()
        self.budget_input.setMinimum(1000)
        self.budget_input.setMaximum(100000000)
        self.budget_input.setSingleStep(1000000)
        self.budget_input.setValue(1000000)
        if self.is_edit:
            self.budget_input.setValue(float(edit_data.get('budget', 1000000)))
            
        self.score_input = QDoubleSpinBox()
        self.score_input.setMinimum(0.01)
        self.score_input.setMaximum(1.0)
        self.score_input.setSingleStep(0.1)
        self.score_input.setValue(0.8)
        if self.is_edit:
            self.score_input.setValue(float(edit_data.get('reliability_score', 0.8)))
        
        layout.addRow("Partner ID:", self.id_input)
        layout.addRow("Nama Mitra:", self.name_input)
        layout.addRow("Kebutuhan Aset:", self.req_type_input)
        layout.addRow("Budget (Rp):", self.budget_input)
        layout.addRow("Skor Reliabilitas (0-1.0):", self.score_input)
        
        self.btn_save = QPushButton("Simpan Perubahan" if self.is_edit else "Simpan Mitra")
        self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 10px;")
        self.btn_save.clicked.connect(self.accept)
        layout.addRow(self.btn_save)

    def get_data(self):
        return {
            'partner_id': self.id_input.text(),
            'partner_name': self.name_input.text(),
            'req_type': self.req_type_input.currentText(),
            'budget': self.budget_input.value(),
            'reliability_score': self.score_input.value()
        }

# --- WIDGET KANVAS MATPLOTLIB ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor('#ffffff')
        super().__init__(fig)
        self.setParent(parent)

# --- KELAS UTAMA APLIKASI ---
class LogisticsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistem Optimasi Harga & Seleksi Mitra Logistik (Enterprise Edition)")
        self.resize(1200, 780)
        
        self.assets_df = None
        self.partners_df = None
        self.optimized_df = None
        self.matching_df = None
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Header Judul Aplikasi Publikasi
        header_layout = QHBoxLayout()
        title_label = QLabel("🚛 <b>Logistics Intelligence & Decision Support System</b>")
        title_label.setStyleSheet("font-size: 18px; color: #1a202c; font-weight: bold;")
        subtitle_label = QLabel("Dynamic Pricing & Partner Matching Platform")
        subtitle_label.setStyleSheet("font-size: 12px; color: #718096;")
        
        header_vbox = QVBoxLayout()
        header_vbox.addWidget(title_label)
        header_vbox.addWidget(subtitle_label)
        header_layout.addLayout(header_vbox)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Group Box Panel Kontrol Operasional
        control_group = QGroupBox("Panel Kontrol & Eksekusi Algoritma")
        control_layout = QVBoxLayout(control_group)

        # Baris 1: Tombol CRUD & Load
        btn_layout_1 = QHBoxLayout()
        
        self.btn_load = QPushButton("📁 1. Load Data")
        self.btn_load.clicked.connect(self.load_data)
        self.btn_load.setStyleSheet("background-color: #3182ce; color: white; font-weight: bold;")
        
        self.btn_add_asset = QPushButton("➕ Tambah Aset")
        self.btn_add_asset.clicked.connect(self.open_add_asset_form)
        self.btn_add_asset.setEnabled(False)

        self.btn_edit_asset = QPushButton("✏️ Edit Aset")
        self.btn_edit_asset.clicked.connect(self.open_edit_asset_form)
        self.btn_edit_asset.setEnabled(False)

        self.btn_del_asset = QPushButton("🗑️ Hapus Aset")
        self.btn_del_asset.clicked.connect(self.delete_selected_asset)
        self.btn_del_asset.setEnabled(False)
        self.btn_del_asset.setStyleSheet("color: #e53e3e;")
        
        self.btn_add_partner = QPushButton("➕ Tambah Mitra")
        self.btn_add_partner.clicked.connect(self.open_add_partner_form)
        self.btn_add_partner.setEnabled(False)

        self.btn_edit_partner = QPushButton("✏️ Edit Mitra")
        self.btn_edit_partner.clicked.connect(self.open_edit_partner_form)
        self.btn_edit_partner.setEnabled(False)

        self.btn_del_partner = QPushButton("🗑️ Hapus Mitra")
        self.btn_del_partner.clicked.connect(self.delete_selected_partner)
        self.btn_del_partner.setEnabled(False)
        self.btn_del_partner.setStyleSheet("color: #e53e3e;")
        
        btn_layout_1.addWidget(self.btn_load)
        btn_layout_1.addWidget(self.btn_add_asset)
        btn_layout_1.addWidget(self.btn_edit_asset)
        btn_layout_1.addWidget(self.btn_del_asset)
        btn_layout_1.addWidget(self.btn_add_partner)
        btn_layout_1.addWidget(self.btn_edit_partner)
        btn_layout_1.addWidget(self.btn_del_partner)
        control_layout.addLayout(btn_layout_1)

        # Baris 2: Proses & Ekspor
        btn_layout_2 = QHBoxLayout()
        
        self.btn_optimize = QPushButton("⚡ 2. Hitung Dynamic Pricing")
        self.btn_optimize.clicked.connect(self.optimize_pricing)
        self.btn_optimize.setEnabled(False)
        self.btn_optimize.setStyleSheet("background-color: #319795; color: white; font-weight: bold;")
        
        self.btn_match = QPushButton("🤖 3. Jalankan Partner Matching")
        self.btn_match.clicked.connect(self.match_partners)
        self.btn_match.setEnabled(False)
        self.btn_match.setStyleSheet("background-color: #d69e2e; color: white; font-weight: bold;")
        
        self.btn_export = QPushButton("💾 Export Laporan Excel/CSV")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold;")
        
        btn_layout_2.addWidget(self.btn_optimize)
        btn_layout_2.addWidget(self.btn_match)
        btn_layout_2.addWidget(self.btn_export)
        control_layout.addLayout(btn_layout_2)

        # Baris 3: Slider What-If Analysis
        slider_layout = QHBoxLayout()
        self.lbl_slider_title = QLabel("<b>Simulasi Margin Profit (What-If Analysis):</b>")
        self.slider_margin = QSlider(Qt.Horizontal)
        self.slider_margin.setRange(0, 50)
        self.slider_margin.setValue(10)
        self.slider_margin.setEnabled(False)
        self.slider_margin.valueChanged.connect(self.on_slider_changed)
        
        self.lbl_slider_val = QLabel("10%")
        self.lbl_slider_val.setStyleSheet("font-weight: bold; color: #3182ce; font-size: 14px;")
        
        slider_layout.addWidget(self.lbl_slider_title)
        slider_layout.addWidget(self.slider_margin)
        slider_layout.addWidget(self.lbl_slider_val)
        control_layout.addLayout(slider_layout)

        main_layout.addWidget(control_group)

        # Tabs Tabel, Grafik, & Log Audit
        self.tabs = QTabWidget()
        
        # Tab Aset
        self.widget_assets = QWidget()
        layout_assets = QVBoxLayout(self.widget_assets)
        self.search_assets = QLineEdit()
        self.search_assets.setPlaceholderText("🔍 Cari data aset berdasarkan ID atau Tipe...")
        self.search_assets.textChanged.connect(lambda: self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text()))
        self.tab_assets = QTableWidget()
        layout_assets.addWidget(self.search_assets)
        layout_assets.addWidget(self.tab_assets)

        # Tab Mitra
        self.widget_partners = QWidget()
        layout_partners = QVBoxLayout(self.widget_partners)
        self.search_partners = QLineEdit()
        self.search_partners.setPlaceholderText("🔍 Cari data mitra berdasarkan Nama atau ID...")
        self.search_partners.textChanged.connect(lambda: self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text()))
        self.tab_partners = QTableWidget()
        layout_partners.addWidget(self.search_partners)
        layout_partners.addWidget(self.tab_partners)

        self.tab_pricing = QTableWidget()
        self.tab_matches = QTableWidget()
        
        # Tab Log Audit
        self.widget_logs = QWidget()
        layout_logs = QVBoxLayout(self.widget_logs)
        self.search_logs = QLineEdit()
        self.search_logs.setPlaceholderText("🔍 Cari riwayat log audit...")
        self.search_logs.textChanged.connect(lambda: self.filter_table(self.tab_logs, load_audit_logs(), self.search_logs.text()))
        self.tab_logs = QTableWidget()
        layout_logs.addWidget(self.search_logs)
        layout_logs.addWidget(self.tab_logs)
        
        self.tab_charts = QWidget()
        self.init_charts_tab()
        
        for t in [self.tab_assets, self.tab_partners, self.tab_pricing, self.tab_matches, self.tab_logs]:
            t.setSelectionBehavior(QTableWidget.SelectRows)
            t.setSelectionMode(QTableWidget.SingleSelection)

        self.tabs.addTab(self.widget_assets, "📦 Data Aset")
        self.tabs.addTab(self.widget_partners, "🤝 Data Mitra")
        self.tabs.addTab(self.tab_pricing, "💰 Hasil Optimasi Harga")
        self.tabs.addTab(self.tab_matches, "⭐ Rekomendasi Mitra")
        self.tabs.addTab(self.tab_charts, "📊 Grafik Analitik")
        self.tabs.addTab(self.widget_logs, "📜 Log Audit Sistem")
        
        main_layout.addWidget(self.tabs)

    def init_charts_tab(self):
        chart_layout = QHBoxLayout(self.tab_charts)
        self.canvas_pricing = MplCanvas(self, width=5, height=4, dpi=100)
        chart_layout.addWidget(self.canvas_pricing)
        self.canvas_partners = MplCanvas(self, width=5, height=4, dpi=100)
        chart_layout.addWidget(self.canvas_partners)

    def clear_table(self, table_widget):
        table_widget.clear()
        table_widget.setRowCount(0)
        table_widget.setColumnCount(0)

    def reset_optimization_state(self):
        self.optimized_df = None
        self.matching_df = None
        self.btn_match.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.slider_margin.setEnabled(False)
        self.clear_table(self.tab_pricing)
        self.clear_table(self.tab_matches)
        self.update_charts()

    def reset_matching_state(self):
        self.matching_df = None
        self.btn_export.setEnabled(False)
        self.clear_table(self.tab_matches)
        self.update_charts()

    def update_charts(self):
        self.canvas_pricing.axes.clear()
        if self.optimized_df is not None and not self.optimized_df.empty:
            x = self.optimized_df['asset_id']
            base = self.optimized_df['base_price'] / 1e6
            optimal = self.optimized_df['optimal_price'] / 1e6
            
            width = 0.35
            ind = range(len(x))
            
            self.canvas_pricing.axes.bar([i - width/2 for i in ind], base, width, label='Harga Dasar (Juta)', color='#a0aec0')
            self.canvas_pricing.axes.bar([i + width/2 for i in ind], optimal, width, label='Harga Optimal (Juta)', color='#3182ce')
            
            self.canvas_pricing.axes.set_title('Perbandingan Harga Dasar vs Harga Optimal Aset', fontsize=11, fontweight='bold', color='#2d3748')
            self.canvas_pricing.axes.set_xlabel('Asset ID', fontsize=9, color='#4a5568')
            self.canvas_pricing.axes.set_ylabel('Harga (Juta IDR)', fontsize=9, color='#4a5568')
            self.canvas_pricing.axes.set_xticks(ind)
            self.canvas_pricing.axes.set_xticklabels(x)
            self.canvas_pricing.axes.legend()
            self.canvas_pricing.axes.grid(axis='y', linestyle='--', alpha=0.5)
        self.canvas_pricing.draw()

        self.canvas_partners.axes.clear()
        if self.partners_df is not None and not self.partners_df.empty:
            names = self.partners_df['partner_name']
            budgets = self.partners_df['budget'] / 1e6
            
            y_pos = range(len(names))
            self.canvas_partners.axes.barh(y_pos, budgets, color='#38a169')
            
            self.canvas_partners.axes.set_title('Distribusi Budget Calon Mitra', fontsize=11, fontweight='bold', color='#2d3748')
            self.canvas_partners.axes.set_xlabel('Budget (Juta IDR)', fontsize=9, color='#4a5568')
            self.canvas_partners.axes.set_yticks(y_pos)
            self.canvas_partners.axes.set_yticklabels(names)
            self.canvas_partners.axes.invert_yaxis()
            self.canvas_partners.axes.grid(axis='x', linestyle='--', alpha=0.5)
        self.canvas_partners.draw()

    def refresh_audit_logs(self):
        logs_df = load_audit_logs()
        self.filter_table(self.tab_logs, logs_df, self.search_logs.text())

    def filter_table(self, table_widget, original_df, keyword):
        if original_df is None:
            self.clear_table(table_widget)
            return

        if original_df.empty or not keyword.strip():
            self.populate_table(table_widget, original_df)
            return
            
        mask = original_df.astype(str).apply(
            lambda col: col.str.contains(keyword, case=False, na=False, regex=False)
        ).any(axis=1)
        filtered_df = original_df[mask]
        self.populate_table(table_widget, filtered_df)

    def load_data(self):
        self.assets_df = load_assets_data()
        self.partners_df = load_partners_data()
        
        self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
        self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
        
        log_activity("LOAD DATA", "Memuat data aset dan mitra dari database SQLite.")
        self.refresh_audit_logs()
        self.update_charts()
        
        self.btn_optimize.setEnabled(True)
        self.btn_add_asset.setEnabled(True)
        self.btn_edit_asset.setEnabled(True)
        self.btn_del_asset.setEnabled(True)
        self.btn_add_partner.setEnabled(True)
        self.btn_edit_partner.setEnabled(True)
        self.btn_del_partner.setEnabled(True)
        
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(self, "Sukses", "Data Aset dan Mitra berhasil dimuat dari database!")

    def open_add_asset_form(self):
        dialog = AddAssetDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data['asset_id'].strip() == "":
                QMessageBox.warning(self, "Gagal", "Asset ID tidak boleh kosong!")
                return
            
            success, msg = save_asset_to_db(new_data)
            if success:
                self.assets_df = load_assets_data()
                self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
                self.refresh_audit_logs()
                self.reset_optimization_state()
                self.tabs.setCurrentIndex(0)
                QMessageBox.information(self, "Sukses", "Aset baru berhasil disimpan ke Database!")
            else:
                QMessageBox.warning(self, "Gagal Menyimpan", msg)

    def open_edit_asset_form(self):
        selected_row = self.tab_assets.currentRow()
        if selected_row < 0 or self.tab_assets.item(selected_row, 0) is None:
            QMessageBox.warning(self, "Peringatan", "Pilih baris aset pada tabel 'Data Aset' yang ingin diedit terlebih dahulu.")
            return
            
        asset_id = self.tab_assets.item(selected_row, 0).text()
        row_data = self.assets_df[self.assets_df['asset_id'] == asset_id].iloc[0].to_dict()
        
        dialog = AddAssetDialog(self, edit_data=row_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            success, msg = update_asset_in_db(updated_data)
            if success:
                self.assets_df = load_assets_data()
                self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
                self.refresh_audit_logs()
                self.reset_optimization_state()
                QMessageBox.information(self, "Sukses", "Aset berhasil diperbarui!")
            else:
                QMessageBox.critical(self, "Error", msg)

    def delete_selected_asset(self):
        selected_row = self.tab_assets.currentRow()
        if selected_row < 0 or self.tab_assets.item(selected_row, 0) is None:
            QMessageBox.warning(self, "Peringatan", "Pilih baris aset pada tabel 'Data Aset' yang ingin dihapus terlebih dahulu.")
            return
            
        asset_id = self.tab_assets.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Konfirmasi Hapus", 
                                       f"Apakah Anda yakin ingin menghapus aset dengan ID: {asset_id}?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            success, msg = delete_asset_from_db(asset_id)
            if success:
                self.assets_df = load_assets_data()
                self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
                self.refresh_audit_logs()
                self.reset_optimization_state()
                QMessageBox.information(self, "Sukses", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

    def open_add_partner_form(self):
        dialog = AddPartnerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data['partner_id'].strip() == "" or new_data['partner_name'].strip() == "":
                QMessageBox.warning(self, "Gagal", "Partner ID dan Nama tidak boleh kosong!")
                return
                
            success, msg = save_partner_to_db(new_data)
            if success:
                self.partners_df = load_partners_data()
                self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
                self.refresh_audit_logs()
                self.reset_matching_state()
                self.tabs.setCurrentIndex(1)
                QMessageBox.information(self, "Sukses", "Mitra baru berhasil disimpan ke Database!")
            else:
                QMessageBox.warning(self, "Gagal Menyimpan", msg)

    def open_edit_partner_form(self):
        selected_row = self.tab_partners.currentRow()
        if selected_row < 0 or self.tab_partners.item(selected_row, 0) is None:
            QMessageBox.warning(self, "Peringatan", "Pilih baris mitra pada tabel 'Data Mitra' yang ingin diedit terlebih dahulu.")
            return
            
        partner_id = self.tab_partners.item(selected_row, 0).text()
        row_data = self.partners_df[self.partners_df['partner_id'] == partner_id].iloc[0].to_dict()
        
        dialog = AddPartnerDialog(self, edit_data=row_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            success, msg = update_partner_in_db(updated_data)
            if success:
                self.partners_df = load_partners_data()
                self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
                self.refresh_audit_logs()
                self.reset_matching_state()
                QMessageBox.information(self, "Sukses", "Mitra berhasil diperbarui!")
            else:
                QMessageBox.critical(self, "Error", msg)

    def delete_selected_partner(self):
        selected_row = self.tab_partners.currentRow()
        if selected_row < 0 or self.tab_partners.item(selected_row, 0) is None:
            QMessageBox.warning(self, "Peringatan", "Pilih baris mitra pada tabel 'Data Mitra' yang ingin dihapus terlebih dahulu.")
            return
            
        partner_id = self.tab_partners.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Konfirmasi Hapus", 
                                       f"Apakah Anda yakin ingin menghapus mitra dengan ID: {partner_id}?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            success, msg = delete_partner_from_db(partner_id)
            if success:
                self.partners_df = load_partners_data()
                self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
                self.refresh_audit_logs()
                self.reset_matching_state()
                QMessageBox.information(self, "Sukses", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

    def optimize_pricing(self):
        if self.assets_df is None or self.assets_df.empty:
            return
            
        current_margin = self.slider_margin.value()
        optimizer = PricingOptimizer()
        self.optimized_df = optimizer.calculate_dynamic_pricing(self.assets_df, custom_margin=current_margin)
        
        display_df = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
        self.populate_table(self.tab_pricing, display_df)
        
        self.update_charts()
        
        log_activity("PRICING", f"Menghitung Dynamic Pricing dengan margin profit {current_margin}%.")
        self.refresh_audit_logs()
        
        self.btn_match.setEnabled(True)
        self.slider_margin.setEnabled(True)
        self.tabs.setCurrentIndex(2)

    def on_slider_changed(self, value):
        self.lbl_slider_val.setText(f"{value}%")
        
        if self.assets_df is not None and not self.assets_df.empty:
            optimizer = PricingOptimizer()
            self.optimized_df = optimizer.calculate_dynamic_pricing(self.assets_df, custom_margin=value)
            
            display_df = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
            self.populate_table(self.tab_pricing, display_df)
            
            self.update_charts()
            
            if self.btn_match.isEnabled() and self.matching_df is not None:
                matcher = PartnerMatcher()
                self.matching_df = matcher.match_assets_to_partners(self.optimized_df, self.partners_df)
                if not self.matching_df.empty:
                    self.populate_table(self.tab_matches, self.matching_df)
                    self.btn_export.setEnabled(True)
                else:
                    self.clear_table(self.tab_matches)
                    self.btn_export.setEnabled(False)

    def match_partners(self):
        if self.optimized_df is None or self.optimized_df.empty:
             return
             
        matcher = PartnerMatcher()
        self.matching_df = matcher.match_assets_to_partners(self.optimized_df, self.partners_df)
        
        if self.matching_df.empty:
            QMessageBox.warning(self, "Hasil", "Tidak ada mitra yang cocok dengan kriteria saat ini.")
            self.clear_table(self.tab_matches)
            self.btn_export.setEnabled(False)
        else:
            self.populate_table(self.tab_matches, self.matching_df)
            log_activity("MATCHING", "Menjalankan pencocokan mitra terbaik berdasarkan AI scoring.")
            self.refresh_audit_logs()
            self.tabs.setCurrentIndex(3)
            self.btn_export.setEnabled(True)
            QMessageBox.information(self, "Sukses", "Rekomendasi mitra berhasil dibuat!")

    def export_report(self):
        if self.matching_df is None or self.matching_df.empty:
            return

        options = QFileDialog.Options()
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, 
            "Simpan Laporan Logistik", 
            "Laporan_Optimasi_Logistik.xlsx", 
            "Excel Files (*.xlsx);;CSV Files (*.csv)", 
            options=options
        )
        
        if file_path:
            try:
                lower_path = file_path.lower()
                if not (lower_path.endswith('.xlsx') or lower_path.endswith('.csv')):
                    if 'csv' in selected_filter.lower():
                        file_path += '.csv'
                    else:
                        file_path += '.xlsx'
                    lower_path = file_path.lower()

                if lower_path.endswith('.xlsx'):
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        self.matching_df.to_excel(writer, sheet_name='Rekomendasi_Mitra', index=False)
                        display_pricing = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
                        display_pricing.to_excel(writer, sheet_name='Harga_Optimal', index=False)
                elif lower_path.endswith('.csv'):
                    self.matching_df.to_csv(file_path, index=False)
                
                log_activity("EXPORT", f"Mengekspor laporan ke file: {file_path}")
                self.refresh_audit_logs()
                QMessageBox.information(self, "Berhasil", f"Laporan sukses diekspor ke:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Ekspor", f"Gagal menyimpan file.\nDetail: {str(e)}")

    def populate_table(self, table_widget, df):
        table_widget.clear()
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])
        table_widget.setHorizontalHeaderLabels(df.columns.astype(str))
        
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                table_widget.setItem(i, j, item)
        
        header = table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Terapkan Global StyleSheet Professional
    app.setStyleSheet(MODERN_STYLE)
    
    window = LogisticsApp()
    window.show()
    sys.exit(app.exec_())