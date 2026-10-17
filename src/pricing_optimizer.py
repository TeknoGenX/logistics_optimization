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
        if assets_df is None:
            return pd.DataFrame(columns=['asset_id', 'asset_type', 'capacity_tons', 'base_price', 'location_score', 'demand_index', 'optimal_price'])

        optimized_df = assets_df.copy()
        
        # Gunakan custom_margin jika diberikan oleh slider GUI (konversi dari persen ke desimal, misal 15 -> 1.15)
        margin = self.profit_margin if custom_margin is None else (1.0 + (custom_margin / 100.0))
        
        if optimized_df.empty:
            optimized_df['optimal_price'] = pd.Series(dtype=float)
            return optimized_df

        base = pd.to_numeric(optimized_df.get('base_price', 0.0), errors='coerce').fillna(0.0)
        loc = pd.to_numeric(optimized_df.get('location_score', 1.0), errors='coerce').fillna(1.0)
        demand = pd.to_numeric(optimized_df.get('demand_index', 1.0), errors='coerce').fillna(1.0)

        optimized_df['optimal_price'] = (base * loc * demand * margin).round(-3)
        return optimized_df