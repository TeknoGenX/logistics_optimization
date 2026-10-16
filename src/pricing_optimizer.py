import pandas as pd

class PricingOptimizer:
    def __init__(self, profit_margin=1.1):
        # profit_margin dalam bentuk desimal (misal: 1.1 berarti margin 10%, 1.25 berarti 25%)
        self.profit_margin = profit_margin

    def calculate_dynamic_pricing(self, assets_df, custom_margin=None):
        """
        Menghitung harga optimal berbasis data:
        Harga Optimal = Harga Dasar x Skor Lokasi x Indeks Demand x Margin Profit
        """
        optimized_df = assets_df.copy()
        
        # Gunakan custom_margin jika diberikan oleh slider GUI (konversi dari persen ke desimal, misal 15 -> 1.15)
        margin = self.profit_margin if custom_margin is None else (1.0 + (custom_margin / 100.0))
        
        optimized_df['optimal_price'] = (
            optimized_df['base_price'] * 
            optimized_df['location_score'] * 
            optimized_df['demand_index'] * 
            margin
        )
        
        # Pembulatan harga ke ribuan terdekat
        optimized_df['optimal_price'] = optimized_df['optimal_price'].round(-3) 
        return optimized_df