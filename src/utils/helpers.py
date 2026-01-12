"""
Utility Functions
"""
from datetime import datetime
from typing import List


def time_index_to_time_str(time_index: int) -> str:
    """
    time_index를 시간 문자열로 변환
    
    Args:
        time_index: 10초 단위 인덱스
        
    Returns:
        "HH:MM:SS" 형식 문자열
    """
    total_seconds = time_index * 10
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def time_str_to_time_index(time_str: str) -> int:
    """
    시간 문자열을 time_index로 변환
    
    Args:
        time_str: "HH:MM" or "HH:MM:SS" 형식
        
    Returns:
        time_index (10초 단위)
    """
    parts = time_str.split(':')
    
    if len(parts) == 2:
        hours, minutes = int(parts[0]), int(parts[1])
        seconds = 0
    elif len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    else:
        raise ValueError(f"Invalid time format: {time_str}")
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds // 10


def get_weekday_name(date: datetime, lang: str = 'kr') -> str:
    """
    날짜의 요일명 반환
    
    Args:
        date: datetime 객체
        lang: 'kr' 또는 'en'
        
    Returns:
        요일명
    """
    weekday = date.weekday()
    
    if lang == 'kr':
        names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    else:
        names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return names[weekday]


def is_weekend(date: datetime) -> bool:
    """주말 여부 확인"""
    return date.weekday() >= 5


def format_duration(minutes: float) -> str:
    """
    분 단위 시간을 읽기 쉬운 형식으로 변환
    
    Args:
        minutes: 분 단위 시간
        
    Returns:
        "1h 23m" 형식 문자열
    """
    if minutes < 1:
        return f"{int(minutes * 60)}s"
    elif minutes < 60:
        return f"{int(minutes)}m"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"


def calculate_data_hash(df) -> int:
    """
    DataFrame의 해시값 계산 (캐싱용)
    
    Args:
        df: pandas DataFrame
        
    Returns:
        hash value
    """
    try:
        return hash(tuple(df.values.tobytes()))
    except:
        return hash(str(df.shape) + str(df.columns.tolist()))
