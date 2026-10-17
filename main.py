from src.data_handler import load_assets_data, load_partners_data
from src.pricing_optimizer import PricingOptimizer
from src.partner_matcher import PartnerMatcher
from src.financial_calculator import FinancialAnalyzer

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
    print("-" * 60)

    print("\n[PROSES 3] Ringkasan Eksekutif & KPI Finansial Proyeksi...")
    metrics = FinancialAnalyzer.calculate_metrics(assets_df, optimized_assets, matching_results, partners_df)
    print(f" • Total Harga Dasar Aset   : {FinancialAnalyzer.format_currency(metrics['total_base_revenue'])}")
    print(f" • Total Proyeksi Revenue   : {FinancialAnalyzer.format_currency(metrics['total_optimal_revenue'])}")
    sign = "+" if metrics['revenue_uplift'] >= 0 else ""
    print(f" • Potensi Kenaikan Revenue : {sign}{FinancialAnalyzer.format_currency(metrics['revenue_uplift'])} ({sign}{metrics['uplift_percentage']}%)")
    print(f" • Biaya Operasional (35%)  : {FinancialAnalyzer.format_currency(metrics['total_operational_cost'])}")
    print(f" • Estimasi Net Profit      : {FinancialAnalyzer.format_currency(metrics['net_profit'])} (Margin: {metrics['net_profit_margin_percentage']}%)")
    print(f" • Rasio Aset Terpasangkan  : {metrics['matched_assets_count']} / {metrics['total_assets_count']} ({metrics['matching_ratio_percentage']}%)")
    print(f" • Rata-rata Skor Kualitas  : {metrics['average_match_score']}%")
    print("\n[PROSES 4] Optimasi Alokasi Eksklusif 1-ke-1 (Hungarian Bipartite Matching)...")
    exclusive_assignments = matcher.assign_exclusive_partners(
        optimized_assets, partners_df, objective='score', include_unassigned=True
    )
    print("Hasil Alokasi Eksklusif Aset ke Mitra (Anti Double-Booking):")
    if not exclusive_assignments.empty:
        display_cols = ['asset_id', 'asset_type', 'optimal_price', 'partner_id', 'partner_name', 'match_score', 'deal_price', 'allocation_status']
        print(exclusive_assignments[display_cols].to_string(index=False))
        assign_metrics = FinancialAnalyzer.calculate_assignment_metrics(exclusive_assignments, assets_df)
        print("\nMetrik Alokasi Eksklusif:")
        print(f" • Rasio Aset Teralokasi    : {assign_metrics['total_assigned_count']} / {assign_metrics['total_assets_count']} ({assign_metrics['allocation_ratio_percentage']}%)")
        print(f" • Total Nilai Kesepakatan  : {FinancialAnalyzer.format_currency(assign_metrics['total_deal_value'])}")
        print(f" • Net Profit dari Alokasi  : {FinancialAnalyzer.format_currency(assign_metrics['assigned_net_profit'])} (Margin: {assign_metrics['assigned_net_margin_percentage']}%)")
        print(f" • Rata-rata Skor Alokasi   : {assign_metrics['average_assigned_score']}%")
    else:
        print("Tidak ada aset yang dapat dialokasikan secara eksklusif.")
    print("="*60)

if __name__ == "__main__":
    main()

