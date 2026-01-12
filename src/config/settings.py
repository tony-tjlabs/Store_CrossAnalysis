"""
Cross-Store Analysis System - Configuration
전역 설정 및 상수 정의
"""
from pathlib import Path

# ==================== 경로 설정 ====================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "Data"

# ==================== Streamlit 페이지 설정 ====================
PAGE_CONFIG = {
    "page_title": "Cross-Store Analysis Dashboard",
    "page_icon": "🏪",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ==================== 디바이스 타입 정의 ====================
DEVICE_TYPES = {
    1: {"name": "iPhone", "color": "#00FF00", "marker": "o"},
    10: {"name": "Android", "color": "#0000FF", "marker": "s"},
    32: {"name": "T-Ward", "color": "#800080", "marker": "^"},
    101: {"name": "Trace", "color": "#FF0000", "marker": "d"}
}

# ==================== 시각화 설정 ====================
# S-Ward 색상 (매장별 구분)
STORE_COLORS = {
    "store_1": "#FF6B6B",  # Red
    "store_2": "#4ECDC4",  # Teal
    "store_3": "#FFE66D"   # Yellow
}

# 포인트 크기
SWARD_RADIUS = 8
DEVICE_RADIUS = 3

# 지도 투명도
MAP_ALPHA = 0.7

# ==================== 분석 설정 ====================
# 시간 관련
TIME_UNIT_SECONDS = 10  # time_index 1 = 10초
SECONDS_PER_HOUR = 3600
TIME_INDEX_PER_HOUR = SECONDS_PER_HOUR // TIME_UNIT_SECONDS  # 360

# 영업 시간 (time_index 기준)
BUSINESS_HOURS = {
    "open": 0,      # 00:00 (0시)
    "close": 4320   # 12:00 (43200초 / 10 = 4320)
}

# 시간대 정의 (time_index 기준)
TIME_PERIODS = {
    "early_morning": (0, 540),       # 00:00 ~ 01:30
    "morning": (540, 1080),          # 01:30 ~ 03:00
    "late_morning": (1080, 1620),    # 03:00 ~ 04:30
    "lunch": (1620, 2160),           # 04:30 ~ 06:00
    "afternoon": (2160, 2700),       # 06:00 ~ 07:30
    "late_afternoon": (2700, 3240),  # 07:30 ~ 09:00
    "evening": (3240, 3780),         # 09:00 ~ 10:30
    "night": (3780, 4320)            # 10:30 ~ 12:00
}

# 요일 매핑 (한글)
WEEKDAY_NAMES_KR = {
    0: "월요일",
    1: "화요일",
    2: "수요일",
    3: "목요일",
    4: "금요일",
    5: "토요일",
    6: "일요일"
}

WEEKDAY_NAMES_EN = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

# ==================== 위치 계산 설정 ====================
# RSSI → 거리 변환 파라미터
RSSI_DISTANCE_REF = {
    "rssi_near": -60,    # -60 dBm
    "dist_near": 2.0,    # 2m
    "rssi_far": -80,     # -80 dBm
    "dist_far": 10.0     # 10m
}

# EMA 스무딩 계수
EMA_ALPHA = 0.3  # 현재 30% + 이전 70%

# ==================== 성능 최적화 설정 ====================
# 청크 크기 (대용량 파일 처리)
CHUNK_SIZE = 100000

# 캐싱 설정
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1시간

# 병렬 처리
MAX_WORKERS = 4

# ==================== UI 설정 ====================
# 매장 이름 표시 최대 길이
MAX_STORE_NAME_LENGTH = 20

# 차트 기본 크기
CHART_HEIGHT = 400
CHART_WIDTH = 600

# ==================== 분석 메트릭 설정 ====================
# 체류 시간 임계값 (time_index 단위)
MIN_DWELL_TIME = 6  # 60초 (6 * 10초)
SHORT_VISIT = 18    # 3분
MEDIUM_VISIT = 60   # 10분
LONG_VISIT = 180    # 30분

# 이동 거리 임계값 (픽셀)
MIN_MOVEMENT = 10.0
ACTIVE_MOVEMENT = 50.0
