import pandas as pd

class FinancialAnalyzer:
    """
    Modul Analisis Finansial & KPI Proyeksi Pendapatan Logistik.
    Menghitung metrik performa bisnis: Total Proyeksi Revenue,
    Kenaikan Margin Uplift, Rasio Aset Terpasangkan, dan Rata-rata Skor Kualitas Mitra.
    """
    @staticmethod
    def calculate_metrics(assets_df=None, optimized_df=None, matching_df=None, partners_df=None, cost_ratio=0.35):
        ratio = float(cost_ratio) if cost_ratio is not None else 0.35
        metrics = {
            'total_base_revenue': 0.0,
            'total_optimal_revenue': 0.0,
            'revenue_uplift': 0.0,
            'uplift_percentage': 0.0,
            'total_assets_count': 0,
            'matched_assets_count': 0,
            'matching_ratio_percentage': 0.0,
            'average_match_score': 0.0,
            'total_partners_count': 0,
            # Metrik Biaya Operasional & Net Profit
            'cost_ratio_percentage': round(ratio * 100.0, 1),
            'total_operational_cost': 0.0,
            'fuel_cost': 0.0,
            'maintenance_cost': 0.0,
            'depreciation_cost': 0.0,
            'overhead_cost': 0.0,
            'net_profit': 0.0,
            'net_profit_margin_percentage': 0.0,
            'base_net_profit': 0.0,
            'net_profit_uplift': 0.0
        }
        
        # 1. Metrik Aset Dasar
        if assets_df is not None and not assets_df.empty:
            metrics['total_assets_count'] = len(assets_df)
            if 'base_price' in assets_df.columns:
                metrics['total_base_revenue'] = float(pd.to_numeric(assets_df['base_price'], errors='coerce').fillna(0.0).sum())
                
        # 2. Metrik Mitra
        if partners_df is not None and not partners_df.empty:
            metrics['total_partners_count'] = len(partners_df)

        # 3. Metrik Dynamic Pricing (Optimal Revenue & Uplift)
        if optimized_df is not None and not optimized_df.empty:
            if 'optimal_price' in optimized_df.columns:
                metrics['total_optimal_revenue'] = float(pd.to_numeric(optimized_df['optimal_price'], errors='coerce').fillna(0.0).sum())
            if 'base_price' in optimized_df.columns and metrics['total_base_revenue'] == 0:
                metrics['total_base_revenue'] = float(pd.to_numeric(optimized_df['base_price'], errors='coerce').fillna(0.0).sum())

            metrics['revenue_uplift'] = metrics['total_optimal_revenue'] - metrics['total_base_revenue']
            if metrics['total_base_revenue'] > 0:
                metrics['uplift_percentage'] = round(
                    (metrics['revenue_uplift'] / metrics['total_base_revenue']) * 100.0, 2
                )

        # 4. Perhitungan Biaya Operasional & Net Profit
        ref_revenue = metrics['total_optimal_revenue'] if metrics['total_optimal_revenue'] > 0 else metrics['total_base_revenue']
        if ref_revenue > 0:
            metrics['total_operational_cost'] = round(ref_revenue * ratio, 2)
            # Rincian biaya: BBM (15/35), Pemeliharaan (10/35), Depresiasi (5/35), Overhead (5/35)
            metrics['fuel_cost'] = round(ref_revenue * (ratio * (15.0 / 35.0)), 2)
            metrics['maintenance_cost'] = round(ref_revenue * (ratio * (10.0 / 35.0)), 2)
            metrics['depreciation_cost'] = round(ref_revenue * (ratio * (5.0 / 35.0)), 2)
            metrics['overhead_cost'] = round(ref_revenue * (ratio * (5.0 / 35.0)), 2)
            
            metrics['net_profit'] = round(ref_revenue - metrics['total_operational_cost'], 2)
            metrics['net_profit_margin_percentage'] = round(
                (metrics['net_profit'] / ref_revenue) * 100.0, 2
            )

        if metrics['total_base_revenue'] > 0:
            base_cost = metrics['total_base_revenue'] * ratio
            metrics['base_net_profit'] = round(metrics['total_base_revenue'] - base_cost, 2)
            if metrics['total_optimal_revenue'] > 0:
                metrics['net_profit_uplift'] = round(metrics['net_profit'] - metrics['base_net_profit'], 2)

        # 5. Metrik Partner Matching (Keterisian & Skor Kualitas)
        if matching_df is not None and not matching_df.empty:
            if 'asset_id' in matching_df.columns:
                unique_matched = matching_df['asset_id'].nunique()
                metrics['matched_assets_count'] = int(unique_matched)
                if metrics['total_assets_count'] > 0:
                    metrics['matching_ratio_percentage'] = round(
                        (unique_matched / metrics['total_assets_count']) * 100.0, 2
                    )
            if 'match_score' in matching_df.columns:
                valid_scores = pd.to_numeric(matching_df['match_score'], errors='coerce').dropna()
                metrics['average_match_score'] = round(float(valid_scores.mean()), 2) if not valid_scores.empty else 0.0

        return metrics

    @staticmethod
    def calculate_operational_breakdown(revenue, cost_ratio=0.35):
        """Menghitung rincian biaya operasional berdasarkan estimasi rasio biaya."""
        ratio = float(cost_ratio) if cost_ratio is not None else 0.35
        total_cost = round(revenue * ratio, 2)
        return {
            'total_cost': total_cost,
            'fuel_cost': round(revenue * (ratio * (15.0 / 35.0)), 2),
            'maintenance_cost': round(revenue * (ratio * (10.0 / 35.0)), 2),
            'depreciation_cost': round(revenue * (ratio * (5.0 / 35.0)), 2),
            'overhead_cost': round(revenue * (ratio * (5.0 / 35.0)), 2),
            'net_profit': round(revenue - total_cost, 2),
            'net_margin_pct': round(((revenue - total_cost) / revenue) * 100.0, 2) if revenue > 0 else 0.0
        }

    @staticmethod
    def calculate_assignment_metrics(assignment_df, assets_df=None, cost_ratio=0.35):
        """
        Menghitung metrik finansial dan utilisasi khusus untuk hasil alokasi eksklusif 1-ke-1.
        Mencakup pendapatan terealisasi (deal value), biaya operasional, laba bersih,
        dan rasio utilisasi aset alokasi.
        """
        ratio = float(cost_ratio) if cost_ratio is not None else 0.35
        metrics = {
            'total_assets_count': len(assets_df) if (assets_df is not None and not assets_df.empty) else 0,
            'total_assigned_count': 0,
            'allocation_ratio_percentage': 0.0,
            'assigned_optimal_revenue': 0.0,
            'total_deal_value': 0.0,
            'assigned_operational_cost': 0.0,
            'assigned_net_profit': 0.0,
            'assigned_net_margin_percentage': 0.0,
            'average_assigned_score': 0.0,
            'unassigned_count': 0
        }

        if assignment_df is None or assignment_df.empty:
            metrics['unassigned_count'] = metrics['total_assets_count']
            return metrics

        if 'allocation_status' in assignment_df.columns:
            allocated = assignment_df[assignment_df['allocation_status'] == 'Allocated']
        else:
            allocated = assignment_df

        assigned_cnt = len(allocated)
        metrics['total_assigned_count'] = assigned_cnt
        if metrics['total_assets_count'] == 0:
            metrics['total_assets_count'] = len(assignment_df)

        if metrics['total_assets_count'] > 0:
            metrics['allocation_ratio_percentage'] = round((assigned_cnt / metrics['total_assets_count']) * 100.0, 2)
            metrics['unassigned_count'] = max(0, metrics['total_assets_count'] - assigned_cnt)

        if 'optimal_price' in allocated.columns:
            metrics['assigned_optimal_revenue'] = float(allocated['optimal_price'].sum())

        if 'deal_price' in allocated.columns:
            metrics['total_deal_value'] = float(allocated['deal_price'].sum())
        else:
            metrics['total_deal_value'] = metrics['assigned_optimal_revenue']

        if 'match_score' in allocated.columns and assigned_cnt > 0:
            metrics['average_assigned_score'] = round(float(allocated['match_score'].mean()), 2)

        deal_val = metrics['total_deal_value']
        if deal_val > 0:
            metrics['assigned_operational_cost'] = round(deal_val * ratio, 2)
            metrics['assigned_net_profit'] = round(deal_val - metrics['assigned_operational_cost'], 2)
            metrics['assigned_net_margin_percentage'] = round(
                (metrics['assigned_net_profit'] / deal_val) * 100.0, 2
            )

        return metrics

    @staticmethod
    def format_currency(amount):
        """Format angka ke dalam format mata uang Rupiah IDR yang rapi."""
        if amount is None or amount == 0:
            return "Rp 0"
        return f"Rp {amount:,.0f}".replace(",", ".")

