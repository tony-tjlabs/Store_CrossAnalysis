"""
Visitor Classifier - 실제 방문자 vs 외부 유동인구 분류
약국 특성을 고려한 방문자 분류 알고리즘
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


# 디바이스 타입별 RSSI 임계값 (약국 방문 인정 기준)
DEVICE_RSSI_THRESHOLDS = {
    1: -75,    # iPhone: RSSI > -75 dBm
    10: -85,   # Android: RSSI > -85 dBm
}
DEFAULT_RSSI_THRESHOLD = -80  # 기타 디바이스


class VisitorClassifier:
    """
    약국 방문자 분류기
    
    분류 기준:
    1. 실제 약국 방문자 (Real Visitor):
       - 체류 시간 ≥ 2분 (12 time_index)
       - 2분 윈도우 내 6회 이상 감지
       - 평균 RSSI > 임계값 (iPhone: -75dBm, Android: -85dBm)
       
    2. 외부 유동인구 (Passer-by):
       - 위 조건을 만족하지 않음
    """
    
    def __init__(self, 
                 min_dwell_time: int = 12,      # 120초 = 12 * 10초 (2분)
                 min_detections_in_window: int = 6,  # 2분 내 최소 6회 감지
                 rssi_threshold_iphone: float = -75,   # iPhone RSSI 임계값
                 rssi_threshold_android: float = -85,  # Android RSSI 임계값
                 rssi_std_threshold: float = 15):
        """
        Args:
            min_dwell_time: 최소 체류 시간 (time_index 단위, 기본 2분=12)
            min_detections_in_window: 윈도우 내 최소 감지 횟수
            rssi_threshold_iphone: iPhone RSSI 임계값 (dBm)
            rssi_threshold_android: Android RSSI 임계값 (dBm)
            rssi_std_threshold: RSSI 표준편차 임계값
        """
        self.min_dwell_time = min_dwell_time
        self.min_detections = min_detections_in_window
        self.rssi_threshold_iphone = rssi_threshold_iphone
        self.rssi_threshold_android = rssi_threshold_android
        self.rssi_std_threshold = rssi_std_threshold
        self.time_unit = 10  # 10초
    
    def get_rssi_threshold(self, device_type: int) -> float:
        """
        디바이스 타입별 RSSI 임계값 반환
        
        Args:
            device_type: 1=iPhone, 10=Android
            
        Returns:
            RSSI 임계값 (dBm)
        """
        if device_type == 1:  # iPhone
            return self.rssi_threshold_iphone
        elif device_type == 10:  # Android
            return self.rssi_threshold_android
        else:
            return DEFAULT_RSSI_THRESHOLD
    
    def classify_visitors(self, rawdata: pd.DataFrame) -> pd.DataFrame:
        """
        Raw 데이터에서 각 MAC을 방문자 vs 유동인구로 분류
        
        방문자 인정 조건 (AND):
        1. 체류시간: 2분 윈도우 내 6회 이상 감지
        2. 신호세기: 평균 RSSI > 임계값 (iPhone: -75dBm, Android: -85dBm)
        
        Args:
            rawdata: Raw RSSI 데이터 (time_index, mac_address, rssi, device_type 필수)
            
        Returns:
            DataFrame with columns:
                - mac_address
                - visitor_type: 'real_visitor' or 'passer_by'
                - dwell_time: 체류 시간 (초)
                - avg_rssi: 평균 RSSI
                - rssi_std: RSSI 표준편차
                - first_time: 첫 출현 time_index
                - last_time: 마지막 출현 time_index
                - appearance_count: 출현 횟수
                - device_type: 디바이스 타입 (1=iPhone, 10=Android)
                - rssi_threshold_used: 사용된 RSSI 임계값
        """
        classifications = []
        
        for mac in rawdata['mac_address'].unique():
            mac_data = rawdata[rawdata['mac_address'] == mac].sort_values('time_index')
            
            # 디바이스 타입 확인 (device_type 또는 type 컬럼 사용, iPhone=1, Android=10)
            if 'device_type' in mac_data.columns:
                device_type = mac_data['device_type'].iloc[0]
            elif 'type' in mac_data.columns:
                device_type = mac_data['type'].iloc[0]
            else:
                device_type = None
            
            # 디바이스 타입별 RSSI 임계값 결정
            rssi_threshold = self.get_rssi_threshold(device_type) if device_type else DEFAULT_RSSI_THRESHOLD
            
            # 2분 슬라이딩 윈도우로 방문자 체크
            time_indices = mac_data['time_index'].values
            rssi_values = mac_data['rssi'].values
            
            is_visitor = False
            
            # 각 2분(12 time_index) 윈도우를 체크
            for i in range(len(time_indices)):
                window_start = time_indices[i]
                window_end = window_start + self.min_dwell_time  # 2분 = 12 time_index
                
                # 이 윈도우 내의 감지 데이터
                window_mask = (time_indices >= window_start) & (time_indices < window_end)
                window_detections = np.sum(window_mask)
                
                # 조건 1: 최소 감지 횟수 충족
                if window_detections >= self.min_detections:
                    window_rssi = rssi_values[window_mask]
                    avg_rssi_window = np.mean(window_rssi)
                    
                    # 조건 2: RSSI 임계값 충족 (디바이스별 다름)
                    if avg_rssi_window > rssi_threshold:
                        is_visitor = True
                        break
            
            # 기본 통계 (backward compatibility)
            first_time = mac_data['time_index'].min()
            last_time = mac_data['time_index'].max()
            dwell_time_sec = len(time_indices) * self.time_unit  # 실제 감지 시간
            
            appearance_count = len(mac_data)
            avg_rssi = mac_data['rssi'].mean()
            rssi_std = mac_data['rssi'].std()
            
            if pd.isna(rssi_std):
                rssi_std = 0
            
            # 분류 결과
            visitor_type = 'real_visitor' if is_visitor else 'passer_by'
            
            classifications.append({
                'mac_address': mac,
                'visitor_type': visitor_type,
                'dwell_time': dwell_time_sec,
                'avg_rssi': avg_rssi,
                'rssi_std': rssi_std,
                'first_time': first_time,
                'last_time': last_time,
                'appearance_count': appearance_count,
                'device_type': device_type,
                'rssi_threshold_used': rssi_threshold
            })
        
        return pd.DataFrame(classifications)
    
    def get_visitor_stats(self, classification_df: pd.DataFrame) -> Dict:
        """
        방문자 분류 통계 계산
        
        Returns:
            {
                'total_macs': 총 MAC 수,
                'real_visitors': 실제 방문자 수,
                'passers_by': 외부 유동인구 수,
                'visitor_ratio': 방문자 비율 (0~1),
                'avg_dwell_time_visitors': 실제 방문자 평균 체류시간,
                'avg_dwell_time_passers': 유동인구 평균 체류시간,
                'avg_rssi_visitors': 실제 방문자 평균 RSSI,
                'avg_rssi_passers': 유동인구 평균 RSSI
            }
        """
        total_macs = len(classification_df)
        
        visitors = classification_df[classification_df['visitor_type'] == 'real_visitor']
        passers = classification_df[classification_df['visitor_type'] == 'passer_by']
        
        real_visitors_count = len(visitors)
        passers_by_count = len(passers)
        
        visitor_ratio = real_visitors_count / total_macs if total_macs > 0 else 0
        
        return {
            'total_macs': total_macs,
            'real_visitors': real_visitors_count,
            'passers_by': passers_by_count,
            'visitor_ratio': visitor_ratio,
            'avg_dwell_time_visitors': visitors['dwell_time'].mean() if len(visitors) > 0 else 0,
            'avg_dwell_time_passers': passers['dwell_time'].mean() if len(passers) > 0 else 0,
            'avg_rssi_visitors': visitors['avg_rssi'].mean() if len(visitors) > 0 else 0,
            'avg_rssi_passers': passers['avg_rssi'].mean() if len(passers) > 0 else 0
        }
    
    def compare_stores(self, store_classifications: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        여러 매장의 방문자 분류 비교
        
        Args:
            store_classifications: {store_name: classification_df}
            
        Returns:
            비교 DataFrame
        """
        comparison_data = []
        
        for store_name, classification_df in store_classifications.items():
            stats = self.get_visitor_stats(classification_df)
            stats['store_name'] = store_name
            comparison_data.append(stats)
        
        df = pd.DataFrame(comparison_data)
        
        # 컬럼 순서 재정렬
        columns_order = [
            'store_name',
            'total_macs',
            'real_visitors',
            'passers_by',
            'visitor_ratio',
            'avg_dwell_time_visitors',
            'avg_dwell_time_passers',
            'avg_rssi_visitors',
            'avg_rssi_passers'
        ]
        
        return df[columns_order]
    
    def get_hourly_visitor_pattern(self, rawdata: pd.DataFrame, 
                                   classification_df: pd.DataFrame) -> pd.DataFrame:
        """
        시간대별 실제 방문자 vs 유동인구 패턴
        
        Returns:
            DataFrame (hour, real_visitors, passers_by, total)
        """
        # 실제 방문자와 유동인구 MAC 분리
        real_visitor_macs = set(classification_df[
            classification_df['visitor_type'] == 'real_visitor'
        ]['mac_address'])
        
        passer_by_macs = set(classification_df[
            classification_df['visitor_type'] == 'passer_by'
        ]['mac_address'])
        
        # 시간대별 집계
        rawdata['hour'] = (rawdata['time_index'] * self.time_unit / 3600).astype(int)
        
        hourly_data = []
        
        for hour in sorted(rawdata['hour'].unique()):
            hour_data = rawdata[rawdata['hour'] == hour]
            
            real_count = hour_data[hour_data['mac_address'].isin(real_visitor_macs)]['mac_address'].nunique()
            passer_count = hour_data[hour_data['mac_address'].isin(passer_by_macs)]['mac_address'].nunique()
            
            hourly_data.append({
                'hour': hour,
                'real_visitors': real_count,
                'passers_by': passer_count,
                'total': real_count + passer_count
            })
        
        return pd.DataFrame(hourly_data)
    
    def apply_mac_stitching_adjustment(self, classification_df: pd.DataFrame,
                                      mac_change_interval: int = 6) -> Dict:
        """
        MAC 주소 변경을 고려한 실제 방문자 수 추정
        
        Args:
            classification_df: 분류 결과 DataFrame
            mac_change_interval: MAC 변경 주기 (time_index 단위, 기본 60초)
            
        Returns:
            {
                'estimated_real_visitors': 추정 실제 방문자 수,
                'adjustment_factor': 조정 계수
            }
        """
        real_visitors = classification_df[classification_df['visitor_type'] == 'real_visitor']
        
        if len(real_visitors) == 0:
            return {
                'estimated_real_visitors': 0,
                'adjustment_factor': 1.0
            }
        
        # 평균 체류 시간 기반 MAC 변경 횟수 추정
        avg_dwell_time_idx = real_visitors['dwell_time'].mean() / self.time_unit
        
        # 체류 시간 동안 몇 번 MAC이 변경되었을지 추정
        estimated_mac_changes = max(1, avg_dwell_time_idx / mac_change_interval)
        
        # 조정 계수 (실제 방문자 수는 MAC 개수 / 변경 횟수)
        adjustment_factor = 1.0 / estimated_mac_changes
        
        estimated_visitors = int(len(real_visitors) * adjustment_factor)
        
        return {
            'estimated_real_visitors': estimated_visitors,
            'adjustment_factor': adjustment_factor,
            'raw_mac_count': len(real_visitors),
            'avg_dwell_time': real_visitors['dwell_time'].mean()
        }
    
    def classify_with_mac_stitching(self, rawdata: pd.DataFrame, 
                                    positions_df: pd.DataFrame,
                                    journeys_df: pd.DataFrame,
                                    mac_to_journey: Dict[str, str]) -> pd.DataFrame:
        """
        MAC Stitching 결과를 활용한 방문자 분류
        
        Args:
            rawdata: Raw RSSI 데이터
            positions_df: 위치 데이터
            journeys_df: Journey 통계
            mac_to_journey: MAC to Journey 매핑
            
        Returns:
            Journey별 분류 DataFrame
        """
        classifications = []
        
        for _, journey in journeys_df.iterrows():
            journey_id = journey['journey_id']
            macs = journey['macs']
            
            # Journey의 모든 MAC 데이터 수집
            journey_rawdata = rawdata[rawdata['mac_address'].isin(macs)]
            
            # 디바이스 타입별 RSSI 임계값 결정
            device_type = journey['device_type']
            rssi_threshold = self.get_rssi_threshold(device_type) if device_type else DEFAULT_RSSI_THRESHOLD
            
            # 분류 로직: 2분간 6회 이상 + RSSI > 임계값 (iPhone: -75, Android: -85)
            time_indices = journey_rawdata['time_index'].values
            rssi_values = journey_rawdata['rssi'].values
            
            is_visitor = False
            
            # 각 2분(12 time_index) 윈도우를 체크
            if len(time_indices) > 0:
                for i in range(len(time_indices)):
                    window_start = time_indices[i]
                    window_end = window_start + self.min_dwell_time  # 2분 = 12 time_index
                    
                    # 이 윈도우 내의 감지 데이터
                    window_mask = (time_indices >= window_start) & (time_indices < window_end)
                    window_detections = np.sum(window_mask)
                    
                    # 조건 1: 최소 감지 횟수 충족
                    if window_detections >= self.min_detections:
                        window_rssi = rssi_values[window_mask]
                        avg_rssi_window = np.mean(window_rssi)
                        
                        # 조건 2: RSSI 임계값 충족 (디바이스별 다름)
                        if avg_rssi_window > rssi_threshold:
                            is_visitor = True
                            break
            
            # 기본 통계 계산
            dwell_time_sec = journey['lifetime']
            appearance_count = journey['total_appearances']
            device_type = journey['device_type']
            
            # 전체 평균 RSSI 및 표준편차
            avg_rssi = journey_rawdata['rssi'].mean()
            rssi_std = journey_rawdata['rssi'].std()
            
            if pd.isna(rssi_std):
                rssi_std = 0
            
            # 분류 결과
            visitor_type = 'real_visitor' if is_visitor else 'passer_by'
            
            classifications.append({
                'journey_id': journey_id,
                'mac_count': journey['mac_count'],
                'macs': macs,
                'visitor_type': visitor_type,
                'dwell_time': dwell_time_sec,
                'avg_rssi': avg_rssi,
                'rssi_std': rssi_std,
                'first_time': journey['first_time'],
                'last_time': journey['last_time'],
                'appearance_count': appearance_count,
                'device_type': device_type
            })
        
        return pd.DataFrame(classifications)
    
    def get_journey_visitor_stats(self, journey_classification_df: pd.DataFrame) -> Dict:
        """
        Journey 기반 방문자 통계 (MAC Stitching 적용 후)
        
        Returns:
            정확한 방문자 통계
        """
        total_journeys = len(journey_classification_df)
        
        visitors = journey_classification_df[journey_classification_df['visitor_type'] == 'real_visitor']
        passers = journey_classification_df[journey_classification_df['visitor_type'] == 'passer_by']
        
        real_visitors_count = len(visitors)
        passers_by_count = len(passers)
        
        visitor_ratio = real_visitors_count / total_journeys if total_journeys > 0 else 0
        
        # MAC 통합 정보
        total_macs_visitors = visitors['mac_count'].sum() if len(visitors) > 0 else 0
        total_macs_passers = passers['mac_count'].sum() if len(passers) > 0 else 0
        
        return {
            'total_journeys': total_journeys,
            'real_visitors': real_visitors_count,
            'passers_by': passers_by_count,
            'visitor_ratio': visitor_ratio,
            'avg_dwell_time_visitors': visitors['dwell_time'].mean() if len(visitors) > 0 else 0,
            'avg_dwell_time_passers': passers['dwell_time'].mean() if len(passers) > 0 else 0,
            'avg_rssi_visitors': visitors['avg_rssi'].mean() if len(visitors) > 0 else 0,
            'avg_rssi_passers': passers['avg_rssi'].mean() if len(passers) > 0 else 0,
            'total_macs_visitors': total_macs_visitors,
            'total_macs_passers': total_macs_passers,
            'avg_mac_per_visitor': visitors['mac_count'].mean() if len(visitors) > 0 else 0,
            'avg_mac_per_passer': passers['mac_count'].mean() if len(passers) > 0 else 0
        }
