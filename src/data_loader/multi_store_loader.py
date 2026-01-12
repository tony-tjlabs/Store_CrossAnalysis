"""
Multi-Store Data Loader
여러 매장의 데이터를 효율적으로 로드하고 관리
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import streamlit as st
from PIL import Image


class MultiStoreLoader:
    """
    다중 매장 데이터 로더
    
    기능:
    1. ChamYakSa 폴더 내 모든 매장 자동 감지
    2. 각 매장별 데이터 로드 (map, swards, rawdata)
    3. 날짜별 데이터 필터링
    4. 캐싱을 통한 성능 최적화
    """
    
    def __init__(self, base_folder: Path):
        """
        Args:
            base_folder: ChamYakSa 폴더 경로
        """
        self.base_folder = Path(base_folder)
        
        if not self.base_folder.exists():
            raise FileNotFoundError(f"Base folder not found: {base_folder}")
        
        # 매장 목록 자동 탐지
        self.stores = self._detect_stores()
        
        if not self.stores:
            raise ValueError(f"No store folders found in {base_folder}")
        
        print(f"✅ Detected {len(self.stores)} stores: {list(self.stores.keys())}")
    
    def _detect_stores(self) -> Dict[str, Path]:
        """
        base_folder 내 모든 매장 폴더 탐지
        
        Returns:
            {store_name: store_path}
        """
        stores = {}
        
        for item in self.base_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                stores[item.name] = item
        
        return stores
    
    def get_store_info(self, store_name: str) -> Dict:
        """
        매장 정보 조회
        
        Returns:
            {
                'name': 매장명,
                'path': 경로,
                'has_map': 지도 존재 여부,
                'has_swards': S-Ward 설정 존재 여부,
                'available_dates': 사용 가능한 날짜 목록
            }
        """
        if store_name not in self.stores:
            return None
        
        store_path = self.stores[store_name]
        
        # 지도 파일 확인
        map_file = store_path / "map.png"
        has_map = map_file.exists()
        
        # S-Ward 설정 파일 확인
        sward_file = store_path / "swards.csv"
        has_swards = sward_file.exists()
        
        # 사용 가능한 날짜 탐지
        available_dates = self._get_available_dates(store_path)
        
        return {
            'name': store_name,
            'path': store_path,
            'has_map': has_map,
            'has_swards': has_swards,
            'available_dates': sorted(available_dates)
        }
    
    def _get_available_dates(self, store_path: Path) -> List[datetime]:
        """
        매장 폴더 내 사용 가능한 날짜 목록 추출
        
        파일명 형식: 2025-11-10_parsing.csv
        """
        dates = []
        
        for file in store_path.glob("*_parsing.csv"):
            try:
                # 파일명에서 날짜 추출
                date_str = file.stem.replace("_parsing", "")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date)
            except Exception as e:
                continue
        
        return dates
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def load_map(_self, store_name: str) -> Optional[Image.Image]:
        """
        매장 지도 이미지 로드
        
        Args:
            store_name: 매장명
            
        Returns:
            PIL Image 또는 None
        """
        if store_name not in _self.stores:
            return None
        
        map_file = _self.stores[store_name] / "map.png"
        
        if not map_file.exists():
            return None
        
        try:
            return Image.open(map_file)
        except Exception as e:
            st.error(f"Failed to load map for {store_name}: {e}")
            return None
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def load_swards(_self, store_name: str) -> Optional[pd.DataFrame]:
        """
        S-Ward 설정 로드
        
        Args:
            store_name: 매장명
            
        Returns:
            DataFrame (columns: name, description, x, y) 또는 None
        """
        if store_name not in _self.stores:
            return None
        
        sward_file = _self.stores[store_name] / "swards.csv"
        
        if not sward_file.exists():
            return None
        
        try:
            df = pd.read_csv(sward_file)
            
            # 필수 컬럼 확인
            required_cols = ['name', 'x', 'y']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing columns in swards.csv: {missing_cols}")
                return None
            
            # description 컬럼이 없으면 추가
            if 'description' not in df.columns:
                df['description'] = ''
            
            return df
            
        except Exception as e:
            st.error(f"Failed to load swards for {store_name}: {e}")
            return None
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def load_rawdata(_self, store_name: str, date: datetime, 
                     time_range: Optional[Tuple[int, int]] = None) -> Optional[pd.DataFrame]:
        """
        Raw 데이터 로드 (특정 날짜)
        
        Args:
            store_name: 매장명
            date: 날짜
            time_range: 시간 범위 (start_time_index, end_time_index)
            
        Returns:
            DataFrame (columns: time_index, sward_name, mac_address, type, rssi) 또는 None
        """
        if store_name not in _self.stores:
            return None
        
        # 날짜 문자열로 변환 (str 또는 datetime 모두 지원)
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime("%Y-%m-%d")
        
        rawdata_file = _self.stores[store_name] / f"{date_str}_parsing.csv"
        
        if not rawdata_file.exists():
            return None
        
        try:
            # 파일 크기 확인
            file_size_mb = rawdata_file.stat().st_size / (1024 * 1024)
            
            # 대용량 파일 처리
            if file_size_mb > 50:
                df = _self._load_large_file_chunked(rawdata_file, time_range)
            else:
                df = pd.read_csv(rawdata_file, low_memory=False)
                
                # 시간 필터링
                if time_range is not None:
                    start_idx, end_idx = time_range
                    df = df[(df['time_index'] >= start_idx) & (df['time_index'] <= end_idx)]
            
            return df
            
        except Exception as e:
            st.error(f"Failed to load rawdata for {store_name} on {date_str}: {e}")
            return None
    
    def _load_large_file_chunked(self, file_path: Path, 
                                 time_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
        """
        대용량 파일을 청크 단위로 로드
        
        Args:
            file_path: 파일 경로
            time_range: 시간 범위 (start, end)
            
        Returns:
            필터링된 DataFrame
        """
        chunks = []
        chunk_size = 100000
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
            # 시간 필터링
            if time_range is not None:
                start_idx, end_idx = time_range
                chunk = chunk[(chunk['time_index'] >= start_idx) & (chunk['time_index'] <= end_idx)]
            
            if len(chunk) > 0:
                chunks.append(chunk)
        
        if chunks:
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def load_multiple_dates(self, store_name: str, dates: List[datetime],
                           time_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
        """
        여러 날짜의 데이터를 한번에 로드
        
        Args:
            store_name: 매장명
            dates: 날짜 목록
            time_range: 시간 범위
            
        Returns:
            결합된 DataFrame (date 컬럼 추가됨)
        """
        all_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, date in enumerate(dates):
            status_text.text(f"Loading {store_name} - {date.strftime('%Y-%m-%d')}...")
            
            df = self.load_rawdata(store_name, date, time_range)
            
            if df is not None and len(df) > 0:
                df['date'] = date
                all_data.append(df)
            
            progress_bar.progress((i + 1) / len(dates))
        
        progress_bar.empty()
        status_text.empty()
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def get_common_dates(self, store_names: Optional[List[str]] = None) -> List[datetime]:
        """
        여러 매장에 공통으로 존재하는 날짜 찾기
        
        Args:
            store_names: 비교할 매장 목록 (None이면 전체)
            
        Returns:
            공통 날짜 목록
        """
        if store_names is None:
            store_names = list(self.stores.keys())
        
        # 첫 번째 매장의 날짜로 초기화
        common_dates = set(self.get_store_info(store_names[0])['available_dates'])
        
        # 다른 매장들과 교집합
        for store_name in store_names[1:]:
            store_dates = set(self.get_store_info(store_name)['available_dates'])
            common_dates = common_dates.intersection(store_dates)
        
        return sorted(list(common_dates))
