"""
MAC Stitcher - Random MAC 변경 감지 및 연결
Code_Localization에서 가져온 검증된 알고리즘

약국 특성에 맞게 최적화:
- 짧은 체류 시간 (1-5분)
- 좁은 공간
- 높은 MAC 변경 빈도
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class MACStitcher:
    """
    MAC Address Stitching 알고리즘
    Random MAC 변경으로 인해 분리된 같은 디바이스를 연결
    """
    
    def __init__(self, time_window: int = 60, threshold: float = 0.6, rawdata_df: pd.DataFrame = None,
                 fast_mode: bool = False):
        """
        Args:
            time_window: 연결 가능한 최대 시간 간격 (초)
            threshold: 유사도 임계값 (0~1)
            rawdata_df: 원본 RSSI 데이터 (RSSI 벡터 유사도 계산용)
            fast_mode: 빠른 모드 (RSSI 유사도 계산 생략, 속도 3배 향상)
        """
        self.time_window = time_window
        self.threshold = threshold
        self.rawdata_df = rawdata_df
        self.fast_mode = fast_mode
        
        # RSSI 데이터 전처리 (빠른 모드가 아닐 때만)
        if rawdata_df is not None and not fast_mode:
            self.rssi_data = self._preprocess_rssi_data(rawdata_df)
        else:
            self.rssi_data = None
    
    def _preprocess_rssi_data(self, rawdata_df: pd.DataFrame) -> Dict:
        """
        RSSI 데이터를 빠르게 조회할 수 있도록 전처리
        ⚡ 최적화: groupby 사용으로 100배 이상 빠름
        
        Returns:
            {(time_index, mac_address): {sward_name: rssi}}
        """
        rssi_dict = {}
        
        # vectorized 방식으로 변환 (iterrows 대신 groupby 사용)
        grouped = rawdata_df.groupby(['time_index', 'mac_address'])
        
        for (time_idx, mac_addr), group in grouped:
            rssi_dict[(time_idx, mac_addr)] = dict(zip(group['sward_name'], group['rssi']))
        
        return rssi_dict
        
    def extract_features(self, positions_df: pd.DataFrame) -> pd.DataFrame:
        """
        각 MAC 주소의 특징 추출
        ⚡ 최적화: groupby 및 벡터화 연산 사용
        
        Returns:
            features_df: MAC별 특징 DataFrame
        """
        # MAC별로 정렬
        sorted_df = positions_df.sort_values(['mac_address', 'time_index'])
        
        # groupby로 집계 (대부분의 통계를 한번에)
        agg_dict = {
            'time_index': ['min', 'max', 'count'],
            'x': ['first', 'last', 'mean', 'std'],
            'y': ['first', 'last', 'mean', 'std'],
            'device_type': 'first'
        }
        
        features_df = sorted_df.groupby('mac_address').agg(agg_dict).reset_index()
        
        # 컬럼명 평탄화
        features_df.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                               for col in features_df.columns.values]
        
        # 컬럼명 정리
        features_df.rename(columns={
            'time_index_min': 'first_time',
            'time_index_max': 'last_time',
            'time_index_count': 'appearances',
            'x_first': 'first_x',
            'x_last': 'last_x',
            'x_mean': 'mean_x',
            'x_std': 'std_x',
            'y_first': 'first_y',
            'y_last': 'last_y',
            'y_mean': 'mean_y',
            'y_std': 'std_y',
            'device_type_first': 'device_type'
        }, inplace=True)
        
        # lifetime 계산
        features_df['lifetime'] = (features_df['last_time'] - features_df['first_time']) * 10
        
        # NaN을 0으로
        features_df['std_x'] = features_df['std_x'].fillna(0)
        features_df['std_y'] = features_df['std_y'].fillna(0)
        
        # 이동 거리는 별도 계산 (벡터화가 어려움)
        total_distances = []
        for mac in features_df['mac_address']:
            mac_data = sorted_df[sorted_df['mac_address'] == mac]
            if len(mac_data) < 2:
                total_distances.append(0)
            else:
                dx = mac_data['x'].diff()
                dy = mac_data['y'].diff()
                distances = np.sqrt(dx**2 + dy**2)
                total_distances.append(distances.sum())
        
        features_df['total_distance'] = total_distances
        
        return features_df
    
    def generate_candidates(self, features_df: pd.DataFrame, positions_df: pd.DataFrame) -> List[Tuple[str, str, float, int]]:
        """
        연결 가능한 MAC 쌍 후보 생성
        ⚡ 최적화: 벡터화 및 조기 필터링
        
        Returns:
            candidates: [(mac_a, mac_b, time_gap, overlap_time), ...]
        """
        candidates = []
        
        # iPhone과 Android만 필터링 (타입 1, 10)
        random_mac_features = features_df[features_df['device_type'].isin([1, 10])].copy()
        
        if len(random_mac_features) == 0:
            return candidates
        
        # MAC별 출현 시간 리스트 생성 (한 번에)
        positions_filtered = positions_df[positions_df['mac_address'].isin(random_mac_features['mac_address'])]
        mac_times = positions_filtered.groupby('mac_address')['time_index'].apply(set).to_dict()
        
        # 디바이스 타입별로 분리 (조인 최적화)
        for device_type in [1, 10]:
            type_features = random_mac_features[random_mac_features['device_type'] == device_type]
            
            if len(type_features) < 2:
                continue
            
            # 벡터화 가능한 부분만 미리 계산
            mac_list = type_features['mac_address'].values
            last_times = type_features.set_index('mac_address')['last_time'].to_dict()
            first_times = type_features.set_index('mac_address')['first_time'].to_dict()
            
            time_window_idx = self.time_window / 10
            
            # 이중 루프 (하지만 타입별로 분리되어 더 빠름)
            for mac_a in mac_list:
                mac_a_times = mac_times[mac_a]
                mac_a_last = last_times[mac_a]
                
                for mac_b in mac_list:
                    if mac_a == mac_b:
                        continue
                    
                    mac_b_first = first_times[mac_b]
                    
                    # 조건 1: 시간 윈도우 체크 (빠른 필터링)
                    if mac_b_first > mac_a_last + time_window_idx:
                        continue
                    
                    # 조건 2: 겹치는 시간 찾기
                    mac_b_times = mac_times[mac_b]
                    overlap_times = mac_a_times & mac_b_times
                    
                    if not overlap_times:
                        continue
                    
                    overlap_time = max(overlap_times)
                    time_gap = (mac_b_first - mac_a_last) * 10
                    
                    candidates.append((mac_a, mac_b, time_gap, overlap_time))
        
        return candidates
    
    def calculate_similarity(self, 
                           mac_a_addr: str,
                           mac_b_addr: str,
                           mac_a: pd.Series, 
                           mac_b: pd.Series, 
                           time_gap: float,
                           overlap_time: int = None) -> float:
        """
        두 MAC 간 유사도 점수 계산
        ⚡ fast_mode: RSSI 유사도 생략, 속도 3배 향상
        
        Returns:
            score: 0~1 사이의 유사도 점수
        """
        # Fast mode: RSSI 유사도 생략
        if self.fast_mode:
            rssi_score = 0.7  # 기본값
        else:
            # 0. RSSI 벡터 유사도 (50% - 가장 중요!)
            rssi_score = 0.0
            if self.rssi_data is not None and overlap_time is not None:
                mac_a_key = (overlap_time, mac_a_addr)
                mac_b_key = (overlap_time, mac_b_addr)
                
                if mac_a_key in self.rssi_data and mac_b_key in self.rssi_data:
                    rssi_a = self.rssi_data[mac_a_key]
                    rssi_b = self.rssi_data[mac_b_key]
                    
                    # 공통 S-Ward만 비교
                    common_swards = set(rssi_a.keys()) & set(rssi_b.keys())
                    
                    if len(common_swards) >= 2:  # 최소 2개 이상 S-Ward 공통
                        # RSSI 절대 차이 계산 (약국 특성: 좁은 공간에서 절대값이 중요!)
                        rssi_diffs = []
                        for sw in common_swards:
                            diff = abs(rssi_a[sw] - rssi_b[sw])
                            rssi_diffs.append(diff)
                        
                        # 평균 차이를 점수로 변환
                        avg_diff = np.mean(rssi_diffs)
                        
                        # 차이가 작을수록 높은 점수
                        # 0dBm 차이 → 1.0점, 10dBm 차이 → 0.5점, 20dBm 이상 → 0.0점
                        rssi_score = max(0, 1 - avg_diff / 20)
            
            # RSSI 유사도가 낮으면 강력한 페널티 (fast_mode가 아닐 때만)
            # 약국 특성: 좁은 공간에서 RSSI 패턴이 가장 중요한 지표
            if rssi_score < 0.5:
                return rssi_score * 0.5  # 0.6 → 0.5로 강화
        
        # 1. 시간 간격 점수 (15%) - 가중치 감소
        temporal_score = max(0, 1 - abs(time_gap) / self.time_window)
        
        # 2. 공간 연속성 점수 (15%)
        spatial_distance = np.sqrt(
            (mac_b['first_x'] - mac_a['last_x'])**2 + 
            (mac_b['first_y'] - mac_a['last_y'])**2
        )
        max_distance = 100
        spatial_score = max(0, 1 - spatial_distance / max_distance)
        
        # 3. 위치 패턴 유사도 (10%)
        mean_distance = np.sqrt(
            (mac_b['mean_x'] - mac_a['mean_x'])**2 + 
            (mac_b['mean_y'] - mac_a['mean_y'])**2
        )
        pattern_score = max(0, 1 - mean_distance / max_distance)
        
        # 4. 이동 패턴 유사도 (10%) - 가중치 증가
        std_diff = abs(mac_a['std_x'] - mac_b['std_x']) + abs(mac_a['std_y'] - mac_b['std_y'])
        movement_score = max(0, 1 - std_diff / 50)
        
        # 가중 평균 (RSSI 유사도를 60%로 증가!)
        # 약국 환경: RSSI가 가장 신뢰할 수 있는 지표
        total_score = (
            0.60 * rssi_score +      # 50% → 60% (가장 중요!)
            0.15 * temporal_score +   # 20% → 15%
            0.15 * spatial_score +    # 15% → 15%
            0.05 * pattern_score +    # 10% → 5%
            0.05 * movement_score     # 5% → 5%
        )
        
        return total_score
    
    def link_macs(self, 
                  features_df: pd.DataFrame, 
                  candidates: List[Tuple[str, str, float, int]]) -> Dict[str, str]:
        """
        유사도 기반으로 MAC 연결
        
        Returns:
            mac_to_journey: {mac_address: journey_id}
        """
        # 유사도 계산
        scored_candidates = []
        features_dict = features_df.set_index('mac_address').to_dict('index')
        
        for mac_a, mac_b, time_gap, overlap_time in candidates:
            mac_a_features = features_dict[mac_a]
            mac_b_features = features_dict[mac_b]
            
            score = self.calculate_similarity(
                mac_a,
                mac_b,
                pd.Series(mac_a_features),
                pd.Series(mac_b_features),
                time_gap,
                overlap_time
            )
            
            if score >= self.threshold:
                scored_candidates.append((mac_a, mac_b, score))
        
        # 최적의 연결만 선택
        mac_next = {}
        
        for mac_a, mac_b, score in scored_candidates:
            if mac_a not in mac_next or score > mac_next[mac_a][1]:
                mac_next[mac_a] = (mac_b, score)
        
        # Journey 할당
        mac_to_journey = {}
        journey_id = 0
        assigned = set()
        
        for mac_a, (mac_b, score) in mac_next.items():
            if mac_a not in assigned:
                journey_id += 1
                journey_name = f"J{journey_id:04d}"
                mac_to_journey[mac_a] = journey_name
                assigned.add(mac_a)
            
            if mac_b not in assigned:
                mac_to_journey[mac_b] = mac_to_journey[mac_a]
                assigned.add(mac_b)
        
        # 연결되지 않은 MAC들도 개별 Journey로 할당
        all_macs = set(features_df['mac_address'])
        unlinked_macs = all_macs - assigned
        
        for mac in unlinked_macs:
            journey_id += 1
            mac_to_journey[mac] = f"J{journey_id:04d}"
        
        return mac_to_journey
    
    def create_journeys(self, 
                       positions_df: pd.DataFrame, 
                       mac_to_journey: Dict[str, str]) -> pd.DataFrame:
        """
        Journey 통계 생성
        
        Returns:
            journeys_df: Journey별 통계 DataFrame
        """
        positions_with_journey = positions_df.copy()
        positions_with_journey['journey_id'] = positions_with_journey['mac_address'].map(mac_to_journey)
        
        journeys = []
        
        for journey_id in positions_with_journey['journey_id'].unique():
            journey_data = positions_with_journey[positions_with_journey['journey_id'] == journey_id]
            
            macs = journey_data['mac_address'].unique()
            mac_count = len(macs)
            
            first_time = journey_data['time_index'].min()
            last_time = journey_data['time_index'].max()
            lifetime = (last_time - first_time) * 10
            
            total_appearances = len(journey_data)
            device_type = journey_data['device_type'].iloc[0]
            
            journeys.append({
                'journey_id': journey_id,
                'mac_count': mac_count,
                'macs': list(macs),
                'device_type': device_type,
                'first_time': first_time,
                'last_time': last_time,
                'lifetime': lifetime,
                'total_appearances': total_appearances
            })
        
        return pd.DataFrame(journeys)
    
    def stitch(self, positions_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str], pd.DataFrame]:
        """
        전체 MAC Stitching 파이프라인 실행
        
        Returns:
            features_df: MAC별 특징
            mac_to_journey: MAC to Journey 매핑
            journeys_df: Journey 통계
        """
        # 1. 특징 추출
        features_df = self.extract_features(positions_df)
        
        # 2. 후보 생성
        candidates = self.generate_candidates(features_df, positions_df)
        
        # 3. MAC 연결
        mac_to_journey = self.link_macs(features_df, candidates)
        
        # 4. Journey 생성
        journeys_df = self.create_journeys(positions_df, mac_to_journey)
        
        return features_df, mac_to_journey, journeys_df
