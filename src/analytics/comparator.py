"""
Store Comparator - 매장 간 비교 분석 엔진
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class StoreComparator:
    """
    여러 매장의 데이터를 비교 분석
    
    기능:
    1. 기본 통계 비교 (방문자 수, 체류 시간 등)
    2. 시간대별 비교
    3. 요일별 비교
    4. 주중/주말 비교
    5. 트렌드 분석
    """
    
    def __init__(self):
        self.time_unit = 10  # 10초
    
    def _time_index_to_hour(self, time_index: int) -> float:
        """time_index를 시간(hour)으로 변환"""
        return (time_index * self.time_unit) / 3600
    
    def _time_index_to_period(self, time_index: int) -> str:
        """time_index를 시간대로 변환"""
        hour = self._time_index_to_hour(time_index)
        
        if 0 <= hour < 1.5:
            return "early_morning"
        elif 1.5 <= hour < 3:
            return "morning"
        elif 3 <= hour < 4.5:
            return "late_morning"
        elif 4.5 <= hour < 6:
            return "lunch"
        elif 6 <= hour < 7.5:
            return "afternoon"
        elif 7.5 <= hour < 9:
            return "late_afternoon"
        elif 9 <= hour < 10.5:
            return "evening"
        else:
            return "night"
    
    def calculate_basic_stats(self, positions_df: pd.DataFrame, 
                             store_name: str) -> Dict:
        """
        기본 통계 계산
        
        Returns:
            {
                'store_name': 매장명,
                'total_visitors': 총 방문자 수 (unique MAC),
                'total_records': 총 레코드 수,
                'avg_dwell_time': 평균 체류 시간 (분),
                'device_type_dist': 디바이스 타입 분포,
                'peak_hour': 피크 시간대,
                'peak_visitors': 피크 시간대 방문자 수
            }
        """
        if len(positions_df) == 0:
            return {
                'store_name': store_name,
                'total_visitors': 0,
                'total_records': 0,
                'avg_dwell_time': 0,
                'device_type_dist': {},
                'peak_hour': None,
                'peak_visitors': 0
            }
        
        # 총 방문자 수
        total_visitors = positions_df['mac_address'].nunique()
        
        # 총 레코드 수
        total_records = len(positions_df)
        
        # 평균 체류 시간 계산
        dwell_times = []
        for mac in positions_df['mac_address'].unique():
            mac_data = positions_df[positions_df['mac_address'] == mac]
            time_range = mac_data['time_index'].max() - mac_data['time_index'].min()
            dwell_time_minutes = (time_range * self.time_unit) / 60
            dwell_times.append(dwell_time_minutes)
        
        avg_dwell_time = np.mean(dwell_times) if dwell_times else 0
        
        # 디바이스 타입 분포
        device_type_dist = positions_df['device_type'].value_counts().to_dict()
        
        # 피크 시간대 찾기
        positions_df['hour'] = positions_df['time_index'].apply(
            lambda x: int(self._time_index_to_hour(x))
        )
        hourly_visitors = positions_df.groupby('hour')['mac_address'].nunique()
        
        if len(hourly_visitors) > 0:
            peak_hour = hourly_visitors.idxmax()
            peak_visitors = hourly_visitors.max()
        else:
            peak_hour = None
            peak_visitors = 0
        
        return {
            'store_name': store_name,
            'total_visitors': total_visitors,
            'total_records': total_records,
            'avg_dwell_time': avg_dwell_time,
            'device_type_dist': device_type_dist,
            'peak_hour': peak_hour,
            'peak_visitors': peak_visitors
        }
    
    def compare_hourly_traffic(self, store_positions: Dict[str, pd.DataFrame], 
                              store_rawdata: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, pd.DataFrame]:
        """
        시간대별 방문자 수 비교 (1분 time bin 사용)
        3가지 카테고리: 전체 센싱, 내부 방문자, 외부 유동인구
        
        프로세스:
        1. 하루 전체 데이터로 각 MAC 주소별 방문자/유동인구 분류
        2. 분류 결과를 기반으로 1분 단위 카운팅
        
        Args:
            store_positions: {store_name: positions_df}
            store_rawdata: {store_name: rawdata_df} (MAC 분류용)
            
        Returns:
            {
                'total': DataFrame (hour, store1, store2, ...),
                'visitors': DataFrame (hour, store1, store2, ...),
                'passers': DataFrame (hour, store1, store2, ...)
            }
        """
        hourly_total = {}
        hourly_visitors = {}
        hourly_passers = {}
        
        for store_name, positions_df in store_positions.items():
            if len(positions_df) == 0:
                continue
            
            # 1분 단위 time bin 생성 (6개 time_index = 1분)
            positions_df = positions_df.copy()
            positions_df['minute_bin'] = positions_df['time_index'] // 6
            positions_df['hour'] = positions_df['time_index'].apply(
                lambda x: int(self._time_index_to_hour(x))
            )
            
            # 전체 센싱 인원
            minute_total = positions_df.groupby(['hour', 'minute_bin'])['mac_address'].nunique()
            hourly_avg_total = minute_total.groupby(level=0).mean()
            hourly_total[store_name] = hourly_avg_total
            
            # 1단계: 하루 전체 데이터로 MAC 주소별 방문자/유동인구 분류
            if store_rawdata and store_name in store_rawdata:
                rawdata = store_rawdata[store_name]
                
                visitor_macs = set()
                passer_macs = set()
                
                total_macs = 0
                long_dwell_count = 0
                strong_signal_count = 0
                stable_signal_count = 0
                
                for mac in rawdata['mac_address'].unique():
                    mac_data = rawdata[rawdata['mac_address'] == mac].sort_values('time_index')
                    total_macs += 1
                    
                    # 2분 슬라이딩 윈도우로 체크
                    time_indices = mac_data['time_index'].values
                    rssi_values = mac_data['rssi'].values
                    
                    is_visitor = False
                    
                    # 각 2분(12 time_index) 윈도우를 체크
                    for i in range(len(time_indices)):
                        window_start = time_indices[i]
                        window_end = window_start + 12  # 2분 = 12 time_index
                        
                        # 이 윈도우 내의 감지 데이터
                        window_mask = (time_indices >= window_start) & (time_indices < window_end)
                        window_detections = np.sum(window_mask)
                        
                        if window_detections >= 6:  # 2분 중 6회 이상 감지
                            window_rssi = rssi_values[window_mask]
                            avg_rssi = np.mean(window_rssi)
                            
                            if avg_rssi > -70:  # 평균 RSSI > -70
                                is_visitor = True
                                break
                    
                    # 통계용
                    if len(time_indices) >= 6:
                        long_dwell_count += 1
                    if np.mean(rssi_values) > -70:
                        strong_signal_count += 1
                    stable_signal_count += 1  # 모든 MAC이 "감지됨"이므로 카운트
                    
                    if is_visitor:
                        visitor_macs.add(mac)
                    else:
                        passer_macs.add(mac)
                
                # 디버깅 출력 (첫 번째 매장만)
                if len(hourly_total) == 0:  # 첫 번째 매장
                    print(f"\n=== {store_name} 분류 결과 ===")
                    print(f"전체 MAC: {total_macs}개")
                    print(f"1분+ 체류: {long_dwell_count}개 ({long_dwell_count/total_macs*100:.1f}%)")
                    print(f"강한 신호: {strong_signal_count}개 ({strong_signal_count/total_macs*100:.1f}%)")
                    print(f"안정적: {stable_signal_count}개 ({stable_signal_count/total_macs*100:.1f}%)")
                    print(f"방문자: {len(visitor_macs)}개 ({len(visitor_macs)/total_macs*100:.1f}%)")
                    print(f"유동인구: {len(passer_macs)}개 ({len(passer_macs)/total_macs*100:.1f}%)")
                    print("========================\n")
                
                # 2단계: 분류된 MAC을 기반으로 1분 단위 카운팅
                visitor_hourly = []
                passer_hourly = []
                hours = []
                
                for (hour, minute_bin), group in positions_df.groupby(['hour', 'minute_bin']):
                    macs_in_bin = set(group['mac_address'].unique())
                    
                    # 방문자 카운트
                    visitor_count = len(macs_in_bin & visitor_macs)
                    passer_count = len(macs_in_bin & passer_macs)
                    
                    hours.append(hour)
                    visitor_hourly.append(visitor_count)
                    passer_hourly.append(passer_count)
                
                # 시간별 평균 계산
                if hours:
                    visitor_series = pd.Series(visitor_hourly, index=hours)
                    passer_series = pd.Series(passer_hourly, index=hours)
                    
                    hourly_visitors[store_name] = visitor_series.groupby(level=0).mean()
                    hourly_passers[store_name] = passer_series.groupby(level=0).mean()
        
        # DataFrame으로 결합
        result_total = pd.DataFrame(hourly_total).fillna(0).reset_index()
        result_total.columns.name = None
        result_total = result_total.rename(columns={'index': 'hour'})
        
        result_visitors = pd.DataFrame(hourly_visitors).fillna(0).reset_index()
        result_visitors.columns.name = None
        result_visitors = result_visitors.rename(columns={'index': 'hour'})
        
        result_passers = pd.DataFrame(hourly_passers).fillna(0).reset_index()
        result_passers.columns.name = None
        result_passers = result_passers.rename(columns={'index': 'hour'})
        
        return {
            'total': result_total,
            'visitors': result_visitors,
            'passers': result_passers
        }
    
    def compare_period_traffic(self, store_positions: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        시간대(period)별 방문자 수 비교
        
        Returns:
            DataFrame (period, store1, store2, ...)
        """
        period_data = {}
        
        for store_name, positions_df in store_positions.items():
            if len(positions_df) == 0:
                continue
            
            positions_df['period'] = positions_df['time_index'].apply(self._time_index_to_period)
            
            period_visitors = positions_df.groupby('period')['mac_address'].nunique()
            period_data[store_name] = period_visitors
        
        result = pd.DataFrame(period_data)
        result.index.name = 'period'
        result = result.fillna(0).reset_index()
        
        return result
    
    def compare_weekday_traffic(self, store_positions: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        요일별 방문자 수 비교
        
        Args:
            store_positions: {store_name: positions_df} (date 컬럼 필수)
            
        Returns:
            DataFrame (weekday, store1, store2, ...)
        """
        weekday_data = {}
        
        for store_name, positions_df in store_positions.items():
            if len(positions_df) == 0 or 'date' not in positions_df.columns:
                continue
            
            positions_df['weekday'] = positions_df['date'].apply(
                lambda x: x.weekday() if isinstance(x, datetime) else None
            )
            
            weekday_visitors = positions_df.groupby('weekday')['mac_address'].nunique()
            weekday_data[store_name] = weekday_visitors
        
        result = pd.DataFrame(weekday_data)
        result.index.name = 'weekday'
        result = result.fillna(0).reset_index()
        
        return result
    
    def compare_weekend_vs_weekday(self, store_positions: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        주중/주말 비교
        
        Returns:
            DataFrame (day_type, store1, store2, ...)
        """
        day_type_data = {}
        
        for store_name, positions_df in store_positions.items():
            if len(positions_df) == 0 or 'date' not in positions_df.columns:
                continue
            
            positions_df['is_weekend'] = positions_df['date'].apply(
                lambda x: x.weekday() >= 5 if isinstance(x, datetime) else False
            )
            
            weekend_visitors = positions_df[positions_df['is_weekend']]['mac_address'].nunique()
            weekday_visitors = positions_df[~positions_df['is_weekend']]['mac_address'].nunique()
            
            day_type_data[store_name] = {
                'Weekday': weekday_visitors,
                'Weekend': weekend_visitors
            }
        
        result = pd.DataFrame(day_type_data).T
        result.index.name = 'store'
        result = result.reset_index()
        
        return result
    
    def compare_dwell_time_distribution(self, store_positions: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        체류 시간 분포 비교
        
        Returns:
            DataFrame (duration_category, store1, store2, ...)
        """
        duration_data = {}
        
        for store_name, positions_df in store_positions.items():
            if len(positions_df) == 0:
                continue
            
            # 각 MAC별 체류 시간 계산
            dwell_times = []
            for mac in positions_df['mac_address'].unique():
                mac_data = positions_df[positions_df['mac_address'] == mac]
                time_range = mac_data['time_index'].max() - mac_data['time_index'].min()
                dwell_time_minutes = (time_range * self.time_unit) / 60
                dwell_times.append(dwell_time_minutes)
            
            # 카테고리 분류
            dwell_times = np.array(dwell_times)
            categories = {
                'Very Short (<3min)': np.sum(dwell_times < 3),
                'Short (3-10min)': np.sum((dwell_times >= 3) & (dwell_times < 10)),
                'Medium (10-30min)': np.sum((dwell_times >= 10) & (dwell_times < 30)),
                'Long (30-60min)': np.sum((dwell_times >= 30) & (dwell_times < 60)),
                'Very Long (60min+)': np.sum(dwell_times >= 60)
            }
            
            duration_data[store_name] = categories
        
        result = pd.DataFrame(duration_data).T
        result.index.name = 'store'
        result = result.reset_index()
        
        return result
    
    def calculate_movement_stats(self, positions_df: pd.DataFrame) -> Dict:
        """
        이동 통계 계산
        
        Returns:
            {
                'avg_distance': 평균 이동 거리,
                'total_distance': 총 이동 거리,
                'avg_speed': 평균 속도 (픽셀/초)
            }
        """
        if len(positions_df) == 0:
            return {
                'avg_distance': 0,
                'total_distance': 0,
                'avg_speed': 0
            }
        
        total_distances = []
        
        for mac in positions_df['mac_address'].unique():
            mac_data = positions_df[positions_df['mac_address'] == mac].sort_values('time_index')
            
            if len(mac_data) < 2:
                continue
            
            # 이동 거리 계산
            total_distance = 0
            for i in range(len(mac_data) - 1):
                x1, y1 = mac_data.iloc[i]['x'], mac_data.iloc[i]['y']
                x2, y2 = mac_data.iloc[i+1]['x'], mac_data.iloc[i+1]['y']
                distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                total_distance += distance
            
            total_distances.append(total_distance)
        
        avg_distance = np.mean(total_distances) if total_distances else 0
        total_distance = np.sum(total_distances)
        
        # 평균 속도 (대략적)
        if len(positions_df) > 0:
            total_time = positions_df['time_index'].max() - positions_df['time_index'].min()
            total_time_seconds = total_time * self.time_unit
            avg_speed = total_distance / total_time_seconds if total_time_seconds > 0 else 0
        else:
            avg_speed = 0
        
        return {
            'avg_distance': avg_distance,
            'total_distance': total_distance,
            'avg_speed': avg_speed
        }
