"""
Traffic Analyzer - 유동/방문 인구 분류 및 전환율 분석

MAC 랜덤화 환경에서 체류시간 + 신호세기 기반으로 유동/방문 분류

방문 인정 조건 (AND):
1. 체류시간: 2분 윈도우 내 6회 이상 감지
2. 신호세기: 평균 RSSI > 임계값
   - iPhone: -75 dBm
   - Android: -85 dBm
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


# 디바이스 타입별 RSSI 임계값
DEVICE_RSSI_THRESHOLDS = {
    1: -75,    # iPhone: RSSI > -75 dBm
    10: -85,   # Android: RSSI > -85 dBm
}
DEFAULT_RSSI_THRESHOLD = -80  # 기타 디바이스


class TrafficAnalyzer:
    """
    유동인구 vs 방문인구 분류 및 전환율 분석
    
    분류 기준 (체류시간 + 신호세기 AND 조건):
    - 유동인구 (Pass-by): 조건 미충족
    - 방문인구 (Visit): 
      * 2분 내 6회 이상 감지 AND
      * 평균 RSSI > 임계값 (iPhone: -75dBm, Android: -85dBm)
    """
    
    def __init__(self, 
                 pass_by_threshold_minutes: float = 2.0,
                 min_detections_in_window: int = 6,
                 rssi_threshold_iphone: float = -75,
                 rssi_threshold_android: float = -85,
                 time_unit_seconds: int = 10):
        """
        Args:
            pass_by_threshold_minutes: 유동/방문 구분 임계값 (분)
            min_detections_in_window: 윈도우 내 최소 감지 횟수
            rssi_threshold_iphone: iPhone RSSI 임계값 (dBm)
            rssi_threshold_android: Android RSSI 임계값 (dBm)
            time_unit_seconds: time_index 단위 (초)
        """
        self.pass_by_threshold = pass_by_threshold_minutes
        self.min_dwell_time = int(pass_by_threshold_minutes * 60 / time_unit_seconds)  # 12 time_index
        self.min_detections = min_detections_in_window
        self.rssi_threshold_iphone = rssi_threshold_iphone
        self.rssi_threshold_android = rssi_threshold_android
        self.time_unit = time_unit_seconds
    
    def get_rssi_threshold(self, device_type: int) -> float:
        """디바이스 타입별 RSSI 임계값 반환"""
        if device_type == 1:  # iPhone
            return self.rssi_threshold_iphone
        elif device_type == 10:  # Android
            return self.rssi_threshold_android
        else:
            return DEFAULT_RSSI_THRESHOLD
        
    def classify_traffic(self, positions_df: pd.DataFrame) -> pd.DataFrame:
        """
        각 MAC 주소를 유동/방문으로 분류 (positions_df 기반 - Legacy)
        
        주의: 이 메서드는 RSSI 정보가 없어 체류시간만으로 분류합니다.
        RSSI 필터링이 필요한 경우 classify_traffic_with_rssi()를 사용하세요.
        
        Args:
            positions_df: 위치 데이터 (time_index, mac_address 필수)
            
        Returns:
            분류 결과 DataFrame:
            - mac_address
            - first_seen: 첫 감지 시간
            - last_seen: 마지막 감지 시간
            - dwell_time_minutes: 체류 시간 (분)
            - traffic_type: 'pass_by' or 'visit'
            - record_count: 레코드 수
        """
        if len(positions_df) == 0:
            return pd.DataFrame(columns=[
                'mac_address', 'first_seen', 'last_seen', 
                'dwell_time_minutes', 'traffic_type', 'record_count'
            ])
        
        results = []
        
        for mac in positions_df['mac_address'].unique():
            mac_data = positions_df[positions_df['mac_address'] == mac]
            
            first_seen = mac_data['time_index'].min()
            last_seen = mac_data['time_index'].max()
            
            # 체류 시간 계산 (분)
            time_range = last_seen - first_seen
            dwell_time_minutes = (time_range * self.time_unit) / 60.0
            
            # 유동/방문 분류
            traffic_type = 'visit' if dwell_time_minutes >= self.pass_by_threshold else 'pass_by'
            
            results.append({
                'mac_address': mac,
                'first_seen': first_seen,
                'last_seen': last_seen,
                'dwell_time_minutes': dwell_time_minutes,
                'traffic_type': traffic_type,
                'record_count': len(mac_data)
            })
        
        return pd.DataFrame(results)
    
    def classify_traffic_with_rssi(self, rawdata: pd.DataFrame) -> pd.DataFrame:
        """
        각 MAC 주소를 유동/방문으로 분류 (RSSI 기반 필터링 포함) - 최적화 버전
        
        방문 인정 조건 (AND):
        1. 체류시간: 2분 윈도우 내 6회 이상 감지
        2. 신호세기: 평균 RSSI > 임계값 (iPhone: -75dBm, Android: -85dBm)
        
        Args:
            rawdata: Raw RSSI 데이터 (time_index, mac_address, rssi, type 필수)
            
        Returns:
            분류 결과 DataFrame
        """
        if len(rawdata) == 0:
            return pd.DataFrame(columns=[
                'mac_address', 'device_type', 'first_seen', 'last_seen', 
                'dwell_time_minutes', 'avg_rssi', 'rssi_threshold_used',
                'traffic_type', 'record_count'
            ])
        
        # 컬럼명 통일 (type -> device_type)
        df = rawdata.copy()
        if 'type' in df.columns and 'device_type' not in df.columns:
            df['device_type'] = df['type']
        
        # Step 1: MAC별 기본 통계 계산 (벡터화)
        mac_stats = df.groupby('mac_address').agg({
            'time_index': ['min', 'max', 'count'],
            'rssi': 'mean',
            'device_type': 'first'
        }).reset_index()
        
        mac_stats.columns = ['mac_address', 'first_seen', 'last_seen', 'record_count', 'avg_rssi', 'device_type']
        mac_stats['dwell_time_minutes'] = (mac_stats['last_seen'] - mac_stats['first_seen']) * self.time_unit / 60.0
        
        # Step 2: RSSI 임계값 매핑 (벡터화)
        mac_stats['rssi_threshold_used'] = mac_stats['device_type'].map(
            lambda x: self.rssi_threshold_iphone if x == 1 else (
                self.rssi_threshold_android if x == 10 else DEFAULT_RSSI_THRESHOLD
            )
        )
        
        # Step 3: 빠른 필터링 - 최소 감지 횟수 미달은 바로 pass_by
        mac_stats['traffic_type'] = 'pass_by'
        
        # 최소 감지 횟수 이상인 MAC만 상세 검사
        candidates = mac_stats[mac_stats['record_count'] >= self.min_detections]['mac_address'].values
        
        if len(candidates) > 0:
            # Step 4: 후보 MAC들만 윈도우 검사 (최적화된 버전)
            visitor_macs = self._check_visitor_windows_fast(df, candidates)
            mac_stats.loc[mac_stats['mac_address'].isin(visitor_macs), 'traffic_type'] = 'visit'
        
        return mac_stats
    
    def _check_visitor_windows_fast(self, df: pd.DataFrame, candidate_macs: np.ndarray) -> set:
        """
        후보 MAC들에 대해 2분 윈도우 조건 검사 (최적화 버전)
        
        Returns:
            방문자로 판정된 MAC 주소 set
        """
        visitor_macs = set()
        
        # 후보 MAC 데이터만 필터링
        candidate_df = df[df['mac_address'].isin(candidate_macs)]
        
        # MAC별로 그룹화하여 처리
        for mac, group in candidate_df.groupby('mac_address'):
            if mac in visitor_macs:
                continue
                
            time_indices = group['time_index'].values
            rssi_values = group['rssi'].values
            device_type = group['device_type'].iloc[0]
            
            rssi_threshold = (self.rssi_threshold_iphone if device_type == 1 
                            else self.rssi_threshold_android if device_type == 10 
                            else DEFAULT_RSSI_THRESHOLD)
            
            # 정렬된 상태에서 윈도우 검사 (조기 종료)
            sorted_indices = np.argsort(time_indices)
            time_indices = time_indices[sorted_indices]
            rssi_values = rssi_values[sorted_indices]
            
            # 슬라이딩 윈도우 (최적화: 첫 번째 조건 충족시 즉시 종료)
            n = len(time_indices)
            for i in range(n):
                window_end = time_indices[i] + self.min_dwell_time
                
                # 이진 탐색으로 윈도우 끝 인덱스 찾기
                j = np.searchsorted(time_indices, window_end, side='left')
                window_count = j - i
                
                if window_count >= self.min_detections:
                    window_rssi_mean = np.mean(rssi_values[i:j])
                    if window_rssi_mean > rssi_threshold:
                        visitor_macs.add(mac)
                        break
        
        return visitor_macs
    
    def classify_traffic_with_rssi_ultra_fast(self, rawdata: pd.DataFrame) -> Dict:
        """
        초고속 분류 - 숫자만 반환 (체류시간 세부 정보 불필요 시 사용)
        
        Returns:
            {'visit_count': int, 'pass_by_count': int, 'total': int}
        """
        if len(rawdata) == 0:
            return {'visit_count': 0, 'pass_by_count': 0, 'total': 0}
        
        # 컬럼명 통일
        df = rawdata.copy()
        if 'type' in df.columns and 'device_type' not in df.columns:
            df['device_type'] = df['type']
        
        # MAC별 감지 횟수
        mac_counts = df.groupby('mac_address').size()
        total_macs = len(mac_counts)
        
        # 최소 감지 횟수 미달은 바로 pass_by
        candidates = mac_counts[mac_counts >= self.min_detections].index.values
        
        if len(candidates) == 0:
            return {'visit_count': 0, 'pass_by_count': total_macs, 'total': total_macs}
        
        # 후보들만 상세 검사
        visitor_macs = self._check_visitor_windows_fast(df, candidates)
        visit_count = len(visitor_macs)
        
        return {
            'visit_count': visit_count,
            'pass_by_count': total_macs - visit_count,
            'total': total_macs
        }
    
    def calculate_conversion_rate(self, traffic_df: pd.DataFrame) -> Dict:
        """
        전환율 계산
        
        Args:
            traffic_df: classify_traffic() 결과
            
        Returns:
            {
                'total_traffic': 총 트래픽,
                'pass_by_count': 유동인구,
                'visit_count': 방문인구,
                'conversion_rate': 전환율 (0-1),
                'avg_dwell_pass_by': 유동인구 평균 체류시간 (분),
                'avg_dwell_visit': 방문인구 평균 체류시간 (분)
            }
        """
        if len(traffic_df) == 0:
            return {
                'total_traffic': 0,
                'pass_by_count': 0,
                'visit_count': 0,
                'conversion_rate': 0.0,
                'avg_dwell_pass_by': 0.0,
                'avg_dwell_visit': 0.0
            }
        
        pass_by_df = traffic_df[traffic_df['traffic_type'] == 'pass_by']
        visit_df = traffic_df[traffic_df['traffic_type'] == 'visit']
        
        pass_by_count = len(pass_by_df)
        visit_count = len(visit_df)
        total_traffic = pass_by_count + visit_count
        
        conversion_rate = visit_count / total_traffic if total_traffic > 0 else 0.0
        
        avg_dwell_pass_by = pass_by_df['dwell_time_minutes'].mean() if len(pass_by_df) > 0 else 0.0
        avg_dwell_visit = visit_df['dwell_time_minutes'].mean() if len(visit_df) > 0 else 0.0
        
        return {
            'total_traffic': total_traffic,
            'pass_by_count': pass_by_count,
            'visit_count': visit_count,
            'conversion_rate': conversion_rate,
            'avg_dwell_pass_by': avg_dwell_pass_by,
            'avg_dwell_visit': avg_dwell_visit
        }
    
    def hourly_conversion_analysis(self, 
                                  positions_df: pd.DataFrame) -> pd.DataFrame:
        """
        시간대별 전환율 분석
        
        Returns:
            DataFrame with columns:
            - hour: 시간 (0-23)
            - total_traffic
            - pass_by_count
            - visit_count
            - conversion_rate
        """
        if len(positions_df) == 0:
            return pd.DataFrame(columns=[
                'hour', 'total_traffic', 'pass_by_count', 
                'visit_count', 'conversion_rate'
            ])
        
        # 시간 추가
        positions_df = positions_df.copy()
        positions_df['hour'] = (positions_df['time_index'] * self.time_unit / 3600).astype(int)
        
        hourly_results = []
        
        for hour in range(24):
            hour_data = positions_df[positions_df['hour'] == hour]
            
            if len(hour_data) == 0:
                hourly_results.append({
                    'hour': hour,
                    'total_traffic': 0,
                    'pass_by_count': 0,
                    'visit_count': 0,
                    'conversion_rate': 0.0
                })
                continue
            
            # 이 시간대에 있었던 MAC 분류
            traffic_df = self.classify_traffic(hour_data)
            conversion_stats = self.calculate_conversion_rate(traffic_df)
            
            hourly_results.append({
                'hour': hour,
                'total_traffic': conversion_stats['total_traffic'],
                'pass_by_count': conversion_stats['pass_by_count'],
                'visit_count': conversion_stats['visit_count'],
                'conversion_rate': conversion_stats['conversion_rate']
            })
        
        return pd.DataFrame(hourly_results)
    
    def compare_stores_conversion(self, 
                                 store_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        여러 매장의 전환율 비교
        
        Args:
            store_data: {store_name: positions_df, ...}
            
        Returns:
            비교 결과 DataFrame:
            - store_name
            - total_traffic
            - pass_by_count
            - visit_count
            - conversion_rate
            - avg_dwell_pass_by
            - avg_dwell_visit
        """
        results = []
        
        for store_name, positions_df in store_data.items():
            traffic_df = self.classify_traffic(positions_df)
            stats = self.calculate_conversion_rate(traffic_df)
            
            results.append({
                'store_name': store_name,
                **stats
            })
        
        return pd.DataFrame(results)
    
    def peak_time_analysis(self, positions_df: pd.DataFrame) -> Dict:
        """
        피크타임 분석 (유동 vs 방문)
        
        Returns:
            {
                'peak_traffic_hour': 총 트래픽 피크 시간,
                'peak_visit_hour': 방문인구 피크 시간,
                'peak_conversion_hour': 전환율 피크 시간,
                'hourly_data': 시간대별 데이터
            }
        """
        hourly_df = self.hourly_conversion_analysis(positions_df)
        
        if len(hourly_df) == 0:
            return {
                'peak_traffic_hour': None,
                'peak_visit_hour': None,
                'peak_conversion_hour': None,
                'hourly_data': hourly_df
            }
        
        # 피크 시간 찾기
        peak_traffic_hour = hourly_df.loc[hourly_df['total_traffic'].idxmax(), 'hour']
        peak_visit_hour = hourly_df.loc[hourly_df['visit_count'].idxmax(), 'hour']
        peak_conversion_hour = hourly_df.loc[hourly_df['conversion_rate'].idxmax(), 'hour']
        
        return {
            'peak_traffic_hour': int(peak_traffic_hour),
            'peak_visit_hour': int(peak_visit_hour),
            'peak_conversion_hour': int(peak_conversion_hour),
            'hourly_data': hourly_df
        }
    
    def weekday_pattern_analysis(self,
                                store_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
        """
        요일별 전환율 패턴 분석
        
        Args:
            store_data: {
                store_name: {
                    'YYYY-MM-DD': positions_df,
                    ...
                }
            }
            
        Returns:
            DataFrame with:
            - store_name
            - weekday (0=Mon, 6=Sun)
            - avg_conversion_rate
            - avg_visit_count
        """
        results = []
        
        for store_name, dates_data in store_data.items():
            weekday_stats = {i: {'conversions': [], 'visits': []} for i in range(7)}
            
            for date_str, positions_df in dates_data.items():
                date_obj = pd.to_datetime(date_str)
                weekday = date_obj.weekday()
                
                traffic_df = self.classify_traffic(positions_df)
                stats = self.calculate_conversion_rate(traffic_df)
                
                weekday_stats[weekday]['conversions'].append(stats['conversion_rate'])
                weekday_stats[weekday]['visits'].append(stats['visit_count'])
            
            for weekday, data in weekday_stats.items():
                if len(data['conversions']) > 0:
                    results.append({
                        'store_name': store_name,
                        'weekday': weekday,
                        'avg_conversion_rate': np.mean(data['conversions']),
                        'avg_visit_count': np.mean(data['visits'])
                    })
        
        return pd.DataFrame(results)
