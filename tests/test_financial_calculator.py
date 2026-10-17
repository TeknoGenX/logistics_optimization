import unittest
import pandas as pd
from src.financial_calculator import FinancialAnalyzer

class TestFinancialAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_assets = pd.DataFrame([
            {'asset_id': 'AST-001', 'base_price': 10000000.0},
            {'asset_id': 'AST-002', 'base_price': 2500000.0},
            {'asset_id': 'AST-003', 'base_price': 15000000.0}
        ])
        self.sample_optimized = pd.DataFrame([
            {'asset_id': 'AST-001', 'base_price': 10000000.0, 'optimal_price': 12000000.0},
            {'asset_id': 'AST-002', 'base_price': 2500000.0, 'optimal_price': 3000000.0},
            {'asset_id': 'AST-003', 'base_price': 15000000.0, 'optimal_price': 18000000.0}
        ])
        self.sample_matches = pd.DataFrame([
            {'asset_id': 'AST-001', 'match_score': 90.0},
            {'asset_id': 'AST-002', 'match_score': 80.0}
        ])
        self.sample_partners = pd.DataFrame([
            {'partner_id': 'PTN-01'}, {'partner_id': 'PTN-02'}, {'partner_id': 'PTN-03'}
        ])

    def test_calculate_metrics_normal(self):
        """Uji perhitungan metrik finansial normal."""
        metrics = FinancialAnalyzer.calculate_metrics(
            assets_df=self.sample_assets,
            optimized_df=self.sample_optimized,
            matching_df=self.sample_matches,
            partners_df=self.sample_partners
        )

        # Base: 10M + 2.5M + 15M = 27.5M
        self.assertEqual(metrics['total_base_revenue'], 27500000.0)
        # Optimal: 12M + 3M + 18M = 33M
        self.assertEqual(metrics['total_optimal_revenue'], 33000000.0)
        # Uplift: 33M - 27.5M = 5.5M
        self.assertEqual(metrics['revenue_uplift'], 5500000.0)
        # Uplift %: (5.5M / 27.5M) * 100 = 20.0%
        self.assertEqual(metrics['uplift_percentage'], 20.0)
        # Matched assets: 2 dari 3 aset = 66.67%
        self.assertEqual(metrics['matched_assets_count'], 2)
        self.assertEqual(metrics['total_assets_count'], 3)
        self.assertEqual(metrics['matching_ratio_percentage'], 66.67)
        # Average score: (90 + 80) / 2 = 85.0%
        self.assertEqual(metrics['average_match_score'], 85.0)
        self.assertEqual(metrics['total_partners_count'], 3)

    def test_calculate_metrics_empty(self):
        """Uji perhitungan metrik dengan DataFrame kosong/None."""
        metrics = FinancialAnalyzer.calculate_metrics(None, None, None, None)
        self.assertEqual(metrics['total_base_revenue'], 0.0)
        self.assertEqual(metrics['total_optimal_revenue'], 0.0)
        self.assertEqual(metrics['revenue_uplift'], 0.0)
        self.assertEqual(metrics['uplift_percentage'], 0.0)
        self.assertEqual(metrics['total_assets_count'], 0)
        self.assertEqual(metrics['matched_assets_count'], 0)
        self.assertEqual(metrics['matching_ratio_percentage'], 0.0)
        self.assertEqual(metrics['average_match_score'], 0.0)

    def test_zero_base_revenue_division_guard(self):
        """Pastikan tidak terjadi ZeroDivisionError jika total_base_revenue adalah 0."""
        zero_assets = pd.DataFrame([{'asset_id': 'A1', 'base_price': 0.0}])
        zero_opt = pd.DataFrame([{'asset_id': 'A1', 'base_price': 0.0, 'optimal_price': 1000.0}])
        metrics = FinancialAnalyzer.calculate_metrics(zero_assets, zero_opt)
        self.assertEqual(metrics['total_base_revenue'], 0.0)
        self.assertEqual(metrics['total_optimal_revenue'], 1000.0)
        self.assertEqual(metrics['uplift_percentage'], 0.0)

    def test_format_currency(self):
        """Uji pemformatan nominal mata uang Rupiah IDR."""
        self.assertEqual(FinancialAnalyzer.format_currency(12500000), "Rp 12.500.000")
        self.assertEqual(FinancialAnalyzer.format_currency(0), "Rp 0")
        self.assertEqual(FinancialAnalyzer.format_currency(None), "Rp 0")

    def test_operational_cost_and_net_profit_calculation(self):
        """Uji perhitungan biaya operasional dan laba bersih (net profit)."""
        metrics = FinancialAnalyzer.calculate_metrics(
            assets_df=self.sample_assets,
            optimized_df=self.sample_optimized,
            matching_df=self.sample_matches,
            partners_df=self.sample_partners,
            cost_ratio=0.35
        )
        # Optimal revenue = 33,000,000
        # Total cost = 33M * 0.35 = 11,550,000
        self.assertEqual(metrics['total_operational_cost'], 11550000.0)
        # Net profit = 33M - 11.55M = 21,450,000
        self.assertEqual(metrics['net_profit'], 21450000.0)
        # Net margin % = (21.45M / 33M) * 100 = 65.0%
        self.assertEqual(metrics['net_profit_margin_percentage'], 65.0)

        # Uji dengan custom cost ratio (40%)
        metrics_40 = FinancialAnalyzer.calculate_metrics(
            assets_df=self.sample_assets,
            optimized_df=self.sample_optimized,
            cost_ratio=0.40
        )
        self.assertEqual(metrics_40['total_operational_cost'], 13200000.0)
        self.assertEqual(metrics_40['net_profit'], 19800000.0)
        self.assertEqual(metrics_40['net_profit_margin_percentage'], 60.0)

    def test_calculate_operational_breakdown(self):
        """Uji rincian komponen biaya operasional."""
        breakdown = FinancialAnalyzer.calculate_operational_breakdown(10000000, cost_ratio=0.35)
        self.assertEqual(breakdown['total_cost'], 3500000.0)
        self.assertEqual(breakdown['fuel_cost'], 1500000.0)
        self.assertEqual(breakdown['maintenance_cost'], 1000000.0)
        self.assertEqual(breakdown['depreciation_cost'], 500000.0)
        self.assertEqual(breakdown['overhead_cost'], 500000.0)
        self.assertEqual(breakdown['net_profit'], 6500000.0)
        self.assertEqual(breakdown['net_margin_pct'], 65.0)

    def test_calculate_assignment_metrics(self):
        """Uji perhitungan metrik finansial untuk alokasi eksklusif 1-ke-1."""
        sample_assignment = pd.DataFrame([
            {
                'asset_id': 'AST-001',
                'optimal_price': 12000000.0,
                'deal_price': 11500000.0,
                'match_score': 95.0,
                'allocation_status': 'Allocated'
            },
            {
                'asset_id': 'AST-002',
                'optimal_price': 3000000.0,
                'deal_price': 2000000.0,
                'match_score': 85.0,
                'allocation_status': 'Allocated'
            },
            {
                'asset_id': 'AST-003',
                'optimal_price': 18000000.0,
                'deal_price': 0.0,
                'match_score': 0.0,
                'allocation_status': 'Unallocated'
            }
        ])
        metrics = FinancialAnalyzer.calculate_assignment_metrics(sample_assignment, self.sample_assets, cost_ratio=0.35)
        self.assertEqual(metrics['total_assets_count'], 3)
        self.assertEqual(metrics['total_assigned_count'], 2)
        self.assertEqual(metrics['unassigned_count'], 1)
        self.assertEqual(metrics['allocation_ratio_percentage'], 66.67)
        # Total deal value = 11.5M + 2.0M = 13.5M
        self.assertEqual(metrics['total_deal_value'], 13500000.0)
        # Cost = 13.5M * 0.35 = 4,725,000
        self.assertEqual(metrics['assigned_operational_cost'], 4725000.0)
        # Net profit = 13.5M - 4.725M = 8,775,000
        self.assertEqual(metrics['assigned_net_profit'], 8775000.0)
        self.assertEqual(metrics['average_assigned_score'], 90.0)

    def test_numeric_coercion_prevents_string_concatenation(self):
        """Pastikan kolom harga bertipe string dijumlahkan secara numerik, bukan konkatenasi teks."""
        string_assets = pd.DataFrame([
            {'asset_id': 'A1', 'base_price': '1000'},
            {'asset_id': 'A2', 'base_price': '2000'}
        ])
        metrics = FinancialAnalyzer.calculate_metrics(assets_df=string_assets)
        self.assertEqual(metrics['total_base_revenue'], 3000.0)

if __name__ == '__main__':
    unittest.main()


