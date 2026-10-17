import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, 
                             QTabWidget, QHeaderView, QMessageBox, QDialog, QFormLayout, 
                             QLineEdit, QComboBox, QDoubleSpinBox, QFileDialog, QLabel, QSlider, QGroupBox,
                             QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# Import Matplotlib untuk integrasi GUI PyQt5
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Import modul bisnis 
from src.data_handler import (load_assets_data, load_partners_data, load_audit_logs, log_activity,
                              save_asset_to_db, save_partner_to_db, 
                              delete_asset_from_db, delete_partner_from_db,
                              update_asset_in_db, update_partner_in_db,
                              import_assets_from_file, import_partners_from_file)
from src.pricing_optimizer import PricingOptimizer
from src.partner_matcher import PartnerMatcher
from src.financial_calculator import FinancialAnalyzer

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
        self.capacity_input.setMaximum(1000000)
        self.capacity_input.setValue(10.0)
        if self.is_edit:
            self.capacity_input.setValue(float(edit_data.get('capacity_tons', 10.0)))
            
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(1000)
        self.price_input.setMaximum(100000000000)
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
            'asset_id': self.id_input.text().strip(),
            'asset_type': self.type_input.currentText().strip(),
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
        self.budget_input.setMaximum(100000000000)
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
            'partner_id': self.id_input.text().strip(),
            'partner_name': self.name_input.text().strip(),
            'req_type': self.req_type_input.currentText().strip(),
            'budget': self.budget_input.value(),
            'reliability_score': self.score_input.value()
        }

class AlgorithmSettingsDialog(QDialog):
    def __init__(self, parent=None, weight_budget=0.7, weight_reliability=0.3, min_score_threshold=50.0):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Pengaturan Bobot & Threshold Algoritma")
        self.setFixedSize(500, 440)
        
        self._sync_in_progress = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)
        
        # Info Header
        info_label = QLabel(
            "<b>Konfigurasi Parameter Algoritma Rekomendasi Mitra:</b><br>"
            "<span style='color: #4a5568; font-size: 11px;'>"
            "Atur prioritas antara kesesuaian anggaran vs reputasi mitra, serta batas minimal skor kelayakan."
            "</span>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Form Group
        form_group = QGroupBox("Bobot Kriteria & Batas Kelayakan")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(12, 16, 12, 12)
        
        # 1. Bobot Anggaran
        self.slider_budget = QSlider(Qt.Horizontal)
        self.slider_budget.setRange(0, 100)
        self.slider_budget.setSingleStep(5)
        self.slider_budget.setValue(int(round(weight_budget * 100)))

        self.spin_budget = QSpinBox()
        self.spin_budget.setRange(0, 100)
        self.spin_budget.setSuffix(" %")
        self.spin_budget.setValue(int(round(weight_budget * 100)))
        
        budget_row = QHBoxLayout()
        budget_row.addWidget(self.slider_budget)
        budget_row.addWidget(self.spin_budget)
        form_layout.addRow("💰 Kesesuaian Anggaran:", budget_row)

        # 2. Bobot Reputasi
        self.slider_reliability = QSlider(Qt.Horizontal)
        self.slider_reliability.setRange(0, 100)
        self.slider_reliability.setSingleStep(5)
        self.slider_reliability.setValue(int(round(weight_reliability * 100)))

        self.spin_reliability = QSpinBox()
        self.spin_reliability.setRange(0, 100)
        self.spin_reliability.setSuffix(" %")
        self.spin_reliability.setValue(int(round(weight_reliability * 100)))

        rel_row = QHBoxLayout()
        rel_row.addWidget(self.slider_reliability)
        rel_row.addWidget(self.spin_reliability)
        form_layout.addRow("⭐ Skor Reliabilitas:", rel_row)

        # Checkbox Auto-Sync
        self.chk_sync = QCheckBox("🔒 Kunci total bobot anggaran & reputasi = 100%")
        self.chk_sync.setChecked(True)
        form_layout.addRow("", self.chk_sync)

        # 3. Ambang Batas Minimal Skor (Threshold)
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setRange(0, 100)
        self.slider_threshold.setSingleStep(5)
        self.slider_threshold.setValue(int(round(min_score_threshold)))

        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(0, 100)
        self.spin_threshold.setSuffix(" %")
        self.spin_threshold.setValue(int(round(min_score_threshold)))

        thresh_row = QHBoxLayout()
        thresh_row.addWidget(self.slider_threshold)
        thresh_row.addWidget(self.spin_threshold)
        form_layout.addRow("🎯 Ambang Batas Minimal:", thresh_row)

        layout.addWidget(form_group)

        # Pratinjau Formula
        self.card_preview = QGroupBox("Pratinjau Formula Algoritma")
        card_layout = QVBoxLayout(self.card_preview)
        card_layout.setContentsMargins(10, 8, 10, 8)
        self.lbl_formula = QLabel()
        self.lbl_formula.setStyleSheet("font-size: 11px; color: #2d3748; line-height: 1.4;")
        self.lbl_formula.setWordWrap(True)
        card_layout.addWidget(self.lbl_formula)
        layout.addWidget(self.card_preview)

        # Signal connections
        self.slider_budget.valueChanged.connect(self._on_slider_budget_changed)
        self.spin_budget.valueChanged.connect(self.slider_budget.setValue)

        self.slider_reliability.valueChanged.connect(self._on_slider_rel_changed)
        self.spin_reliability.valueChanged.connect(self.slider_reliability.setValue)

        self.slider_threshold.valueChanged.connect(self.spin_threshold.setValue)
        self.spin_threshold.valueChanged.connect(self.slider_threshold.setValue)
        self.slider_threshold.valueChanged.connect(self._update_preview)

        # Buttons
        btn_box = QHBoxLayout()
        self.btn_reset = QPushButton("🔄 Reset Default")
        self.btn_reset.setStyleSheet("background-color: #edf2f7; color: #4a5568;")
        self.btn_reset.clicked.connect(self.reset_defaults)

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = QPushButton("💾 Simpan & Terapkan")
        self.btn_apply.setStyleSheet("background-color: #3182ce; color: white; font-weight: bold; padding: 8px 16px;")
        self.btn_apply.clicked.connect(self.accept)

        btn_box.addWidget(self.btn_reset)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_apply)
        layout.addLayout(btn_box)

        self._update_preview()

    def _on_slider_budget_changed(self, val):
        if self._sync_in_progress:
            return
        self.spin_budget.blockSignals(True)
        self.spin_budget.setValue(val)
        self.spin_budget.blockSignals(False)
        
        if self.chk_sync.isChecked():
            self._sync_in_progress = True
            other_val = max(0, 100 - val)
            self.slider_reliability.setValue(other_val)
            self.spin_reliability.setValue(other_val)
            self._sync_in_progress = False
            
        self._update_preview()

    def _on_slider_rel_changed(self, val):
        if self._sync_in_progress:
            return
        self.spin_reliability.blockSignals(True)
        self.spin_reliability.setValue(val)
        self.spin_reliability.blockSignals(False)
        
        if self.chk_sync.isChecked():
            self._sync_in_progress = True
            other_val = max(0, 100 - val)
            self.slider_budget.setValue(other_val)
            self.spin_budget.setValue(other_val)
            self._sync_in_progress = False
            
        self._update_preview()

    def _update_preview(self):
        b = self.slider_budget.value()
        r = self.slider_reliability.value()
        th = self.slider_threshold.value()
        total = b + r
        if total > 0:
            eff_b = (b / total) * 100.0
            eff_r = (r / total) * 100.0
        else:
            eff_b, eff_r = 50.0, 50.0
            
        text = (
            f"• <b>Skor Rekomendasi:</b> (Kesesuaian Anggaran × {eff_b:.1f}%) + (Skor Reputasi × {eff_r:.1f}%)<br>"
            f"• <b>Kriteria Filter:</b> Rekomendasi lolos jika Skor Kecocokan > <b>{th}%</b>"
        )
        if total != 100 and not self.chk_sync.isChecked():
            text += f"<br><span style='color: #dd6b20;'>⚠️ Total bobot ({total}%) akan dinormalisasi proporsional.</span>"
        self.lbl_formula.setText(text)

    def reset_defaults(self):
        self._sync_in_progress = True
        self.chk_sync.setChecked(True)
        self.slider_budget.setValue(70)
        self.spin_budget.setValue(70)
        self.slider_reliability.setValue(30)
        self.spin_reliability.setValue(30)
        self.slider_threshold.setValue(50)
        self.spin_threshold.setValue(50)
        self._sync_in_progress = False
        self._update_preview()

    def get_config(self):
        total = self.slider_budget.value() + self.slider_reliability.value()
        if total <= 0:
            b_val, r_val = 0.5, 0.5
        else:
            b_val = self.slider_budget.value() / 100.0
            r_val = self.slider_reliability.value() / 100.0
        return {
            'weight_budget': b_val,
            'weight_reliability': r_val,
            'min_score_threshold': float(self.slider_threshold.value())
        }

# --- WIDGET KANVAS MATPLOTLIB ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor('#ffffff')
        self.axes = fig.add_subplot(111)
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
        self.assignment_df = None
        self.logs_df = None
        
        # Konfigurasi Algoritma Seleksi Mitra
        self.weight_budget = 0.7
        self.weight_reliability = 0.3
        self.min_score_threshold = 50.0
        self.partner_matcher = PartnerMatcher(
            weight_budget=self.weight_budget,
            weight_reliability=self.weight_reliability,
            min_score_threshold=self.min_score_threshold
        )
        
        # Konfigurasi Finansial & Biaya Operasional
        self.cost_ratio = 0.35
        
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

        self.btn_assign = QPushButton("🎯 4. Alokasi Eksklusif 1-ke-1")
        self.btn_assign.clicked.connect(self.run_exclusive_assignment)
        self.btn_assign.setEnabled(False)
        self.btn_assign.setStyleSheet("background-color: #805ad5; color: white; font-weight: bold;")
        
        self.btn_export = QPushButton("💾 Export Laporan Excel/CSV")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #2b6cb0; color: white; font-weight: bold;")

        self.btn_matching_settings = QPushButton("⚙️ Pengaturan Bobot")
        self.btn_matching_settings.clicked.connect(self.open_algorithm_settings)
        self.btn_matching_settings.setStyleSheet("background-color: #6b46c1; color: white; font-weight: bold;")
        
        self.btn_import_assets = QPushButton("📥 Import Aset")
        self.btn_import_assets.clicked.connect(self.import_assets_action)
        self.btn_import_assets.setStyleSheet("background-color: #4a5568; color: white; font-weight: bold;")

        self.btn_import_partners = QPushButton("📥 Import Mitra")
        self.btn_import_partners.clicked.connect(self.import_partners_action)
        self.btn_import_partners.setStyleSheet("background-color: #4a5568; color: white; font-weight: bold;")

        btn_layout_2.addWidget(self.btn_optimize)
        btn_layout_2.addWidget(self.btn_match)
        btn_layout_2.addWidget(self.btn_assign)
        btn_layout_2.addWidget(self.btn_matching_settings)
        btn_layout_2.addWidget(self.btn_export)
        btn_layout_2.addWidget(self.btn_import_assets)
        btn_layout_2.addWidget(self.btn_import_partners)
        control_layout.addLayout(btn_layout_2)

        # Baris 3: Slider What-If Analysis (Pricing Margin & Operational Cost Ratio)
        slider_layout = QHBoxLayout()
        self.lbl_slider_title = QLabel("<b>Simulasi Margin Profit (Pricing):</b>")
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

        # Slider Biaya Operasional (What-If Cost Analysis)
        self.lbl_cost_slider_title = QLabel("  |  <b>Simulasi Rasio Biaya Ops (BBM/Servis):</b>")
        self.slider_cost = QSlider(Qt.Horizontal)
        self.slider_cost.setRange(5, 70)
        self.slider_cost.setValue(35)
        self.slider_cost.setEnabled(False)
        self.slider_cost.valueChanged.connect(self.on_cost_slider_changed)

        self.lbl_cost_slider_val = QLabel("35%")
        self.lbl_cost_slider_val.setStyleSheet("font-weight: bold; color: #e53e3e; font-size: 14px;")

        slider_layout.addWidget(self.lbl_cost_slider_title)
        slider_layout.addWidget(self.slider_cost)
        slider_layout.addWidget(self.lbl_cost_slider_val)
        control_layout.addLayout(slider_layout)

        main_layout.addWidget(control_group)

        # Panel KPI Dashboard Finansial & Metrik Bisnis
        self.kpi_group = QGroupBox("📊 Ringkasan Eksekutif & KPI Finansial")
        kpi_layout = QHBoxLayout(self.kpi_group)
        kpi_layout.setSpacing(10)
        kpi_layout.setContentsMargins(10, 10, 10, 10)

        self.card_rev, self.lbl_kpi_rev_val, self.lbl_kpi_rev_sub = self.create_kpi_card(
            "💰 TOTAL PROYEKSI REVENUE", "Rp 0", "Harga Dasar: Rp 0", "#2b6cb0"
        )
        self.card_uplift, self.lbl_kpi_uplift_val, self.lbl_kpi_uplift_sub = self.create_kpi_card(
            "📈 KENAIKAN MARGIN (UPLIFT)", "0.0%", "+Rp 0 vs Dasar", "#2f855a"
        )
        self.card_net, self.lbl_kpi_net_val, self.lbl_kpi_net_sub = self.create_kpi_card(
            "💵 ESTIMASI NET PROFIT", "Rp 0 (0.0%)", "Biaya Ops: Rp 0", "#2c5282"
        )
        self.card_match, self.lbl_kpi_match_val, self.lbl_kpi_match_sub = self.create_kpi_card(
            "🤝 RASIO ASET TERPASANGKAN", "0 / 0 (0%)", "0 Mitra Terdaftar", "#d69e2e"
        )
        self.card_quality, self.lbl_kpi_quality_val, self.lbl_kpi_quality_sub = self.create_kpi_card(
            "⭐ RATA-RATA SKOR KUALITAS", "0.0%", "AI Scoring Rekomendasi", "#6b46c1"
        )

        kpi_layout.addWidget(self.card_rev)
        kpi_layout.addWidget(self.card_uplift)
        kpi_layout.addWidget(self.card_net)
        kpi_layout.addWidget(self.card_match)
        kpi_layout.addWidget(self.card_quality)

        main_layout.addWidget(self.kpi_group)

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

        # Tab Rekomendasi Mitra dengan Kontrol & Filter
        self.widget_matches = QWidget()
        layout_matches = QVBoxLayout(self.widget_matches)
        
        panel_matches_header = QGroupBox("⚙️ Kontrol Algoritma & Filter Rekomendasi")
        panel_matches_header.setStyleSheet("""
            QGroupBox {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                margin-top: 0px;
            }
        """)
        header_layout_matches = QHBoxLayout(panel_matches_header)
        header_layout_matches.setContentsMargins(6, 4, 6, 4)

        self.lbl_matching_config = QLabel()
        self.lbl_matching_config.setStyleSheet("font-size: 12px; color: #2d3748;")

        lbl_quick_thresh = QLabel("<b>Min. Skor:</b>")
        lbl_quick_thresh.setStyleSheet("font-size: 11px; color: #4a5568;")
        self.slider_quick_thresh = QSlider(Qt.Horizontal)
        self.slider_quick_thresh.setRange(0, 100)
        self.slider_quick_thresh.setSingleStep(5)
        self.slider_quick_thresh.setValue(int(self.min_score_threshold))
        self.slider_quick_thresh.setFixedWidth(130)
        self.slider_quick_thresh.valueChanged.connect(self.on_quick_thresh_changed)

        self.lbl_quick_thresh_val = QLabel(f">{int(self.min_score_threshold)}%")
        self.lbl_quick_thresh_val.setStyleSheet("font-weight: bold; color: #6b46c1; font-size: 12px;")

        self.btn_quick_settings = QPushButton("⚙️ Ubah Bobot")
        self.btn_quick_settings.clicked.connect(self.open_algorithm_settings)
        self.btn_quick_settings.setStyleSheet("background-color: #6b46c1; color: white; padding: 4px 10px; font-size: 11px;")

        header_layout_matches.addWidget(self.lbl_matching_config)
        header_layout_matches.addStretch()
        header_layout_matches.addWidget(lbl_quick_thresh)
        header_layout_matches.addWidget(self.slider_quick_thresh)
        header_layout_matches.addWidget(self.lbl_quick_thresh_val)
        header_layout_matches.addWidget(self.btn_quick_settings)

        self.search_matches = QLineEdit()
        self.search_matches.setPlaceholderText("🔍 Cari rekomendasi mitra berdasarkan ID Aset, Tipe, atau Nama Mitra...")
        self.search_matches.textChanged.connect(lambda: self.filter_table(self.tab_matches, self.matching_df, self.search_matches.text()))

        self.tab_matches = QTableWidget()

        layout_matches.addWidget(panel_matches_header)
        layout_matches.addWidget(self.search_matches)
        layout_matches.addWidget(self.tab_matches)
        
        self.update_matching_config_label()
        
        # Tab Alokasi Eksklusif 1-ke-1 (Hungarian Anti Double-Booking)
        self.widget_assignment = QWidget()
        layout_assign = QVBoxLayout(self.widget_assignment)

        panel_assign_header = QGroupBox("🎯 Kontrol Optimasi Alokasi Eksklusif 1-ke-1 (Bipartite Matching)")
        panel_assign_header.setStyleSheet("""
            QGroupBox {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                margin-top: 0px;
            }
        """)
        header_layout_assign = QHBoxLayout(panel_assign_header)
        header_layout_assign.setContentsMargins(6, 4, 6, 4)

        lbl_assign_obj = QLabel("<b>Objektif:</b>")
        lbl_assign_obj.setStyleSheet("font-size: 11px; color: #4a5568;")
        self.combo_assign_obj = QComboBox()
        self.combo_assign_obj.addItem("🎯 Skor Kecocokan", "score")
        self.combo_assign_obj.addItem("💰 Revenue Optimal", "revenue")
        self.combo_assign_obj.addItem("🤝 Nilai Kesepakatan (Deal Value)", "deal_value")
        self.combo_assign_obj.setStyleSheet("font-size: 11px;")

        lbl_assign_method = QLabel("<b>Metode:</b>")
        lbl_assign_method.setStyleSheet("font-size: 11px; color: #4a5568;")
        self.combo_assign_method = QComboBox()
        self.combo_assign_method.addItem("Hungarian (Optimal Global)", "hungarian")
        self.combo_assign_method.addItem("Greedy Heuristic", "greedy")
        self.combo_assign_method.setStyleSheet("font-size: 11px;")

        self.chk_include_unassigned = QCheckBox("Aset Belum Teralokasi")
        self.chk_include_unassigned.setChecked(True)
        self.chk_include_unassigned.setStyleSheet("font-size: 11px; color: #2d3748;")

        self.btn_run_assign = QPushButton("⚡ Jalankan Alokasi")
        self.btn_run_assign.clicked.connect(self.run_exclusive_assignment)
        self.btn_run_assign.setStyleSheet("background-color: #805ad5; color: white; font-weight: bold; padding: 4px 10px; font-size: 11px;")

        header_layout_assign.addWidget(lbl_assign_obj)
        header_layout_assign.addWidget(self.combo_assign_obj)
        header_layout_assign.addWidget(lbl_assign_method)
        header_layout_assign.addWidget(self.combo_assign_method)
        header_layout_assign.addWidget(self.chk_include_unassigned)
        header_layout_assign.addWidget(self.btn_run_assign)
        header_layout_assign.addStretch()

        # Mini KPI Strip untuk Alokasi Eksklusif
        panel_assign_strip = QGroupBox()
        panel_assign_strip.setStyleSheet("""
            QGroupBox {
                background-color: #edf2f7;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        strip_layout = QHBoxLayout(panel_assign_strip)
        strip_layout.setContentsMargins(8, 4, 8, 4)

        self.lbl_strip_ratio = QLabel("<b>Aset Teralokasi:</b> 0 / 0 (0.0%)")
        self.lbl_strip_ratio.setStyleSheet("font-size: 12px; color: #2b6cb0;")
        self.lbl_strip_deal = QLabel("<b>Total Nilai Kesepakatan:</b> Rp 0")
        self.lbl_strip_deal.setStyleSheet("font-size: 12px; color: #2f855a;")
        self.lbl_strip_score = QLabel("<b>Rata-rata Skor:</b> 0.0%")
        self.lbl_strip_score.setStyleSheet("font-size: 12px; color: #6b46c1;")

        strip_layout.addWidget(self.lbl_strip_ratio)
        strip_layout.addSpacing(20)
        strip_layout.addWidget(self.lbl_strip_deal)
        strip_layout.addSpacing(20)
        strip_layout.addWidget(self.lbl_strip_score)
        strip_layout.addStretch()

        self.search_assignment = QLineEdit()
        self.search_assignment.setPlaceholderText("🔍 Cari hasil alokasi berdasarkan ID Aset, Tipe, ID Mitra, atau Nama Mitra...")
        self.search_assignment.textChanged.connect(lambda: self.filter_table(self.tab_assignment, self.assignment_df, self.search_assignment.text()))

        self.tab_assignment = QTableWidget()

        layout_assign.addWidget(panel_assign_header)
        layout_assign.addWidget(panel_assign_strip)
        layout_assign.addWidget(self.search_assignment)
        layout_assign.addWidget(self.tab_assignment)

        # Tab Log Audit
        self.widget_logs = QWidget()
        layout_logs = QVBoxLayout(self.widget_logs)
        self.search_logs = QLineEdit()
        self.search_logs.setPlaceholderText("🔍 Cari riwayat log audit...")
        self.search_logs.textChanged.connect(lambda: self.filter_table(self.tab_logs, self.logs_df, self.search_logs.text()))
        self.tab_logs = QTableWidget()
        layout_logs.addWidget(self.search_logs)
        layout_logs.addWidget(self.tab_logs)
        
        self.tab_charts = QWidget()
        self.init_charts_tab()
        
        for t in [self.tab_assets, self.tab_partners, self.tab_pricing, self.tab_matches, self.tab_assignment, self.tab_logs]:
            t.setSelectionBehavior(QTableWidget.SelectRows)
            t.setSelectionMode(QTableWidget.SingleSelection)

        self.tabs.addTab(self.widget_assets, "📦 Data Aset")
        self.tabs.addTab(self.widget_partners, "🤝 Data Mitra")
        self.tabs.addTab(self.tab_pricing, "💰 Hasil Optimasi Harga")
        self.tabs.addTab(self.widget_matches, "⭐ Rekomendasi Mitra")
        self.tabs.addTab(self.widget_assignment, "🎯 Alokasi Eksklusif 1-ke-1")
        self.tabs.addTab(self.tab_charts, "📊 Grafik Analitik")
        self.tabs.addTab(self.widget_logs, "📜 Log Audit Sistem")
        
        main_layout.addWidget(self.tabs)
        self.refresh_audit_logs()
        self.update_kpi_dashboard()

    def create_kpi_card(self, title, initial_val, initial_sub, value_color):
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 12px;
                margin-top: 0px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(6, 6, 6, 6)
        card_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #718096;")

        lbl_val = QLabel(initial_val)
        lbl_val.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {value_color};")

        lbl_sub = QLabel(initial_sub)
        lbl_sub.setStyleSheet("font-size: 11px; color: #4a5568;")

        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_val)
        card_layout.addWidget(lbl_sub)
        return card, lbl_val, lbl_sub

    def update_kpi_dashboard(self):
        metrics = FinancialAnalyzer.calculate_metrics(
            assets_df=self.assets_df,
            optimized_df=self.optimized_df,
            matching_df=self.matching_df,
            partners_df=self.partners_df,
            cost_ratio=getattr(self, 'cost_ratio', 0.35)
        )

        # 1. Total Proyeksi Revenue
        if self.optimized_df is not None and not self.optimized_df.empty:
            self.lbl_kpi_rev_val.setText(FinancialAnalyzer.format_currency(metrics['total_optimal_revenue']))
            self.lbl_kpi_rev_sub.setText(f"Harga Dasar: {FinancialAnalyzer.format_currency(metrics['total_base_revenue'])}")
        elif self.assets_df is not None and not self.assets_df.empty:
            self.lbl_kpi_rev_val.setText(FinancialAnalyzer.format_currency(metrics['total_base_revenue']))
            self.lbl_kpi_rev_sub.setText("Harga Dasar (Belum dioptimasi)")
        else:
            self.lbl_kpi_rev_val.setText("Rp 0")
            self.lbl_kpi_rev_sub.setText("Harga Dasar: Rp 0")

        # 2. Uplift / Kenaikan Margin
        if self.optimized_df is not None and not self.optimized_df.empty:
            sign = "+" if metrics['revenue_uplift'] >= 0 else ""
            self.lbl_kpi_uplift_val.setText(f"{sign}{metrics['uplift_percentage']}%")
            self.lbl_kpi_uplift_sub.setText(f"{sign}{FinancialAnalyzer.format_currency(metrics['revenue_uplift'])} vs Dasar")
            color = "#2f855a" if metrics['revenue_uplift'] >= 0 else "#e53e3e"
            self.lbl_kpi_uplift_val.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        else:
            self.lbl_kpi_uplift_val.setText("0.0%")
            self.lbl_kpi_uplift_sub.setText("+Rp 0 vs Harga Dasar")
            self.lbl_kpi_uplift_val.setStyleSheet("font-size: 16px; font-weight: bold; color: #718096;")

        # 3. Estimasi Net Profit & Biaya Operasional
        if (self.optimized_df is not None and not self.optimized_df.empty) or (self.assets_df is not None and not self.assets_df.empty):
            self.lbl_kpi_net_val.setText(f"{FinancialAnalyzer.format_currency(metrics['net_profit'])} ({metrics['net_profit_margin_percentage']}%)")
            self.lbl_kpi_net_sub.setText(f"Biaya Ops ({metrics['cost_ratio_percentage']}%): {FinancialAnalyzer.format_currency(metrics['total_operational_cost'])}")
        else:
            self.lbl_kpi_net_val.setText("Rp 0 (0.0%)")
            self.lbl_kpi_net_sub.setText("Biaya Ops: Rp 0")

        # 4. Rasio Keterisian / Matching
        if self.matching_df is not None and not self.matching_df.empty:
            self.lbl_kpi_match_val.setText(f"{metrics['matched_assets_count']} / {metrics['total_assets_count']} ({metrics['matching_ratio_percentage']}%)")
            self.lbl_kpi_match_sub.setText(f"Dari {metrics['total_partners_count']} Mitra Terdaftar")
        elif metrics['total_assets_count'] > 0:
            self.lbl_kpi_match_val.setText(f"0 / {metrics['total_assets_count']} (0%)")
            self.lbl_kpi_match_sub.setText(f"{metrics['total_partners_count']} Mitra Siap Dicocokkan")
        else:
            self.lbl_kpi_match_val.setText("0 / 0 (0%)")
            self.lbl_kpi_match_sub.setText("Belum ada data aset")

        # 5. Kualitas Skor Mitra
        if self.matching_df is not None and not self.matching_df.empty:
            self.lbl_kpi_quality_val.setText(f"{metrics['average_match_score']}%")
            self.lbl_kpi_quality_sub.setText(f"Rata-rata Skor {len(self.matching_df)} Rekomendasi")
        else:
            self.lbl_kpi_quality_val.setText("0.0%")
            self.lbl_kpi_quality_sub.setText("Jalankan AI Partner Matching")

    def init_charts_tab(self):
        chart_layout = QHBoxLayout(self.tab_charts)
        self.canvas_pricing = MplCanvas(self, width=4, height=4, dpi=100)
        chart_layout.addWidget(self.canvas_pricing)
        self.canvas_cost_profit = MplCanvas(self, width=4, height=4, dpi=100)
        chart_layout.addWidget(self.canvas_cost_profit)
        self.canvas_partners = MplCanvas(self, width=4, height=4, dpi=100)
        chart_layout.addWidget(self.canvas_partners)

    def clear_table(self, table_widget):
        table_widget.clear()
        table_widget.setRowCount(0)
        table_widget.setColumnCount(0)

    def reset_optimization_state(self):
        self.optimized_df = None
        self.matching_df = None
        self.assignment_df = None
        self.btn_match.setEnabled(False)
        self.btn_assign.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.slider_margin.setEnabled(False)
        self.slider_cost.setEnabled(False)
        self.clear_table(self.tab_pricing)
        self.search_matches.blockSignals(True)
        self.search_matches.setText("")
        self.search_matches.blockSignals(False)
        self.clear_table(self.tab_matches)
        if hasattr(self, 'search_assignment'):
            self.search_assignment.blockSignals(True)
            self.search_assignment.setText("")
            self.search_assignment.blockSignals(False)
        if hasattr(self, 'tab_assignment'):
            self.clear_table(self.tab_assignment)
        if hasattr(self, 'lbl_strip_ratio'):
            self.lbl_strip_ratio.setText("<b>Aset Teralokasi:</b> 0 / 0 (0.0%)")
            self.lbl_strip_deal.setText("<b>Total Nilai Kesepakatan:</b> Rp 0")
            self.lbl_strip_score.setText("<b>Rata-rata Skor:</b> 0.0%")
        self.update_charts()
        self.update_kpi_dashboard()

    def reset_matching_state(self):
        self.matching_df = None
        self.assignment_df = None
        self.btn_export.setEnabled(False)
        self.search_matches.blockSignals(True)
        self.search_matches.setText("")
        self.search_matches.blockSignals(False)
        self.clear_table(self.tab_matches)
        if hasattr(self, 'search_assignment'):
            self.search_assignment.blockSignals(True)
            self.search_assignment.setText("")
            self.search_assignment.blockSignals(False)
        if hasattr(self, 'tab_assignment'):
            self.clear_table(self.tab_assignment)
        if hasattr(self, 'lbl_strip_ratio'):
            self.lbl_strip_ratio.setText("<b>Aset Teralokasi:</b> 0 / 0 (0.0%)")
            self.lbl_strip_deal.setText("<b>Total Nilai Kesepakatan:</b> Rp 0")
            self.lbl_strip_score.setText("<b>Rata-rata Skor:</b> 0.0%")
        self.update_charts()
        self.update_kpi_dashboard()

    def update_matching_config_label(self):
        total = self.weight_budget + self.weight_reliability
        if total > 0:
            pct_b = (self.weight_budget / total) * 100.0
            pct_r = (self.weight_reliability / total) * 100.0
        else:
            pct_b, pct_r = 50.0, 50.0
        self.lbl_matching_config.setText(
            f"⚖️ <b>Bobot:</b> Anggaran {pct_b:.0f}% | Reliabilitas {pct_r:.0f}%"
        )

    def open_algorithm_settings(self):
        dialog = AlgorithmSettingsDialog(
            self, 
            weight_budget=self.weight_budget, 
            weight_reliability=self.weight_reliability, 
            min_score_threshold=self.min_score_threshold
        )
        if dialog.exec_() == QDialog.Accepted:
            cfg = dialog.get_config()
            self.weight_budget = cfg['weight_budget']
            self.weight_reliability = cfg['weight_reliability']
            self.min_score_threshold = cfg['min_score_threshold']
            
            self.partner_matcher.set_config(
                weight_budget=self.weight_budget,
                weight_reliability=self.weight_reliability,
                min_score_threshold=self.min_score_threshold
            )
            
            self.slider_quick_thresh.blockSignals(True)
            self.slider_quick_thresh.setValue(int(round(self.min_score_threshold)))
            self.slider_quick_thresh.blockSignals(False)
            self.lbl_quick_thresh_val.setText(f">{int(round(self.min_score_threshold))}%")
            
            self.update_matching_config_label()
            
            log_activity("CONFIG", 
                f"Bobot matching diubah: Budget={self.weight_budget*100:.0f}%, "
                f"Reliabilitas={self.weight_reliability*100:.0f}%, Threshold={self.min_score_threshold:.0f}%"
            )
            self.refresh_audit_logs()
            
            # Jika hasil matching atau alokasi sudah pernah dihitung atau data siap, hitung ulang secara reaktif
            if self.optimized_df is not None and not self.optimized_df.empty:
                if self.matching_df is not None:
                    self.match_partners(silent=True)
                if self.assignment_df is not None:
                    self.run_exclusive_assignment(silent=True)
                
            QMessageBox.information(
                self, "Pengaturan Disimpan",
                f"Parameter algoritma seleksi mitra berhasil diperbarui!\n\n"
                f"• Bobot Kesesuaian Anggaran : {self.weight_budget*100:.0f}%\n"
                f"• Bobot Skor Reliabilitas   : {self.weight_reliability*100:.0f}%\n"
                f"• Ambang Batas Minimal      : {self.min_score_threshold:.0f}%"
            )

    def on_quick_thresh_changed(self, value):
        self.min_score_threshold = float(value)
        self.lbl_quick_thresh_val.setText(f">{value}%")
        self.partner_matcher.set_config(min_score_threshold=self.min_score_threshold)
        self.update_matching_config_label()
        
        # Jika hasil matching atau alokasi sudah ada, jalankan ulang secara reaktif tanpa modal dialog
        if self.optimized_df is not None and not self.optimized_df.empty:
            if self.matching_df is not None:
                self.match_partners(silent=True)
            if self.assignment_df is not None:
                self.run_exclusive_assignment(silent=True)

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
            self.canvas_pricing.figure.tight_layout()
        self.canvas_pricing.draw()

        self.canvas_cost_profit.axes.clear()
        ref_df = self.optimized_df if (self.optimized_df is not None and not self.optimized_df.empty) else self.assets_df
        if ref_df is not None and not ref_df.empty:
            metrics = FinancialAnalyzer.calculate_metrics(
                assets_df=self.assets_df,
                optimized_df=self.optimized_df,
                matching_df=self.matching_df,
                partners_df=self.partners_df,
                cost_ratio=getattr(self, 'cost_ratio', 0.35)
            )
            labels = ['BBM', 'Servis', 'Depresiasi', 'Overhead', 'Net Profit']
            values = [
                metrics['fuel_cost'] / 1e6,
                metrics['maintenance_cost'] / 1e6,
                metrics['depreciation_cost'] / 1e6,
                metrics['overhead_cost'] / 1e6,
                metrics['net_profit'] / 1e6
            ]
            colors = ['#e53e3e', '#dd6b20', '#d69e2e', '#718096', '#2b6cb0']
            
            self.canvas_cost_profit.axes.bar(labels, values, color=colors)
            self.canvas_cost_profit.axes.set_title(
                f"Struktur Biaya Ops vs Net Profit ({metrics['net_profit_margin_percentage']}%)",
                fontsize=11, fontweight='bold', color='#2d3748'
            )
            self.canvas_cost_profit.axes.set_ylabel('Nominal (Juta IDR)', fontsize=9, color='#4a5568')
            self.canvas_cost_profit.axes.grid(axis='y', linestyle='--', alpha=0.5)
            self.canvas_cost_profit.figure.tight_layout()
        self.canvas_cost_profit.draw()

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
            self.canvas_partners.figure.tight_layout()
        self.canvas_partners.draw()

    def refresh_audit_logs(self):
        self.logs_df = load_audit_logs()
        self.filter_table(self.tab_logs, self.logs_df, self.search_logs.text())

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
        self.reset_optimization_state()
        
        log_activity("LOAD DATA", "Memuat data aset dan mitra dari database SQLite.")
        self.refresh_audit_logs()
        self.update_charts()
        self.update_kpi_dashboard()
        
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
            if new_data['asset_id'] == "":
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
        matched = self.assets_df[self.assets_df['asset_id'].astype(str) == str(asset_id)]
        if matched.empty:
            QMessageBox.warning(self, "Error", f"Data aset dengan ID {asset_id} tidak ditemukan.")
            return
        row_data = matched.iloc[0].to_dict()
        
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
            if new_data['partner_id'] == "" or new_data['partner_name'] == "":
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
        matched = self.partners_df[self.partners_df['partner_id'].astype(str) == str(partner_id)]
        if matched.empty:
            QMessageBox.warning(self, "Error", f"Data mitra dengan ID {partner_id} tidak ditemukan.")
            return
        row_data = matched.iloc[0].to_dict()
        
        dialog = AddPartnerDialog(self, edit_data=row_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_data()
            if updated_data['partner_name'] == "":
                QMessageBox.warning(self, "Gagal", "Nama mitra tidak boleh kosong!")
                return
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
            QMessageBox.warning(self, "Peringatan", "Data aset belum dimuat atau kosong. Silakan muat atau tambah aset terlebih dahulu.")
            return
            
        current_margin = self.slider_margin.value()
        optimizer = PricingOptimizer()
        self.optimized_df = optimizer.calculate_dynamic_pricing(self.assets_df, custom_margin=current_margin)
        
        display_df = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
        self.populate_table(self.tab_pricing, display_df)
        
        self.update_charts()
        
        log_activity("PRICING", f"Menghitung Dynamic Pricing dengan margin profit {current_margin}%.")
        self.refresh_audit_logs()
        self.update_kpi_dashboard()
        
        self.btn_match.setEnabled(True)
        self.btn_assign.setEnabled(True)
        self.slider_margin.setEnabled(True)
        self.slider_cost.setEnabled(True)
        self.tabs.setCurrentIndex(2)

    def on_cost_slider_changed(self, value):
        self.cost_ratio = value / 100.0
        self.lbl_cost_slider_val.setText(f"{value}%")
        self.update_kpi_dashboard()
        self.update_charts()

    def on_slider_changed(self, value):
        self.lbl_slider_val.setText(f"{value}%")
        
        if self.assets_df is not None and not self.assets_df.empty:
            optimizer = PricingOptimizer()
            self.optimized_df = optimizer.calculate_dynamic_pricing(self.assets_df, custom_margin=value)
            
            display_df = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
            self.populate_table(self.tab_pricing, display_df)
            
            self.update_charts()
            
            if self.btn_match.isEnabled() and self.matching_df is not None:
                self.matching_df = self.partner_matcher.match_assets_to_partners(
                    self.optimized_df, 
                    self.partners_df,
                    weight_budget=self.weight_budget,
                    weight_reliability=self.weight_reliability,
                    min_score_threshold=self.min_score_threshold
                )
                if not self.matching_df.empty:
                    self.filter_table(self.tab_matches, self.matching_df, self.search_matches.text())
                    self.btn_export.setEnabled(True)
                else:
                    self.clear_table(self.tab_matches)
                    if self.assignment_df is None or self.assignment_df.empty:
                        self.btn_export.setEnabled(False)

            if self.btn_assign.isEnabled() and self.assignment_df is not None:
                self.run_exclusive_assignment(silent=True)

            self.update_kpi_dashboard()

    def match_partners(self, silent=False):
        if self.optimized_df is None or self.optimized_df.empty:
            if not silent:
                QMessageBox.warning(self, "Peringatan", "Hitung Dynamic Pricing terlebih dahulu sebelum mencari mitra.")
            return
             
        self.matching_df = self.partner_matcher.match_assets_to_partners(
            self.optimized_df, 
            self.partners_df,
            weight_budget=self.weight_budget,
            weight_reliability=self.weight_reliability,
            min_score_threshold=self.min_score_threshold
        )
        
        if self.matching_df.empty:
            if not silent:
                QMessageBox.warning(self, "Hasil", "Tidak ada mitra yang cocok dengan kriteria saat ini.")
            self.clear_table(self.tab_matches)
            if self.assignment_df is None or self.assignment_df.empty:
                self.btn_export.setEnabled(False)
        else:
            self.filter_table(self.tab_matches, self.matching_df, self.search_matches.text())
            if not silent:
                log_activity("MATCHING", 
                    f"Menjalankan pencocokan mitra terbaik (Budget: {self.weight_budget*100:.0f}%, "
                    f"Reputasi: {self.weight_reliability*100:.0f}%, Threshold: {self.min_score_threshold:.0f}%)."
                )
                self.refresh_audit_logs()
                self.tabs.setCurrentIndex(3)
                self.btn_export.setEnabled(True)
                QMessageBox.information(self, "Sukses", "Rekomendasi mitra berhasil dibuat!")
            else:
                self.btn_export.setEnabled(True)
        self.update_kpi_dashboard()

    def run_exclusive_assignment(self, silent=False):
        if self.optimized_df is None or self.optimized_df.empty:
            if not silent:
                QMessageBox.warning(self, "Peringatan", "Hitung Dynamic Pricing terlebih dahulu sebelum menjalankan alokasi eksklusif.")
            return

        obj = self.combo_assign_obj.currentData() if hasattr(self, 'combo_assign_obj') else 'score'
        method = self.combo_assign_method.currentData() if hasattr(self, 'combo_assign_method') else 'hungarian'
        include_unassigned = self.chk_include_unassigned.isChecked() if hasattr(self, 'chk_include_unassigned') else True

        self.assignment_df = self.partner_matcher.assign_exclusive_partners(
            self.optimized_df,
            self.partners_df,
            objective=obj,
            method=method,
            include_unassigned=include_unassigned,
            weight_budget=self.weight_budget,
            weight_reliability=self.weight_reliability,
            min_score_threshold=self.min_score_threshold
        )

        if self.assignment_df.empty:
            if not silent:
                QMessageBox.warning(self, "Hasil Alokasi", "Tidak ada pasangan aset dan mitra yang dapat dialokasikan dengan kriteria saat ini.")
            self.clear_table(self.tab_assignment)
            if self.matching_df is None or self.matching_df.empty:
                self.btn_export.setEnabled(False)
        else:
            self.filter_table(self.tab_assignment, self.assignment_df, self.search_assignment.text())
            summary = self.partner_matcher.calculate_assignment_summary(
                self.assignment_df,
                total_assets=len(self.assets_df) if self.assets_df is not None else len(self.assignment_df),
                total_partners=len(self.partners_df) if self.partners_df is not None else 0
            )
            tot_a = summary['total_assigned'] + summary['unassigned_assets']
            self.lbl_strip_ratio.setText(f"<b>Aset Teralokasi:</b> {summary['total_assigned']} / {tot_a} ({summary['allocation_rate']}%)")
            self.lbl_strip_deal.setText(f"<b>Total Nilai Kesepakatan:</b> {FinancialAnalyzer.format_currency(summary['total_deal_value'])}")
            self.lbl_strip_score.setText(f"<b>Rata-rata Skor:</b> {summary['average_match_score']}%")

            self.btn_export.setEnabled(True)
            if not silent:
                log_activity("ASSIGNMENT",
                    f"Menjalankan alokasi eksklusif 1-ke-1 (Objektif: {obj}, Metode: {method}) - "
                    f"{summary['total_assigned']} aset berhasil dipasangkan tanpa bentrok."
                )
                self.refresh_audit_logs()
                self.tabs.setCurrentIndex(4)
                QMessageBox.information(
                    self,
                    "Sukses Alokasi",
                    f"Alokasi eksklusif 1-ke-1 berhasil!\n\n"
                    f"• Aset Teralokasi: {summary['total_assigned']} / {tot_a} ({summary['allocation_rate']}%)\n"
                    f"• Total Deal Value: {FinancialAnalyzer.format_currency(summary['total_deal_value'])}\n"
                    f"• Rata-rata Skor: {summary['average_match_score']}%\n\n"
                    f"Setiap aset dan mitra terpasangkan secara eksklusif tanpa double-booking."
                )

    def export_report(self):
        if (self.matching_df is None or self.matching_df.empty) and (self.assignment_df is None or self.assignment_df.empty):
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
                    metrics = FinancialAnalyzer.calculate_metrics(
                        assets_df=self.assets_df,
                        optimized_df=self.optimized_df,
                        matching_df=self.matching_df,
                        partners_df=self.partners_df,
                        cost_ratio=getattr(self, 'cost_ratio', 0.35)
                    )
                    summary_data = [
                        {'Metrik': 'Total Harga Dasar Aset (IDR)', 'Nilai': metrics['total_base_revenue']},
                        {'Metrik': 'Total Proyeksi Revenue Optimal (IDR)', 'Nilai': metrics['total_optimal_revenue']},
                        {'Metrik': 'Potensi Kenaikan Revenue (Uplift IDR)', 'Nilai': metrics['revenue_uplift']},
                        {'Metrik': 'Persentase Kenaikan Uplift (%)', 'Nilai': metrics['uplift_percentage']},
                        {'Metrik': f"Total Biaya Operasional ({metrics['cost_ratio_percentage']}%) (IDR)", 'Nilai': metrics['total_operational_cost']},
                        {'Metrik': '  - Estimasi Biaya BBM (IDR)', 'Nilai': metrics['fuel_cost']},
                        {'Metrik': '  - Estimasi Biaya Perawatan (IDR)', 'Nilai': metrics['maintenance_cost']},
                        {'Metrik': '  - Estimasi Biaya Depresiasi (IDR)', 'Nilai': metrics['depreciation_cost']},
                        {'Metrik': '  - Estimasi Biaya Overhead (IDR)', 'Nilai': metrics['overhead_cost']},
                        {'Metrik': 'Estimasi Laba Bersih / Net Profit (IDR)', 'Nilai': metrics['net_profit']},
                        {'Metrik': 'Margin Laba Bersih / Net Margin (%)', 'Nilai': metrics['net_profit_margin_percentage']},
                        {'Metrik': 'Rasio Aset Terpasangkan (%)', 'Nilai': metrics['matching_ratio_percentage']},
                        {'Metrik': 'Rata-rata Skor Kualitas Mitra (%)', 'Nilai': metrics['average_match_score']}
                    ]
                    summary_df = pd.DataFrame(summary_data)
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        if self.assignment_df is not None and not self.assignment_df.empty:
                            self.assignment_df.to_excel(writer, sheet_name='Alokasi_Eksklusif', index=False)
                        if self.matching_df is not None and not self.matching_df.empty:
                            self.matching_df.to_excel(writer, sheet_name='Rekomendasi_Mitra', index=False)
                        if self.optimized_df is not None and not self.optimized_df.empty:
                            display_pricing = self.optimized_df[['asset_id', 'asset_type', 'base_price', 'optimal_price']]
                            display_pricing.to_excel(writer, sheet_name='Harga_Optimal', index=False)
                        summary_df.to_excel(writer, sheet_name='Ringkasan_Finansial', index=False)
                elif lower_path.endswith('.csv'):
                    if self.tabs.currentIndex() == 4 and self.assignment_df is not None and not self.assignment_df.empty:
                        self.assignment_df.to_csv(file_path, index=False)
                    elif self.matching_df is not None and not self.matching_df.empty:
                        self.matching_df.to_csv(file_path, index=False)
                    elif self.assignment_df is not None and not self.assignment_df.empty:
                        self.assignment_df.to_csv(file_path, index=False)
                
                log_activity("EXPORT", f"Mengekspor laporan ke file: {file_path}")
                self.refresh_audit_logs()
                QMessageBox.information(self, "Berhasil", f"Laporan sukses diekspor ke:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error Ekspor", f"Gagal menyimpan file.\nDetail: {str(e)}")

    def import_assets_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Data Aset (Excel / CSV)",
            "",
            "Spreadsheet Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        success, msg, new_count, updated_count, error_count = import_assets_from_file(file_path)
        if success:
            self.assets_df = load_assets_data()
            if self.partners_df is None:
                self.partners_df = load_partners_data()
                self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
            self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
            self.refresh_audit_logs()
            self.reset_optimization_state()
            self.btn_optimize.setEnabled(True)
            self.btn_add_asset.setEnabled(True)
            self.btn_edit_asset.setEnabled(True)
            self.btn_del_asset.setEnabled(True)
            self.btn_add_partner.setEnabled(True)
            self.btn_edit_partner.setEnabled(True)
            self.btn_del_partner.setEnabled(True)
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, "Import Aset Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal Import Aset", msg)

    def import_partners_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Data Mitra (Excel / CSV)",
            "",
            "Spreadsheet Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        success, msg, new_count, updated_count, error_count = import_partners_from_file(file_path)
        if success:
            self.partners_df = load_partners_data()
            if self.assets_df is None:
                self.assets_df = load_assets_data()
                self.filter_table(self.tab_assets, self.assets_df, self.search_assets.text())
            self.filter_table(self.tab_partners, self.partners_df, self.search_partners.text())
            self.refresh_audit_logs()
            self.reset_matching_state()
            self.btn_optimize.setEnabled(True)
            self.btn_add_asset.setEnabled(True)
            self.btn_edit_asset.setEnabled(True)
            self.btn_del_asset.setEnabled(True)
            self.btn_add_partner.setEnabled(True)
            self.btn_edit_partner.setEnabled(True)
            self.btn_del_partner.setEnabled(True)
            self.tabs.setCurrentIndex(1)
            QMessageBox.information(self, "Import Mitra Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal Import Mitra", msg)

    def populate_table(self, table_widget, df):
        table_widget.clear()
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])
        table_widget.setHorizontalHeaderLabels(df.columns.astype(str))
        
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable) 
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