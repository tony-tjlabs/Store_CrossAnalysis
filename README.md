# Cross-Store Analysis System

🏪 다중 매장 비교 분석 대시보드 시스템

## 개요

여러 매장의 BLE 실내 위치 데이터를 비교 분석하는 Streamlit 기반 대시보드입니다.

### 주요 기능

1. **📊 Overview** - 매장 정보 및 데이터 가용성 확인
2. **📅 Daily Comparison** - 특정 날짜의 매장 간 비교
3. **📆 Weekly Comparison** - 주간 패턴 및 요일별 분석
4. **🕐 Period Comparison** - 시간대별 트래픽 비교

## 프로젝트 구조

```
Code_CrossAnalysis/
├── Data/                          # 데이터 폴더
│   └── ChamYakSa/                # 기본 데이터 세트
│       ├── Seoungbuk1/           # 매장 1
│       │   ├── map.png
│       │   ├── swards.csv
│       │   └── YYYY-MM-DD_parsing.csv
│       ├── Starfield_Suwon/      # 매장 2
│       └── Tyranno_Yongin/       # 매장 3
├── src/                          # 소스 코드
│   ├── config/                   # 설정
│   │   └── settings.py
│   ├── data_loader/              # 데이터 로더
│   │   └── multi_store_loader.py
│   ├── localization/             # 위치 계산
│   │   └── device_localizer.py
│   ├── analytics/                # 분석 엔진
│   │   └── comparator.py
│   ├── visualization/            # 시각화
│   │   └── multi_store_visualizer.py
│   ├── ui/                       # UI 페이지
│   │   └── pages.py
│   └── utils/                    # 유틸리티
│       └── helpers.py
├── main.py                       # 메인 애플리케이션
├── requirements.txt              # 의존성
└── README.md                     # 이 파일
```

## 설치

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 패키지 목록

- streamlit >= 1.28.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- plotly >= 5.14.0
- Pillow >= 10.0.0

## 실행 방법

### Streamlit 대시보드 실행

```bash
cd Code_CrossAnalysis
streamlit run main.py
```

또는

```bash
python -m streamlit run main.py
```

## 사용 방법

### 1. 데이터 폴더 로드

1. 사이드바에서 데이터 폴더 경로 입력 (예: `Data/ChamYakSa`)
2. **"Load Data Folder"** 버튼 클릭
3. 감지된 매장 목록 확인

### 2. Overview 페이지

- 각 매장의 정보 확인
- 사용 가능한 날짜 확인
- 공통 날짜 확인

### 3. Daily Comparison 페이지

1. 비교할 매장 선택
2. 분석할 날짜 선택
3. **"Calculate Positions"** 버튼 클릭
4. 결과 확인:
   - 기본 통계 (방문자 수, 체류 시간 등)
   - 지도 비교
   - 히트맵 비교
   - 시간대별 트래픽

### 4. Weekly Comparison 페이지

1. 매장 선택
2. 날짜 범위 선택 (시작일 ~ 종료일)
3. **"Analyze Week"** 버튼 클릭
4. 결과 확인:
   - 요일별 비교
   - 주중/주말 비교
   - 체류 시간 분포

## 데이터 형식

### 매장 폴더 구조

각 매장 폴더는 다음 파일을 포함해야 합니다:

```
StoreName/
├── map.png                       # 매장 지도 이미지
├── swards.csv                    # S-Ward 설정
└── YYYY-MM-DD_parsing.csv       # Raw RSSI 데이터
```

### swards.csv 형식

```csv
name,description,x,y
2100011A,"",1711,1278
2100011B,"",1736,1898
```

- `name`: S-Ward ID
- `description`: 설명 (선택)
- `x`, `y`: 픽셀 좌표

### YYYY-MM-DD_parsing.csv 형식

```csv
time_index,sward_name,mac_address,type,rssi
8040,2100011D,67:21:08:E8:5F:2A,1,-65
8041,2100011D,31:39:7F:A2:AA:03,10,-85
```

- `time_index`: 10초 단위 시간 (1 = 00:00:10)
- `sward_name`: 신호를 수신한 S-Ward ID
- `mac_address`: 디바이스 MAC 주소
- `type`: 디바이스 타입 (1=iPhone, 10=Android, 32=T-Ward, 101=Trace)
- `rssi`: 신호 강도 (dBm)

## 주요 알고리즘

### 위치 계산 (DeviceLocalizer)

RSSI 기반 삼변측량:
- 1개 S-Ward: 원주상 위치
- 2개 S-Ward: 가중 내분점
- 3개 이상: 가중 중심
- EMA 스무딩 적용 (alpha=0.3)

### 비교 분석 (StoreComparator)

- 기본 통계: 방문자 수, 체류 시간, 피크 시간
- 시간대별: 1시간 단위 방문자 수
- 요일별: 월~일 패턴 분석
- 주중/주말: 평일 vs 주말 비교
- 체류 시간 분포: 5단계 분류

## 성능 최적화

### 캐싱

- Streamlit `@st.cache_data` 사용
- 데이터 로드, 위치 계산 결과 캐싱
- TTL: 3600초 (1시간)

### 대용량 파일 처리

- 50MB 이상 파일은 청크 단위 로드
- 청크 크기: 100,000 레코드
- 시간 범위 필터링 지원

### Session State

- 버튼 클릭 시 화면 리셋 방지
- 계산 결과 보존
- 탭 전환 시 데이터 유지

## 개발자 가이드

### 새로운 분석 기능 추가

1. `src/analytics/comparator.py`에 분석 메서드 추가
2. `src/visualization/multi_store_visualizer.py`에 시각화 메서드 추가
3. `src/ui/pages.py`에 새로운 페이지 함수 추가
4. `main.py`에서 탭 추가

### 재사용 가능한 모듈

각 모듈은 독립적으로 사용 가능:

```python
# 데이터 로더
from src.data_loader import MultiStoreLoader
loader = MultiStoreLoader(Path("Data/ChamYakSa"))

# 위치 계산
from src.localization import DeviceLocalizer
localizer = DeviceLocalizer(swards_df, alpha=0.3)
positions = localizer.calculate_positions(rawdata)

# 비교 분석
from src.analytics import StoreComparator
comparator = StoreComparator()
stats = comparator.calculate_basic_stats(positions, "Store1")
```

## 문제 해결

### 데이터가 로드되지 않음

1. 폴더 경로 확인
2. 매장 폴더 내 파일 확인 (map.png, swards.csv, *_parsing.csv)
3. CSV 파일 형식 확인

### 위치 계산이 느림

1. 날짜 범위 줄이기
2. 시간 범위 필터링 사용
3. 매장 수 줄이기

### 메모리 부족

1. 한 번에 분석하는 날짜 수 줄이기
2. 청크 크기 조정 (settings.py의 CHUNK_SIZE)
3. 캐시 클리어 (Streamlit 상단 메뉴)

## 라이선스

Internal Use Only

## 문의

프로젝트 관련 문의사항은 개발팀에 연락 바랍니다.
