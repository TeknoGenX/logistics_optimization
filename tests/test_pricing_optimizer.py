import unittest
import pandas as pd
from src.pricing_optimizer import PricingOptimizer

class TestPricingOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = PricingOptimizer(profit_margin=1.1)
        self.sample_assets = pd.DataFrame([
            {
                'asset_id': 'AST-001',
                'asset_type': 'Warehouse',
                'capacity_tons': 5000,
                'base_price': 10000000.0,
                'location_score': 0.9,
                'demand_index': 1.2
            },
            {
                'asset_id': 'AST-002',
                'asset_type': 'Truck',
                'capacity_tons': 20,
                'base_price': 2500000.0,
                'location_score': 0.7,
                'demand_index': 1.0
            }
        ])

    def test_calculate_dynamic_pricing_default_margin(self):
        """Uji perhitungan dynamic pricing dengan margin default (10% / 1.1)."""
        result = self.optimizer.calculate_dynamic_pricing(self.sample_assets)
        self.assertIn('optimal_price', result.columns)
        self.assertEqual(len(result), 2)

        # Perhitungan manual: 10,000,000 * 0.9 * 1.2 * 1.1 = 11,880,000
        expected_ast1 = round(10000000.0 * 0.9 * 1.2 * 1.1, -3)
        self.assertEqual(result.loc[result['asset_id'] == 'AST-001', 'optimal_price'].iloc[0], expected_ast1)

        # Perhitungan manual: 2,500,000 * 0.7 * 1.0 * 1.1 = 1,925,000
        expected_ast2 = round(2500000.0 * 0.7 * 1.0 * 1.1, -3)
        self.assertEqual(result.loc[result['asset_id'] == 'AST-002', 'optimal_price'].iloc[0], expected_ast2)

    def test_calculate_dynamic_pricing_custom_margin(self):
        """Uji perhitungan dynamic pricing dengan custom margin (misal 20% dari slider)."""
        result = self.optimizer.calculate_dynamic_pricing(self.sample_assets, custom_margin=20)
        # Margin 20% -> 1.0 + (20 / 100) = 1.20
        # 10,000,000 * 0.9 * 1.2 * 1.20 = 12,960,000
        expected_ast1 = round(10000000.0 * 0.9 * 1.2 * 1.2, -3)
        self.assertEqual(result.loc[result['asset_id'] == 'AST-001', 'optimal_price'].iloc[0], expected_ast1)

    def test_calculate_dynamic_pricing_zero_margin(self):
        """Uji margin 0% (tidak ada penambahan margin keuntungan)."""
        result = self.optimizer.calculate_dynamic_pricing(self.sample_assets, custom_margin=0)
        # Margin 0% -> 1.0 + 0 = 1.0
        expected_ast1 = round(10000000.0 * 0.9 * 1.2 * 1.0, -3)
        self.assertEqual(result.loc[result['asset_id'] == 'AST-001', 'optimal_price'].iloc[0], expected_ast1)

    def test_empty_dataframe(self):
        """Uji penanganan DataFrame aset kosong."""
        empty_df = pd.DataFrame(columns=['asset_id', 'asset_type', 'base_price', 'location_score', 'demand_index'])
        result = self.optimizer.calculate_dynamic_pricing(empty_df)
        self.assertIn('optimal_price', result.columns)
        self.assertTrue(result.empty)

    def test_zero_base_price(self):
        """Uji jika base_price bernilai 0."""
        zero_df = pd.DataFrame([{
            'asset_id': 'AST-999',
            'asset_type': 'Truck',
            'base_price': 0.0,
            'location_score': 0.8,
            'demand_index': 1.0
        }])
        result = self.optimizer.calculate_dynamic_pricing(zero_df)
        self.assertEqual(result['optimal_price'].iloc[0], 0.0)

    def test_none_dataframe_guard(self):
        """Uji penanganan jika parameter assets_df bernilai None."""
        result = self.optimizer.calculate_dynamic_pricing(None)
        self.assertIn('optimal_price', result.columns)
        self.assertTrue(result.empty)

    def test_string_and_missing_values_coercion(self):
        """Uji konversi tipe data otomatis jika data berupa string atau ada kolom hilang."""
        string_df = pd.DataFrame([{
            'asset_id': 'AST-STR',
            'asset_type': 'Warehouse',
            'base_price': '10000000',
            'location_score': '0.9',
            'demand_index': '1.2'
        }])
        result = self.optimizer.calculate_dynamic_pricing(string_df)
        self.assertEqual(result['optimal_price'].iloc[0], 11880000.0)

if __name__ == '__main__':
    unittest.main()

