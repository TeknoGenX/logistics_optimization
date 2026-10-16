from src.data_handler import load_assets_data, load_partners_data
from src.pricing_optimizer import PricingOptimizer
from src.partner_matcher import PartnerMatcher

def main():
    print("="*60)
    print(" SISTEM OPTIMASI HARGA ASET & SELEKSI MITRA (LOGISTIK)")
    print("="*60)

    assets_df = load_assets_data()
    partners_df = load_partners_data()

    print("\n[PROSES 1] Menghitung Dynamic Pricing Aset...")
    optimizer = PricingOptimizer(profit_margin=1.1)
    optimized_assets = optimizer.calculate_dynamic_pricing(assets_df)

    print("Hasil Penetapan Harga Baru:")
    print(optimized_assets[['asset_id', 'asset_type', 'base_price', 'optimal_price']])
    print("-" * 60)

    print("\n[PROSES 2] Mencari Mitra Terbaik Berdasarkan AI Scoring...")
    matcher = PartnerMatcher()
    matching_results = matcher.match_assets_to_partners(optimized_assets, partners_df)

    print("Hasil Rekomendasi Mitra (Match Score > 50%):")
    if not matching_results.empty:
        print(matching_results.to_string(index=False))
    else:
        print("Tidak ada mitra yang cocok untuk aset saat ini.")
    print("="*60)

if __name__ == "__main__":
    main()
