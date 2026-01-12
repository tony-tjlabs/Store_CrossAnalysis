"""
Device Localizer - 재사용 가능한 위치 계산 모듈
Code_DeepSpace의 알고리즘을 기반으로 구현
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
import streamlit as st


class DeviceLocalizer:
    """
    RSSI 기반 디바이스 위치 계산
    
    알고리즘:
    - 1개 S-Ward: 원주상 랜덤 위치
    - 2개 S-Ward: 가중 내분점
    - 3개 이상: 가중 중심 (삼변측량)
    - EMA 스무딩 적용
    """
    
    def __init__(self, sward_config: pd.DataFrame, alpha: float = 0.3):
        """
        Args:
            sward_config: S-Ward 정보 (name, x, y)
            alpha: EMA 스무딩 계수 (0.3 권장)
        """
        # S-Ward 설정
        id_col = 'sward_id' if 'sward_id' in sward_config.columns else 'name'
        self.sward_config = sward_config.set_index(id_col)
        self.alpha = alpha
        self.device_positions = {}  # 디바이스별 이전 위치 저장
        
    def rssi_to_distance(self, rssi: float) -> float:
        """
        RSSI → 거리 변환
        
        -60 dBm = 2m, -80 dBm = 10m 기준 선형 보간
        """
        if rssi >= -60:
            return 2.0
        elif rssi <= -80:
            return 10.0
        else:
            return 2.0 + (10.0 - 2.0) * (-60 - rssi) / (-60 - (-80))
    
    def rssi_to_weight(self, rssi: float) -> float:
        """
        RSSI → 가중치 변환
        
        강한 신호일수록 높은 가중치
        """
        # RSSI를 0~1 범위로 정규화 (-40 ~ -100)
        normalized = (-40 - rssi) / (-40 - (-100))
        normalized = np.clip(normalized, 0, 1)
        
        # 역수로 변환 (강한 신호 = 높은 가중치)
        weight = 1.0 / (normalized + 0.1)
        
        return weight
    
    def calculate_position_single_sward(self, sward_name: str, rssi: float, 
                                       mac_address: str = None) -> Tuple[float, float]:
        """단일 S-Ward 수신 시 위치 계산"""
        if sward_name not in self.sward_config.index:
            return None, None
            
        sward_pos = self.sward_config.loc[sward_name]
        distance = self.rssi_to_distance(rssi)
        
        # 이전 위치가 있으면 그 방향 유지
        if mac_address and mac_address in self.device_positions:
            prev_x, prev_y = self.device_positions[mac_address]
            sward_x, sward_y = float(sward_pos['x']), float(sward_pos['y'])
            
            dx = prev_x - sward_x
            dy = prev_y - sward_y
            prev_dist = np.sqrt(dx**2 + dy**2)
            
            if prev_dist > 0.1:
                angle = np.arctan2(dy, dx)
            else:
                angle = np.random.uniform(0, 2 * np.pi)
        else:
            angle = np.random.uniform(0, 2 * np.pi)
        
        x = float(sward_pos['x']) + distance * np.cos(angle)
        y = float(sward_pos['y']) + distance * np.sin(angle)
        
        return x, y
    
    def calculate_position_two_swards(self, sward_data: List[Tuple[str, float]]) -> Tuple[float, float]:
        """두 개 S-Ward 수신 시 가중 내분점"""
        sward1_name, rssi1 = sward_data[0]
        sward2_name, rssi2 = sward_data[1]
        
        if sward1_name not in self.sward_config.index or sward2_name not in self.sward_config.index:
            return None, None
        
        pos1 = self.sward_config.loc[sward1_name]
        pos2 = self.sward_config.loc[sward2_name]
        
        # 거리 계산
        dist1 = self.rssi_to_distance(rssi1)
        dist2 = self.rssi_to_distance(rssi2)
        
        # 가중치 (거리 역수)
        w1 = 1.0 / dist1
        w2 = 1.0 / dist2
        total_weight = w1 + w2
        
        x = (float(pos1['x']) * w1 + float(pos2['x']) * w2) / total_weight
        y = (float(pos1['y']) * w1 + float(pos2['y']) * w2) / total_weight
        
        return x, y
    
    def calculate_position_multiple_swards(self, sward_data: List[Tuple[str, float]]) -> Tuple[float, float]:
        """3개 이상 S-Ward 수신 시 가중 중심"""
        valid_swards = []
        
        for sward_name, rssi in sward_data:
            if sward_name in self.sward_config.index:
                valid_swards.append((sward_name, rssi))
        
        if not valid_swards:
            return None, None
        
        # 가중 중심 계산
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for sward_name, rssi in valid_swards:
            pos = self.sward_config.loc[sward_name]
            weight = self.rssi_to_weight(rssi)
            
            weighted_x += float(pos['x']) * weight
            weighted_y += float(pos['y']) * weight
            total_weight += weight
        
        if total_weight == 0:
            return None, None
        
        x = weighted_x / total_weight
        y = weighted_y / total_weight
        
        return x, y
    
    def apply_ema_smoothing(self, mac_address: str, current_x: float, 
                           current_y: float) -> Tuple[float, float]:
        """
        EMA 스무딩 적용
        
        새 위치 = alpha * 현재 + (1-alpha) * 이전
        """
        if mac_address in self.device_positions:
            prev_x, prev_y = self.device_positions[mac_address]
            
            smoothed_x = self.alpha * current_x + (1 - self.alpha) * prev_x
            smoothed_y = self.alpha * current_y + (1 - self.alpha) * prev_y
        else:
            smoothed_x, smoothed_y = current_x, current_y
        
        # 이전 위치 업데이트
        self.device_positions[mac_address] = (smoothed_x, smoothed_y)
        
        return smoothed_x, smoothed_y
    
    def calculate_positions(self, rawdata: pd.DataFrame, 
                          apply_smoothing: bool = True) -> pd.DataFrame:
        """
        전체 rawdata에서 디바이스 위치 계산
        
        Args:
            rawdata: Raw RSSI 데이터
            apply_smoothing: EMA 스무딩 적용 여부
            
        Returns:
            positions_df (time_index, mac_address, device_type, x, y, sward_count)
        """
        # 디바이스 위치 초기화
        self.device_positions = {}
        
        positions = []
        
        # 각 time_index, mac_address 조합별로 처리
        grouped = rawdata.groupby(['time_index', 'mac_address'])
        
        for (time_index, mac_address), group in grouped:
            device_type = group['type'].iloc[0]
            
            # S-Ward별 RSSI 수집
            sward_data = []
            for _, row in group.iterrows():
                sward_data.append((row['sward_name'], row['rssi']))
            
            sward_count = len(sward_data)
            
            # 위치 계산
            if sward_count == 1:
                x, y = self.calculate_position_single_sward(
                    sward_data[0][0], sward_data[0][1], mac_address
                )
            elif sward_count == 2:
                x, y = self.calculate_position_two_swards(sward_data)
            else:
                x, y = self.calculate_position_multiple_swards(sward_data)
            
            if x is None or y is None:
                continue
            
            # EMA 스무딩
            if apply_smoothing:
                x, y = self.apply_ema_smoothing(mac_address, x, y)
            
            positions.append({
                'time_index': time_index,
                'mac_address': mac_address,
                'device_type': device_type,
                'x': x,
                'y': y,
                'sward_count': sward_count
            })
        
        return pd.DataFrame(positions)


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_positions_cached(rawdata_hash: int, sward_config_hash: int,
                               rawdata: pd.DataFrame, sward_config: pd.DataFrame,
                               alpha: float = 0.3) -> pd.DataFrame:
    """
    위치 계산 (캐싱 지원)
    
    Note: Streamlit 캐싱을 위해 hash 값을 파라미터로 받음
    """
    localizer = DeviceLocalizer(sward_config, alpha)
    return localizer.calculate_positions(rawdata, apply_smoothing=True)
