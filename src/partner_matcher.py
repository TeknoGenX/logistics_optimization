import pandas as pd

class PartnerMatcher:
    def __init__(self, weight_budget=0.7, weight_reliability=0.3,
                 weight_capacity=0.0, weight_region=0.0,
                 min_score_threshold=50.0,
                 enforce_capacity=False, enforce_region=False):
        self.weight_budget = float(weight_budget)
        self.weight_reliability = float(weight_reliability)
        self.weight_capacity = float(weight_capacity)
        self.weight_region = float(weight_region)
        self.min_score_threshold = float(min_score_threshold)
        self.enforce_capacity = bool(enforce_capacity)
        self.enforce_region = bool(enforce_region)

    def set_config(self, weight_budget=None, weight_reliability=None,
                   weight_capacity=None, weight_region=None,
                   min_score_threshold=None,
                   enforce_capacity=None, enforce_region=None):
        """Memperbarui konfigurasi bobot, threshold, dan validasi constraint algoritma matching."""
        if weight_budget is not None:
            self.weight_budget = float(weight_budget)
        if weight_reliability is not None:
            self.weight_reliability = float(weight_reliability)
        if weight_capacity is not None:
            self.weight_capacity = float(weight_capacity)
        if weight_region is not None:
            self.weight_region = float(weight_region)
        if min_score_threshold is not None:
            self.min_score_threshold = float(min_score_threshold)
        if enforce_capacity is not None:
            self.enforce_capacity = bool(enforce_capacity)
        if enforce_region is not None:
            self.enforce_region = bool(enforce_region)

    def get_config(self):
        """Mengambil konfigurasi bobot, threshold, dan constraint saat ini."""
        return {
            'weight_budget': self.weight_budget,
            'weight_reliability': self.weight_reliability,
            'weight_capacity': self.weight_capacity,
            'weight_region': self.weight_region,
            'min_score_threshold': self.min_score_threshold,
            'enforce_capacity': self.enforce_capacity,
            'enforce_region': self.enforce_region
        }

    @staticmethod
    def _extract_capacity(row, possible_keys):
        """Mengekstrak nilai kapasitas numerik dari baris data."""
        for key in possible_keys:
            if key in row and pd.notna(row[key]):
                try:
                    val = float(row[key])
                    if val > 0:
                        return val
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def _extract_region(row, possible_keys):
        """Mengekstrak nama wilayah yang telah dinormalisasi dari baris data."""
        for key in possible_keys:
            if key in row and pd.notna(row[key]):
                val = str(row[key]).strip().lower()
                if val != "" and val != "nan" and val != "none":
                    return val
        return None

    def match_assets_to_partners(self, optimized_assets_df, partners_df,
                                 weight_budget=None, weight_reliability=None,
                                 weight_capacity=None, weight_region=None,
                                 min_score_threshold=None,
                                 enforce_capacity=None, enforce_region=None,
                                 include_details=False):
        """
        Mencocokkan aset dengan mitra logistik berdasarkan multi-kriteria:
        1. Kesesuaian Finansial (Budget vs Optimal Price)
        2. Reliabilitas Mitra (Track record & SLA)
        3. Kecocokan Kapasitas (Tonase muatan)
        4. Wilayah Operasional (Kesesuaian regional/cakupan logistik)
        """
        matches = []
        base_columns = ['asset_id', 'asset_type', 'optimal_price', 'partner_id', 'partner_name', 'partner_budget', 'match_score']
        columns = list(base_columns)
        if include_details:
            columns.extend(['capacity_fit', 'region_fit'])
        
        if optimized_assets_df is None or optimized_assets_df.empty or partners_df is None or partners_df.empty:
            return pd.DataFrame(columns=columns)

        w_budget = self.weight_budget if weight_budget is None else float(weight_budget)
        w_rel = self.weight_reliability if weight_reliability is None else float(weight_reliability)
        w_cap = self.weight_capacity if weight_capacity is None else float(weight_capacity)
        w_reg = self.weight_region if weight_region is None else float(weight_region)
        threshold = self.min_score_threshold if min_score_threshold is None else float(min_score_threshold)
        enf_cap = self.enforce_capacity if enforce_capacity is None else bool(enforce_capacity)
        enf_reg = self.enforce_region if enforce_region is None else bool(enforce_region)

        total_weight = w_budget + w_rel + w_cap + w_reg
        if total_weight > 0:
            norm_budget = w_budget / total_weight
            norm_rel = w_rel / total_weight
            norm_cap = w_cap / total_weight
            norm_reg = w_reg / total_weight
        else:
            norm_budget, norm_rel, norm_cap, norm_reg = 0.5, 0.5, 0.0, 0.0

        universal_regions = {'', 'all', 'semua', 'semua wilayah', 'nasional', 'any', 'general', 'seluruh indonesia'}

        for _, asset in optimized_assets_df.iterrows():
            for _, partner in partners_df.iterrows():
                asset_type = str(asset.get('asset_type', '')).strip().lower()
                req_type = str(partner.get('req_type', '')).strip().lower()

                if asset_type == req_type and asset_type != "":
                    # 1. Validasi & Kecocokan Kapasitas (Tonase)
                    asset_cap = self._extract_capacity(asset, ['capacity_tons', 'capacity', 'tonnage'])
                    req_cap = self._extract_capacity(partner, ['req_capacity', 'min_capacity', 'capacity_tons', 'capacity'])
                    
                    if req_cap is not None and asset_cap is not None:
                        if asset_cap >= req_cap:
                            capacity_fit = 1.0
                        else:
                            if enf_cap:
                                # Hard constraint: Kapasitas aset tidak mencukupi kebutuhan mitra
                                continue
                            capacity_fit = max(0.0, float(asset_cap) / float(req_cap))
                    else:
                        capacity_fit = 1.0

                    # 2. Validasi & Kesesuaian Wilayah Operasional
                    asset_reg = self._extract_region(asset, ['operating_region', 'region', 'location', 'lokasi', 'wilayah'])
                    partner_reg = self._extract_region(partner, ['operating_region', 'region', 'target_region', 'lokasi', 'wilayah'])

                    is_asset_univ = (asset_reg is None or asset_reg in universal_regions)
                    is_partner_univ = (partner_reg is None or partner_reg in universal_regions)

                    if is_asset_univ or is_partner_univ:
                        region_fit = 1.0
                    elif asset_reg == partner_reg:
                        region_fit = 1.0
                    else:
                        if enf_reg:
                            # Hard constraint: Wilayah operasional tidak berkesesuaian
                            continue
                        region_fit = 0.0

                    # 3. Kesesuaian Finansial (Harga Optimal vs Budget)
                    try:
                        optimal_price = float(asset.get('optimal_price', 0.0))
                    except (ValueError, TypeError):
                        optimal_price = 0.0

                    try:
                        partner_budget = float(partner.get('budget', 0.0))
                    except (ValueError, TypeError):
                        partner_budget = 0.0

                    price_diff = partner_budget - optimal_price
                    
                    if optimal_price <= 0:
                        financial_fit = 1.0 if partner_budget >= 0 else 0.0
                    elif price_diff >= 0:
                        financial_fit = 1.0
                    else:
                        financial_fit = max(0.0, 1.0 - (abs(price_diff) / optimal_price))
                    
                    # 4. Multi-Kriteria Scoring
                    try:
                        rel_val = partner.get('reliability_score', 0.5)
                        partner_rel = float(rel_val) if (rel_val is not None and pd.notna(rel_val)) else 0.5
                    except (ValueError, TypeError):
                        partner_rel = 0.5

                    match_score = (
                        (financial_fit * norm_budget) +
                        (partner_rel * norm_rel) +
                        (capacity_fit * norm_cap) +
                        (region_fit * norm_reg)
                    )
                    match_score = round(match_score * 100, 2)
                    
                    if match_score > threshold:
                        record = {
                            'asset_id': asset.get('asset_id', ''),
                            'asset_type': asset.get('asset_type', ''),
                            'optimal_price': optimal_price,
                            'partner_id': partner.get('partner_id', ''),
                            'partner_name': partner.get('partner_name', partner.get('name', '')),
                            'partner_budget': partner_budget,
                            'match_score': match_score
                        }
                        if include_details:
                            record['capacity_fit'] = round(capacity_fit * 100, 1)
                            record['region_fit'] = round(region_fit * 100, 1)
                        matches.append(record)
                        
        result_df = pd.DataFrame(matches, columns=columns)
        if not result_df.empty:
            result_df = result_df.sort_values(by=['asset_id', 'match_score'], ascending=[True, False])
        return result_df

    @staticmethod
    def _hungarian_pure(cost_matrix):
        """
        Algoritma Kuhn-Munkres (Hungarian Method) murni Python untuk mencari minimum cost matching
        pada matriks biaya (n x m). Mengembalikan (row_ind, col_ind).
        Digunakan sebagai jaminan fallback jika library eksternal (scipy) tidak tersedia.
        """
        n = len(cost_matrix)
        m = len(cost_matrix[0]) if n > 0 else 0
        if n == 0 or m == 0:
            return [], []

        dim = max(n, m)
        cost = [[0.0] * dim for _ in range(dim)]
        for i in range(n):
            for j in range(m):
                cost[i][j] = float(cost_matrix[i][j])

        u = [0.0] * (dim + 1)
        v = [0.0] * (dim + 1)
        p = [0] * (dim + 1)
        way = [0] * (dim + 1)

        for i in range(1, dim + 1):
            p[0] = i
            j0 = 0
            minv = [float('inf')] * (dim + 1)
            used = [False] * (dim + 1)
            while True:
                used[j0] = True
                i0 = p[j0]
                delta = float('inf')
                j1 = 0
                for j in range(1, dim + 1):
                    if not used[j]:
                        cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j
                for j in range(dim + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                j0 = j1
                if p[j0] == 0:
                    break
            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        row_ind = []
        col_ind = []
        for j in range(1, dim + 1):
            if p[j] != 0 and p[j] <= n and (j - 1) < m:
                row_ind.append(p[j] - 1)
                col_ind.append(j - 1)
        pairs = sorted(zip(row_ind, col_ind), key=lambda x: x[0])
        return [p[0] for p in pairs], [p[1] for p in pairs]

    def assign_exclusive_partners(self, optimized_assets_df, partners_df,
                                 objective='score',
                                 method='hungarian',
                                 include_unassigned=False,
                                 weight_budget=None, weight_reliability=None,
                                 weight_capacity=None, weight_region=None,
                                 min_score_threshold=None,
                                 enforce_capacity=None, enforce_region=None,
                                 include_details=False):
        """
        Melakukan alokasi eksklusif 1-ke-1 antara aset dan mitra logistik.
        Setiap aset hanya dialokasikan ke maksimal 1 mitra, dan setiap mitra
        hanya menerima maksimal 1 aset (mencegah bentrok pemakaian / double booking).

        Parameter:
            objective: 'score' (maksimalkan total skor kecocokan),
                       'revenue' (maksimalkan total pendapatan optimal),
                       'deal_value' (maksimalkan total nilai transaksi yang disepakati)
            method: 'hungarian' (Maximum Weight Bipartite Matching - Optimal Global)
                    'greedy' (Heuristik greedy berbasis prioritas bobot tertinggi)
            include_unassigned: Jika True, menyertakan aset yang tidak teralokasi dengan status 'Unallocated'
        """
        base_cols = [
            'asset_id', 'asset_type', 'optimal_price',
            'partner_id', 'partner_name', 'partner_budget',
            'match_score', 'deal_price', 'allocation_status'
        ]
        columns = list(base_cols)
        if include_details:
            columns.extend(['capacity_fit', 'region_fit'])

        if optimized_assets_df is None or optimized_assets_df.empty:
            return pd.DataFrame(columns=columns)

        if partners_df is None or partners_df.empty:
            if include_unassigned:
                unassigned = []
                for _, a in optimized_assets_df.iterrows():
                    rec = {
                        'asset_id': a.get('asset_id', ''),
                        'asset_type': a.get('asset_type', ''),
                        'optimal_price': a.get('optimal_price', 0.0),
                        'partner_id': '-',
                        'partner_name': '(Belum Teralokasi)',
                        'partner_budget': 0.0,
                        'match_score': 0.0,
                        'deal_price': 0.0,
                        'allocation_status': 'Unallocated'
                    }
                    if include_details:
                        rec['capacity_fit'] = 0.0
                        rec['region_fit'] = 0.0
                    unassigned.append(rec)
                return pd.DataFrame(unassigned, columns=columns)
            return pd.DataFrame(columns=columns)

        candidate_matches = self.match_assets_to_partners(
            optimized_assets_df, partners_df,
            weight_budget=weight_budget, weight_reliability=weight_reliability,
            weight_capacity=weight_capacity, weight_region=weight_region,
            min_score_threshold=min_score_threshold,
            enforce_capacity=enforce_capacity, enforce_region=enforce_region,
            include_details=True
        )

        if candidate_matches.empty:
            if include_unassigned:
                unassigned = []
                for _, a in optimized_assets_df.iterrows():
                    rec = {
                        'asset_id': a.get('asset_id', ''),
                        'asset_type': a.get('asset_type', ''),
                        'optimal_price': a.get('optimal_price', 0.0),
                        'partner_id': '-',
                        'partner_name': '(Belum Teralokasi)',
                        'partner_budget': 0.0,
                        'match_score': 0.0,
                        'deal_price': 0.0,
                        'allocation_status': 'Unallocated'
                    }
                    if include_details:
                        rec['capacity_fit'] = 0.0
                        rec['region_fit'] = 0.0
                    unassigned.append(rec)
                return pd.DataFrame(unassigned, columns=columns)
            return pd.DataFrame(columns=columns)

        # Hitung bobot alokasi untuk setiap pasangan kandidat
        candidate_records = candidate_matches.to_dict('records')
        for cand in candidate_records:
            score = float(cand.get('match_score', 0.0))
            optimal_price = float(cand.get('optimal_price', 0.0))
            budget = float(cand.get('partner_budget', 0.0))
            deal_price = round(min(budget, optimal_price), 2)
            cand['deal_price'] = deal_price

            if objective == 'revenue':
                # Prioritaskan pendapatan sewa terbesar; skor sebagai pemecah seri (tie-breaker)
                cand['weight'] = optimal_price + (score * 0.001)
            elif objective == 'deal_value':
                # Prioritaskan nilai transaksi tercapai terbesar
                cand['weight'] = deal_price + (score * 0.001)
            else:
                # Default 'score': prioritaskan kepuasan / skor kecocokan tertinggi
                cand['weight'] = score

        allocated_matches = []
        assigned_asset_ids = set()
        assigned_partner_ids = set()

        if method == 'greedy':
            # Metode Greedy: Urutkan pasangan kandidat dari weight tertinggi
            sorted_candidates = sorted(candidate_records, key=lambda x: x['weight'], reverse=True)
            for cand in sorted_candidates:
                aid = cand['asset_id']
                pid = cand['partner_id']
                if aid not in assigned_asset_ids and pid not in assigned_partner_ids:
                    assigned_asset_ids.add(aid)
                    assigned_partner_ids.add(pid)
                    rec = dict(cand)
                    rec['allocation_status'] = 'Allocated'
                    allocated_matches.append(rec)
        else:
            # Metode Hungarian (Maximum Weight Bipartite Matching)
            unique_assets = list(optimized_assets_df['asset_id'].unique())
            unique_partners = list(partners_df['partner_id'].unique())
            
            asset_idx_map = {aid: idx for idx, aid in enumerate(unique_assets)}
            partner_idx_map = {pid: idx for idx, pid in enumerate(unique_partners)}
            
            n_assets = len(unique_assets)
            n_partners = len(unique_partners)
            
            # Buat matriks biaya n_assets x n_partners
            PENALTY_COST = 1e9
            cost_matrix = [[PENALTY_COST] * n_partners for _ in range(n_assets)]
            candidate_lookup = {}
            
            for cand in candidate_records:
                aid = cand['asset_id']
                pid = cand['partner_id']
                if aid in asset_idx_map and pid in partner_idx_map:
                    a_idx = asset_idx_map[aid]
                    p_idx = partner_idx_map[pid]
                    cost_matrix[a_idx][p_idx] = -float(cand['weight'])
                    candidate_lookup[(a_idx, p_idx)] = cand

            # Jalankan Hungarian Algorithm
            try:
                from scipy.optimize import linear_sum_assignment
                row_ind, col_ind = linear_sum_assignment(cost_matrix)
            except Exception:
                row_ind, col_ind = self._hungarian_pure(cost_matrix)

            for r, c in zip(row_ind, col_ind):
                # Validasi bahwa pasangan bukan edge penalti
                if cost_matrix[r][c] < (PENALTY_COST / 2.0):
                    cand = candidate_lookup.get((r, c))
                    if cand:
                        assigned_asset_ids.add(cand['asset_id'])
                        assigned_partner_ids.add(cand['partner_id'])
                        rec = dict(cand)
                        rec['allocation_status'] = 'Allocated'
                        allocated_matches.append(rec)

        # Jika include_unassigned diaktifkan, tambahkan aset yang tidak teralokasi
        if include_unassigned:
            for _, asset in optimized_assets_df.iterrows():
                aid = asset.get('asset_id')
                if aid not in assigned_asset_ids:
                    rec = {
                        'asset_id': aid,
                        'asset_type': asset.get('asset_type', ''),
                        'optimal_price': asset.get('optimal_price', 0.0),
                        'partner_id': '-',
                        'partner_name': '(Belum Teralokasi)',
                        'partner_budget': 0.0,
                        'match_score': 0.0,
                        'deal_price': 0.0,
                        'allocation_status': 'Unallocated'
                    }
                    if include_details:
                        rec['capacity_fit'] = 0.0
                        rec['region_fit'] = 0.0
                    allocated_matches.append(rec)

        result_df = pd.DataFrame(allocated_matches, columns=columns)
        if not result_df.empty:
            result_df = result_df.sort_values(by=['asset_id'], ascending=[True])
        return result_df

    @staticmethod
    def calculate_assignment_summary(assignment_df, total_assets=None, total_partners=None):
        """Menghitung ringkasan statistik dari hasil alokasi eksklusif 1-ke-1."""
        if assignment_df is None or assignment_df.empty:
            tot_a = total_assets or 0
            tot_p = total_partners or 0
            return {
                'total_assigned': 0,
                'total_revenue': 0.0,
                'total_deal_value': 0.0,
                'average_match_score': 0.0,
                'unassigned_assets': tot_a,
                'unassigned_partners': tot_p,
                'allocation_rate': 0.0
            }
        
        if 'allocation_status' in assignment_df.columns:
            allocated = assignment_df[assignment_df['allocation_status'] == 'Allocated']
        else:
            allocated = assignment_df

        assigned_count = len(allocated)
        tot_assets = total_assets if total_assets is not None else len(assignment_df)
        tot_rev = float(allocated['optimal_price'].sum()) if 'optimal_price' in allocated.columns else 0.0
        tot_deal = float(allocated['deal_price'].sum()) if 'deal_price' in allocated.columns else 0.0
        avg_score = round(float(allocated['match_score'].mean()), 2) if assigned_count > 0 and 'match_score' in allocated.columns else 0.0
        alloc_rate = round((assigned_count / tot_assets) * 100.0, 2) if tot_assets > 0 else 0.0
        
        unassigned_a = max(0, tot_assets - assigned_count)
        unassigned_p = max(0, (total_partners or 0) - assigned_count)
        
        return {
            'total_assigned': assigned_count,
            'total_revenue': tot_rev,
            'total_deal_value': tot_deal,
            'average_match_score': avg_score,
            'unassigned_assets': unassigned_a,
            'unassigned_partners': unassigned_p,
            'allocation_rate': alloc_rate
        }


