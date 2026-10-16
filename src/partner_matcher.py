import pandas as pd

class PartnerMatcher:
    def __init__(self):
        pass

    def match_assets_to_partners(self, optimized_assets_df, partners_df):
        matches = []
        for _, asset in optimized_assets_df.iterrows():
            for _, partner in partners_df.iterrows():
                if asset['asset_type'] == partner['req_type']:
                    optimal_price = asset['optimal_price']
                    price_diff = partner['budget'] - optimal_price
                    
                    if optimal_price <= 0:
                        financial_fit = 1.0 if partner['budget'] >= 0 else 0.0
                    elif price_diff >= 0:
                        financial_fit = 1.0
                    else:
                        financial_fit = max(0, 1 - (abs(price_diff) / optimal_price))
                    
                    match_score = (financial_fit * 0.7) + (partner['reliability_score'] * 0.3)
                    match_score = round(match_score * 100, 2)
                    
                    if match_score > 50:
                        matches.append({
                            'asset_id': asset['asset_id'],
                            'asset_type': asset['asset_type'],
                            'optimal_price': asset['optimal_price'],
                            'partner_id': partner['partner_id'],
                            'partner_name': partner['partner_name'],
                            'partner_budget': partner['budget'],
                            'match_score': match_score
                        })
                        
        result_df = pd.DataFrame(matches)
        if not result_df.empty:
            result_df = result_df.sort_values(by=['asset_id', 'match_score'], ascending=[True, False])
        return result_df
