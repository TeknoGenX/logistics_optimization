import unittest
import pandas as pd
from src.partner_matcher import PartnerMatcher

class TestPartnerMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = PartnerMatcher()
        self.optimized_assets = pd.DataFrame([
            {
                'asset_id': 'AST-001',
                'asset_type': 'Warehouse',
                'base_price': 10000000.0,
                'optimal_price': 11880000.0
            },
            {
                'asset_id': 'AST-002',
                'asset_type': 'Truck',
                'base_price': 2500000.0,
                'optimal_price': 1925000.0
            }
        ])
        self.partners = pd.DataFrame([
            {
                'partner_id': 'PTN-101',
                'partner_name': 'Logistik Cepat',
                'req_type': 'Warehouse',
                'budget': 11500000.0,
                'reliability_score': 0.95
            },
            {
                'partner_id': 'PTN-102',
                'partner_name': 'Trans Nusantara',
                'req_type': 'Truck',
                'budget': 2000000.0,
                'reliability_score': 0.80
            },
            {
                'partner_id': 'PTN-999',
                'partner_name': 'Mitra Rendah',
                'req_type': 'Warehouse',
                'budget': 1000000.0,
                'reliability_score': 0.10
            }
        ])

    def test_matching_success_and_threshold(self):
        """Uji kecocokan tipe aset dan filter ambang batas match score > 50%."""
        results = self.matcher.match_assets_to_partners(self.optimized_assets, self.partners)
        self.assertFalse(results.empty)

        # Pastikan semua skor di atas 50%
        self.assertTrue((results['match_score'] > 50).all())

        # Pastikan PTN-999 yang skornya rendah tidak masuk ke dalam hasil rekomendasi
        self.assertNotIn('PTN-999', results['partner_id'].values)

        # Pastikan PTN-101 dan PTN-102 masuk
        self.assertIn('PTN-101', results['partner_id'].values)
        self.assertIn('PTN-102', results['partner_id'].values)

    def test_financial_fit_calculation(self):
        """Uji perhitungan financial fit ketika budget >= optimal_price dan sebaliknya."""
        results = self.matcher.match_assets_to_partners(self.optimized_assets, self.partners)
        
        # PTN-102: budget 2,000,000 >= optimal 1,925,000 -> financial_fit = 1.0
        # match_score = (1.0 * 0.7) + (0.80 * 0.3) = 0.70 + 0.24 = 0.94 -> 94.00%
        ptn_102 = results[results['partner_id'] == 'PTN-102'].iloc[0]
        self.assertEqual(ptn_102['match_score'], 94.00)

        # PTN-101: budget 11,500,000 < optimal 11,880,000
        # price_diff = -380,000
        # financial_fit = 1 - (380,000 / 11,880,000) = 0.9679966...
        # match_score = (financial_fit * 0.7) + (0.95 * 0.3) = 0.677597 + 0.285 = 0.962597 -> 96.26%
        ptn_101 = results[results['partner_id'] == 'PTN-101'].iloc[0]
        self.assertEqual(ptn_101['match_score'], 96.26)

    def test_sorting_order(self):
        """Uji apakah hasil diurutkan berdasarkan asset_id ASC dan match_score DESC."""
        # Tambah mitra gudang kedua dengan skor lebih tinggi
        more_partners = self.partners.copy()
        new_partner = pd.DataFrame([{
            'partner_id': 'PTN-104',
            'partner_name': 'Super Mitra',
            'req_type': 'Warehouse',
            'budget': 15000000.0,  # budget tinggi
            'reliability_score': 0.99
        }])
        more_partners = pd.concat([more_partners, new_partner], ignore_index=True)
        results = self.matcher.match_assets_to_partners(self.optimized_assets, more_partners)
        
        # Untuk AST-001, PTN-104 harus berada di atas PTN-101
        ast1_matches = results[results['asset_id'] == 'AST-001']
        self.assertEqual(ast1_matches.iloc[0]['partner_id'], 'PTN-104')

    def test_zero_optimal_price(self):
        """Uji penanganan edge case jika optimal_price bernilai 0 (tidak boleh ZeroDivisionError)."""
        zero_assets = pd.DataFrame([{
            'asset_id': 'AST-FREE',
            'asset_type': 'Truck',
            'optimal_price': 0.0
        }])
        results = self.matcher.match_assets_to_partners(zero_assets, self.partners)
        self.assertFalse(results.empty)
        truck_match = results[results['asset_id'] == 'AST-FREE'].iloc[0]
        # financial_fit = 1.0 karena budget partner >= 0
        self.assertEqual(truck_match['match_score'], 94.00)

    def test_case_insensitive_and_whitespace_matching(self):
        """Uji kecocokan tipe aset dengan perbedaan huruf kapital dan spasi liar."""
        messy_assets = pd.DataFrame([{
            'asset_id': 'AST-MESSY',
            'asset_type': ' warehouse  ',
            'optimal_price': 10000000.0
        }])
        messy_partners = pd.DataFrame([{
            'partner_id': 'PTN-MESSY',
            'partner_name': 'Mitra Kapital',
            'req_type': 'WAREHOUSE',
            'budget': 10000000.0,
            'reliability_score': 0.9
        }])
        results = self.matcher.match_assets_to_partners(messy_assets, messy_partners)
        self.assertFalse(results.empty)
        self.assertEqual(len(results), 1)
        self.assertEqual(results.iloc[0]['partner_id'], 'PTN-MESSY')

    def test_empty_result_columns_integrity(self):
        """Pastikan jika tidak ada mitra yang cocok, skema kolom DataFrame tetap utuh."""
        res = self.matcher.match_assets_to_partners(pd.DataFrame(), pd.DataFrame())
        expected_cols = ['asset_id', 'asset_type', 'optimal_price', 'partner_id', 'partner_name', 'partner_budget', 'match_score']
        self.assertEqual(list(res.columns), expected_cols)

    def test_config_get_and_set(self):
        """Uji getter dan setter konfigurasi bobot dan ambang batas."""
        cfg = self.matcher.get_config()
        self.assertEqual(cfg['weight_budget'], 0.7)
        self.assertEqual(cfg['weight_reliability'], 0.3)
        self.assertEqual(cfg['min_score_threshold'], 50.0)

        self.matcher.set_config(weight_budget=0.6, weight_reliability=0.4, min_score_threshold=60.0)
        updated = self.matcher.get_config()
        self.assertEqual(updated['weight_budget'], 0.6)
        self.assertEqual(updated['weight_reliability'], 0.4)
        self.assertEqual(updated['min_score_threshold'], 60.0)

    def test_custom_weights_effect(self):
        """Uji perhitungan skor kecocokan saat bobot kustom diterapkan (misal 100% reputasi)."""
        # Dengan 100% reliabilitas: bobot budget = 0, reliability = 1.0
        # PTN-102 reliability_score = 0.80 -> match_score harus 80.0
        results = self.matcher.match_assets_to_partners(
            self.optimized_assets, self.partners,
            weight_budget=0.0, weight_reliability=1.0, min_score_threshold=50.0
        )
        ptn_102 = results[results['partner_id'] == 'PTN-102'].iloc[0]
        self.assertEqual(ptn_102['match_score'], 80.0)

    def test_custom_threshold_filtering(self):
        """Uji filter ambang batas threshold dinamis (misal threshold 95%)."""
        # Standar (threshold 50%): PTN-101 (96.26%) dan PTN-102 (94.00%) lolos
        # Jika threshold dinaikkan ke 95%: hanya PTN-101 yang lolos
        results_high = self.matcher.match_assets_to_partners(
            self.optimized_assets, self.partners,
            min_score_threshold=95.0
        )
        self.assertEqual(len(results_high), 1)
        self.assertEqual(results_high.iloc[0]['partner_id'], 'PTN-101')

    def test_exclusive_assignment_prevents_double_booking(self):
        """Uji alokasi eksklusif 1-ke-1 mencegah double-booking pada aset dan mitra."""
        # Tambah mitra gudang kedua (PTN-104) yang juga memperebutkan AST-001 (Warehouse)
        competing_partners = self.partners.copy()
        extra_partner = pd.DataFrame([{
            'partner_id': 'PTN-104',
            'partner_name': 'Agro Makmur',
            'req_type': 'Warehouse',
            'budget': 10500000.0,
            'reliability_score': 0.85
        }])
        competing_partners = pd.concat([competing_partners, extra_partner], ignore_index=True)

        assigned = self.matcher.assign_exclusive_partners(self.optimized_assets, competing_partners)
        self.assertFalse(assigned.empty)

        # Pastikan tidak ada asset_id duplikat
        self.assertEqual(len(assigned['asset_id']), assigned['asset_id'].nunique())
        # Pastikan tidak ada partner_id duplikat
        allocated = assigned[assigned['allocation_status'] == 'Allocated']
        self.assertEqual(len(allocated['partner_id']), allocated['partner_id'].nunique())

        # AST-001 harus dialokasikan ke PTN-101 (skor 96.26%) bukan PTN-104 (skor lebih rendah)
        ast1 = assigned[assigned['asset_id'] == 'AST-001'].iloc[0]
        self.assertEqual(ast1['partner_id'], 'PTN-101')
        self.assertEqual(ast1['allocation_status'], 'Allocated')

    def test_exclusive_assignment_pure_hungarian_fallback(self):
        """Uji algoritma _hungarian_pure menghasilkan indeks optimal yang konsisten."""
        # Matriks biaya 2x2
        cost_matrix = [
            [-90.0, -80.0],
            [-95.0, -70.0]
        ]
        row_ind, col_ind = self.matcher._hungarian_pure(cost_matrix)
        self.assertEqual(row_ind, [0, 1])
        self.assertEqual(col_ind, [1, 0])

    def test_exclusive_assignment_objectives(self):
        """Uji alokasi eksklusif dengan objektif yang berbeda (score vs revenue vs deal_value)."""
        assigned_score = self.matcher.assign_exclusive_partners(
            self.optimized_assets, self.partners, objective='score'
        )
        self.assertIn('deal_price', assigned_score.columns)
        self.assertIn('allocation_status', assigned_score.columns)
        self.assertTrue((assigned_score['allocation_status'] == 'Allocated').all())

        assigned_rev = self.matcher.assign_exclusive_partners(
            self.optimized_assets, self.partners, objective='revenue'
        )
        self.assertEqual(len(assigned_rev), 2)

        assigned_deal = self.matcher.assign_exclusive_partners(
            self.optimized_assets, self.partners, objective='deal_value'
        )
        self.assertEqual(len(assigned_deal), 2)

    def test_exclusive_assignment_include_unassigned(self):
        """Uji opsi include_unassigned=True untuk menyertakan aset yang tidak memiliki mitra cocok."""
        extra_assets = pd.concat([
            self.optimized_assets,
            pd.DataFrame([{
                'asset_id': 'AST-AIR',
                'asset_type': 'Plane',
                'base_price': 100000000.0,
                'optimal_price': 120000000.0
            }])
        ], ignore_index=True)

        assigned = self.matcher.assign_exclusive_partners(
            extra_assets, self.partners, include_unassigned=True
        )
        self.assertEqual(len(assigned), 3)
        unallocated = assigned[assigned['asset_id'] == 'AST-AIR'].iloc[0]
        self.assertEqual(unallocated['allocation_status'], 'Unallocated')
        self.assertEqual(unallocated['partner_id'], '-')

    def test_exclusive_assignment_greedy_method(self):
        """Uji alokasi eksklusif menggunakan metode greedy heuristik."""
        assigned = self.matcher.assign_exclusive_partners(
            self.optimized_assets, self.partners, method='greedy'
        )
        self.assertFalse(assigned.empty)
        self.assertEqual(len(assigned), 2)

    def test_assignment_summary_calculation(self):
        """Uji perhitungan ringkasan alokasi eksklusif (calculate_assignment_summary)."""
        assigned = self.matcher.assign_exclusive_partners(
            self.optimized_assets, self.partners, include_unassigned=True
        )
        summary = self.matcher.calculate_assignment_summary(assigned, total_assets=2, total_partners=3)
        self.assertEqual(summary['total_assigned'], 2)
        self.assertEqual(summary['allocation_rate'], 100.0)
        self.assertEqual(summary['unassigned_partners'], 1)
        self.assertGreater(summary['total_deal_value'], 0)

    def test_dirty_data_handling(self):
        """Uji keandalan saat data mitra/aset berisi string pada kolom numerik atau nilai None."""
        dirty_assets = pd.DataFrame([{
            'asset_id': 'AST-DIRTY',
            'asset_type': 'Truck',
            'optimal_price': '2000000'
        }])
        dirty_partners = pd.DataFrame([{
            'partner_id': 'PTN-DIRTY',
            'partner_name': 'Mitra String',
            'req_type': 'Truck',
            'budget': '2500000',
            'reliability_score': None
        }])
        res = self.matcher.match_assets_to_partners(dirty_assets, dirty_partners)
        self.assertFalse(res.empty)
        self.assertEqual(res.iloc[0]['partner_id'], 'PTN-DIRTY')

        assigned = self.matcher.assign_exclusive_partners(dirty_assets, dirty_partners)
        self.assertFalse(assigned.empty)
        self.assertEqual(assigned.iloc[0]['partner_id'], 'PTN-DIRTY')

if __name__ == '__main__':
    unittest.main()


