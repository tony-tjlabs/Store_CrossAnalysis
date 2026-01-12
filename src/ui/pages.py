"""
UI Pages - 각 분석 페이지 구현
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data_loader import MultiStoreLoader
from src.localization import DeviceLocalizer
from src.analytics import StoreComparator, VisitorClassifier, MACStitcher
from src.visualization import MultiStoreVisualizer
from src.utils import time_index_to_time_str, get_weekday_name, format_duration


def initialize_session_state():
    """Session state 초기화 (리셋 방지)"""
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    
    if 'selected_stores' not in st.session_state:
        st.session_state.selected_stores = []
    
    if 'calculated_positions' not in st.session_state:
        st.session_state.calculated_positions = {}
    
    if 'current_date' not in st.session_state:
        st.session_state.current_date = None
    
    if 'time_range' not in st.session_state:
        st.session_state.time_range = (0, 4320)


def overview_page():
    """메인 대시보드 - 전체 개요"""
    st.header("📊 Store Overview")
    
    if st.session_state.data_loader is None:
        st.warning("⚠️ Please select a data folder in the sidebar first.")
        return
    
    loader = st.session_state.data_loader
    
    # 매장 선택
    all_stores = list(loader.stores.keys())
    
    st.subheader("Select Stores to Compare")
    selected_stores = st.multiselect(
        "Choose stores:",
        options=all_stores,
        default=all_stores[:3] if len(all_stores) >= 3 else all_stores,
        key='overview_store_select'
    )
    
    if not selected_stores:
        st.info("Please select at least one store.")
        return
    
    # 매장 정보 표시
    st.subheader("Store Information")
    
    cols = st.columns(len(selected_stores))
    
    for idx, store_name in enumerate(selected_stores):
        with cols[idx]:
            info = loader.get_store_info(store_name)
            
            st.markdown(f"### {store_name}")
            st.metric("Available Dates", len(info['available_dates']))
            
            if info['available_dates']:
                date_range = f"{info['available_dates'][0].strftime('%Y-%m-%d')} ~ {info['available_dates'][-1].strftime('%Y-%m-%d')}"
                st.text(date_range)
            
            st.text(f"Map: {'✅' if info['has_map'] else '❌'}")
            st.text(f"S-Wards: {'✅' if info['has_swards'] else '❌'}")
            
            # S-Ward 개수
            if info['has_swards']:
                swards = loader.load_swards(store_name)
                st.text(f"S-Ward Count: {len(swards)}")
    
    # 공통 날짜 확인
    st.subheader("Common Available Dates")
    common_dates = loader.get_common_dates(selected_stores)
    
    if common_dates:
        st.success(f"✅ Found {len(common_dates)} common dates across selected stores")
        
        # 날짜 범위 표시
        date_range_text = f"{common_dates[0].strftime('%Y-%m-%d')} ~ {common_dates[-1].strftime('%Y-%m-%d')}"
        st.info(f"📅 Date Range: {date_range_text}")
    else:
        st.error("❌ No common dates found across selected stores")


def daily_comparison_page():
    """일별 비교 페이지"""
    st.header("📅 Daily Comparison")
    
    if st.session_state.data_loader is None:
        st.warning("⚠️ Please select a data folder in the sidebar first.")
        return
    
    loader = st.session_state.data_loader
    comparator = StoreComparator()
    visualizer = MultiStoreVisualizer()
    
    # 매장 선택
    all_stores = list(loader.stores.keys())
    selected_stores = st.multiselect(
        "Select stores to compare:",
        options=all_stores,
        default=all_stores[:3] if len(all_stores) >= 3 else all_stores,
        key='daily_store_select'
    )
    
    if not selected_stores:
        st.info("Please select at least one store.")
        return
    
    # 공통 날짜 가져오기
    common_dates = loader.get_common_dates(selected_stores)
    
    if not common_dates:
        st.error("No common dates available for selected stores.")
        return
    
    # 날짜 선택 및 옵션
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_date = st.selectbox(
            "Select date:",
            options=common_dates,
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({get_weekday_name(x)})",
            key='daily_date_select'
        )
    
    with col2:
        fast_mode = st.checkbox(
            "⚡ Fast Mode",
            value=False,
            help="빠른 모드: RSSI 유사도 생략 (속도 3배 향상, 정확도 감소). 권장: OFF (정확도 우선)"
        )
    
    with col3:
        # 위치 계산 버튼
        if st.button("🔄 Calculate & Analyze", key='daily_calc_btn', type="primary"):
            st.session_state.current_date = selected_date
            st.session_state.calculated_positions = {}
            st.session_state.visitor_classifications = {}
            st.session_state.mac_stitching_results = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_steps = len(selected_stores) * 3  # 각 매장당 3단계
            current_step = 0
            
            for store_name in selected_stores:
                # 1. 데이터 로드
                status_text.text(f"📂 Loading data for {store_name}...")
                rawdata = loader.load_rawdata(store_name, selected_date)
                swards = loader.load_swards(store_name)
                
                if rawdata is None or swards is None:
                    continue
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                
                # 2. 위치 계산
                status_text.text(f"📍 Calculating positions for {store_name}...")
                localizer = DeviceLocalizer(swards, alpha=0.3)
                positions = localizer.calculate_positions(rawdata)
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                
                # 3. MAC Stitching + 방문자 분류
                status_text.text(f"🔗 MAC Stitching & Visitor Classification for {store_name}...")
                
                # MAC Stitching (fast_mode 적용)
                stitcher = MACStitcher(time_window=60, threshold=0.6, rawdata_df=rawdata, fast_mode=fast_mode)
                features_df, mac_to_journey, journeys_df = stitcher.stitch(positions)
                
                # Journey 기반 방문자 분류
                classifier = VisitorClassifier()
                journey_classification = classifier.classify_with_mac_stitching(
                    rawdata, positions, journeys_df, mac_to_journey
                )
                
                st.session_state.calculated_positions[store_name] = {
                    'positions': positions,
                    'map': loader.load_map(store_name),
                    'swards': swards,
                    'rawdata': rawdata
                }
                st.session_state.visitor_classifications[store_name] = journey_classification
                st.session_state.mac_stitching_results[store_name] = {
                    'features': features_df,
                    'mac_to_journey': mac_to_journey,
                    'journeys': journeys_df
                }
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)
            
            progress_bar.empty()
            status_text.empty()
            st.success("✅ MAC Stitching 완료! 정확한 방문자 수가 계산되었습니다!")
    
    # 계산된 데이터 표시
    if st.session_state.calculated_positions:
        st.markdown("---")
        
        # 방문자 분류 결과 (MAC Stitching 적용)
        if 'visitor_classifications' in st.session_state and st.session_state.visitor_classifications:
            st.subheader("🎯 Visitor Analysis (MAC Stitching 적용)")
            st.caption("⚡ Random MAC 변경을 고려한 정확한 방문자 수")
            
            classifier = VisitorClassifier()
            
            # 주요 메트릭 카드 형태로 표시
            cols = st.columns(len(selected_stores))
            
            for idx, store_name in enumerate(selected_stores):
                if store_name in st.session_state.visitor_classifications:
                    with cols[idx]:
                        journey_classification = st.session_state.visitor_classifications[store_name]
                        stitching_results = st.session_state.mac_stitching_results[store_name]
                        
                        # Journey 기반 통계
                        stats = classifier.get_journey_visitor_stats(journey_classification)
                        
                        st.markdown(f"### {store_name}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🏪 실제 방문자", 
                                     f"{stats['real_visitors']}명",
                                     help=f"Journey 수 (MAC Stitching 적용)")
                        with col2:
                            st.metric("🚶 외부 유동인구", 
                                     f"{stats['passers_by']}명")
                        
                        st.metric("📊 방문자 비율", 
                                 f"{stats['visitor_ratio']*100:.1f}%")
                        
                        # MAC 통합 정보
                        st.caption(f"MAC 통합: 방문자 {stats['avg_mac_per_visitor']:.1f}개/인, 유동인구 {stats['avg_mac_per_passer']:.1f}개/인")
                        st.caption(f"평균 체류시간: {stats['avg_dwell_time_visitors']:.0f}초 (방문자) vs {stats['avg_dwell_time_passers']:.0f}초 (유동인구)")
            
            # 상세 비교 테이블
            st.markdown("#### 📊 Detailed Comparison")
            
            # Journey 기반 비교 데이터 수집
            comparison_data = []
            for store_name in selected_stores:
                if store_name in st.session_state.visitor_classifications:
                    journey_classification = st.session_state.visitor_classifications[store_name]
                    stats = classifier.get_journey_visitor_stats(journey_classification)
                    comparison_data.append({
                        '매장명': store_name,
                        '총 Journey': stats['total_journeys'],
                        '실제 방문자': stats['real_visitors'],
                        '외부 유동인구': stats['passers_by'],
                        '방문자 비율': f"{stats['visitor_ratio']*100:.1f}%",
                        '평균 체류시간(방문자)': f"{stats['avg_dwell_time_visitors']:.0f}초",
                        '평균 체류시간(유동인구)': f"{stats['avg_dwell_time_passers']:.0f}초",
                        '평균 RSSI(방문자)': f"{stats['avg_rssi_visitors']:.1f} dBm",
                        '평균 RSSI(유동인구)': f"{stats['avg_rssi_passers']:.1f} dBm",
                        'MAC/방문자': f"{stats['avg_mac_per_visitor']:.1f}",
                        'MAC/유동인구': f"{stats['avg_mac_per_passer']:.1f}"
                    })
            
            comparison_display = pd.DataFrame(comparison_data)
            st.dataframe(comparison_display, use_container_width=True)
            
            # 시각화: 방문자 vs 유동인구 비교 차트
            import plotly.graph_objects as go
            
            # 숫자 데이터 추출 (차트용)
            chart_data = []
            for store_name in selected_stores:
                if store_name in st.session_state.visitor_classifications:
                    journey_classification = st.session_state.visitor_classifications[store_name]
                    stats = classifier.get_journey_visitor_stats(journey_classification)
                    chart_data.append({
                        'store': store_name,
                        'real_visitors': stats['real_visitors'],
                        'passers_by': stats['passers_by']
                    })
            
            chart_df = pd.DataFrame(chart_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='실제 방문자',
                x=chart_df['store'],
                y=chart_df['real_visitors'],
                marker_color='#4ECDC4',
                text=chart_df['real_visitors'],
                textposition='outside'
            ))
            
            fig.add_trace(go.Bar(
                name='외부 유동인구',
                x=chart_df['store'],
                y=chart_df['passers_by'],
                marker_color='#FFE66D',
                text=chart_df['passers_by'],
                textposition='outside'
            ))
            
            fig.update_layout(
                title='실제 방문자 vs 외부 유동인구 비교 (MAC Stitching 적용)',
                xaxis_title='매장',
                yaxis_title='인원 수 (Journey)',
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
        
        # 기본 통계
        st.subheader("📊 Basic Statistics (Raw MAC Count)")
        
        stats_list = []
        for store_name, data in st.session_state.calculated_positions.items():
            stats = comparator.calculate_basic_stats(data['positions'], store_name)
            stats_list.append(stats)
        
        # 통계 테이블
        stats_df = pd.DataFrame(stats_list)
        st.dataframe(stats_df[['store_name', 'total_visitors', 'total_records', 
                               'avg_dwell_time', 'peak_hour', 'peak_visitors']],
                    use_container_width=True)
        
        # 통계 차트
        if len(stats_list) > 1:
            fig = visualizer.plot_stats_comparison(stats_list)
            st.plotly_chart(fig, use_container_width=True)
        
        # 지도 비교
        st.subheader("🗺️ Map Comparison")
        
        fig = visualizer.plot_maps_side_by_side(st.session_state.calculated_positions)
        if fig:
            st.pyplot(fig)
        
        # 히트맵 비교
        st.subheader("🔥 Heatmap Comparison")
        
        fig = visualizer.plot_heatmap_comparison(st.session_state.calculated_positions, bins=30)
        if fig:
            st.pyplot(fig)
        
        # 시간대별 비교
        st.subheader("⏰ Hourly Traffic Comparison")
        
        # 뷰 모드 선택
        view_mode = st.radio(
            "View Mode:",
            options=["Integrated (by store)", "Separated (by category)"],
            horizontal=True,
            key='hourly_view_mode'
        )
        
        store_positions = {name: data['positions'] 
                          for name, data in st.session_state.calculated_positions.items()}
        
        # rawdata 가져오기 (실시간 분류용)
        store_rawdata = {name: data['rawdata'] 
                        for name, data in st.session_state.calculated_positions.items()
                        if 'rawdata' in data}
        
        hourly_data = comparator.compare_hourly_traffic(store_positions, store_rawdata)
        
        if view_mode == "Integrated (by store)":
            # 매장별로 3가지 카테고리를 두 가지 방식으로 표시
            for store_name in selected_stores:
                st.markdown(f"### 📍 {store_name}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**면적 그래프 (비율 직관성)**")
                    fig_area = visualizer.plot_hourly_comparison_area(hourly_data, store_name)
                    st.plotly_chart(fig_area, use_container_width=True)
                
                with col2:
                    st.markdown("**꺾은선 그래프 (정확한 수치)**")
                    fig_line = visualizer.plot_hourly_comparison_integrated(hourly_data, store_name)
                    st.plotly_chart(fig_line, use_container_width=True)
                
                st.markdown("---")
        else:
            # 카테고리별로 모든 매장 비교
            st.markdown("#### 📊 전체 센싱 인원")
            if not hourly_data['total'].empty:
                fig = visualizer.plot_hourly_comparison(hourly_data['total'], 
                                                       title='Total Sensing - All Stores')
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 🏪 내부 방문자")
            if not hourly_data['visitors'].empty:
                fig = visualizer.plot_hourly_comparison(hourly_data['visitors'], 
                                                       title='Real Visitors - All Stores')
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 🚶 외부 유동인구")
            if not hourly_data['passers'].empty:
                fig = visualizer.plot_hourly_comparison(hourly_data['passers'], 
                                                       title='Foot Traffic (Passers-by) - All Stores')
                st.plotly_chart(fig, use_container_width=True)


def weekly_comparison_page():
    """주간 비교 페이지"""
    st.header("📆 Weekly Comparison")
    
    if st.session_state.data_loader is None:
        st.warning("⚠️ Please select a data folder in the sidebar first.")
        return
    
    loader = st.session_state.data_loader
    comparator = StoreComparator()
    visualizer = MultiStoreVisualizer()
    
    # 매장 선택
    all_stores = list(loader.stores.keys())
    selected_stores = st.multiselect(
        "Select stores:",
        options=all_stores,
        default=all_stores[:3] if len(all_stores) >= 3 else all_stores,
        key='weekly_store_select'
    )
    
    if not selected_stores:
        st.info("Please select at least one store.")
        return
    
    # 공통 날짜
    common_dates = loader.get_common_dates(selected_stores)
    
    if not common_dates:
        st.error("No common dates available.")
        return
    
    # 날짜 범위 선택
    st.subheader("Select Date Range")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.selectbox(
            "Start date:",
            options=common_dates,
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({get_weekday_name(x)})",
            key='weekly_start_date'
        )
    
    with col2:
        end_date = st.selectbox(
            "End date:",
            options=[d for d in common_dates if d >= start_date],
            index=min(6, len([d for d in common_dates if d >= start_date]) - 1),
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({get_weekday_name(x)})",
            key='weekly_end_date'
        )
    
    # 선택된 날짜 범위
    date_range = [d for d in common_dates if start_date <= d <= end_date]
    st.info(f"📅 Selected {len(date_range)} days")
    
    # 분석 버튼
    if st.button("🔄 Analyze Week", key='weekly_analyze_btn', type="primary"):
        with st.spinner("Loading and analyzing data..."):
            all_positions = {}
            
            for store_name in selected_stores:
                # 여러 날짜 데이터 로드
                rawdata = loader.load_multiple_dates(store_name, date_range)
                swards = loader.load_swards(store_name)
                
                if rawdata is None or len(rawdata) == 0 or swards is None:
                    continue
                
                # 위치 계산
                localizer = DeviceLocalizer(swards, alpha=0.3)
                positions = localizer.calculate_positions(rawdata)
                
                all_positions[store_name] = positions
            
            st.session_state.weekly_positions = all_positions
        
        st.success("✅ Analysis completed!")
    
    # 결과 표시
    if 'weekly_positions' in st.session_state and st.session_state.weekly_positions:
        st.markdown("---")
        
        # 요일별 비교
        st.subheader("📊 Weekday Comparison")
        
        weekday_df = comparator.compare_weekday_traffic(st.session_state.weekly_positions)
        
        if not weekday_df.empty:
            fig = visualizer.plot_weekday_comparison(weekday_df)
            st.plotly_chart(fig, use_container_width=True)
        
        # 주중/주말 비교
        st.subheader("🏢 Weekday vs Weekend")
        
        day_type_df = comparator.compare_weekend_vs_weekday(st.session_state.weekly_positions)
        
        if not day_type_df.empty:
            st.dataframe(day_type_df, use_container_width=True)
        
        # 체류 시간 분포
        st.subheader("⏱️ Dwell Time Distribution")
        
        duration_df = comparator.compare_dwell_time_distribution(st.session_state.weekly_positions)
        
        if not duration_df.empty:
            fig = visualizer.plot_dwell_time_distribution(duration_df)
            st.plotly_chart(fig, use_container_width=True)


def period_comparison_page():
    """시간대별 비교 페이지"""
    st.header("🕐 Time Period Comparison")
    
    st.info("Compare traffic patterns across different time periods (morning, afternoon, evening, etc.)")
    
    # 구현 예정
    st.warning("🚧 This page is under construction")


def conversion_analysis_page():
    """🎯 유동/방문 전환율 분석 페이지 (신규)"""
    st.header("🎯 Traffic & Conversion Analysis")
    st.markdown("**유동인구 vs 방문인구** 분석 및 전환율 비교")
    
    if st.session_state.data_loader is None:
        st.warning("⚠️ Please select a data folder in the sidebar first.")
        return
    
    loader = st.session_state.data_loader
    all_stores = list(loader.stores.keys())
    
    # 매장 선택
    st.subheader("1️⃣ Select Stores")
    selected_stores = st.multiselect(
        "Choose stores to compare:",
        options=all_stores,
        default=all_stores[:3] if len(all_stores) >= 3 else all_stores,
        key='conversion_store_select'
    )
    
    if not selected_stores:
        st.info("Please select at least one store.")
        return
    
    # 공통 날짜 확인
    common_dates = loader.get_common_dates(selected_stores)
    
    if not common_dates:
        st.error("❌ No common dates found across selected stores")
        return
    
    # 날짜 선택
    st.subheader("2️⃣ Select Date")
    selected_date = st.selectbox(
        "Choose a date:",
        options=[d.strftime('%Y-%m-%d') for d in common_dates],
        key='conversion_date_select'
    )
    
    # 설정
    st.subheader("3️⃣ Analysis Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        pass_by_threshold = st.slider(
            "Pass-by Threshold (minutes)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="체류시간이 이 값보다 작으면 유동인구로 분류"
        )
    
    with col2:
        ema_alpha = st.slider(
            "EMA Smoothing Alpha",
            min_value=0.1,
            max_value=0.9,
            value=0.3,
            step=0.1,
            help="위치 계산 스무딩 계수"
        )
    
    # 분석 실행
    if st.button("🚀 Analyze Traffic & Conversion", type="primary", key='analyze_conversion_btn'):
        from src.analytics import TrafficAnalyzer
        from src.visualization import MultiStoreVisualizer
        
        with st.spinner("Calculating positions and analyzing traffic..."):
            traffic_analyzer = TrafficAnalyzer(
                pass_by_threshold_minutes=pass_by_threshold,
                time_unit_seconds=10
            )
            
            # 각 매장의 위치 계산
            store_positions = {}
            store_traffic_data = {}
            
            progress_bar = st.progress(0)
            
            for idx, store_name in enumerate(selected_stores):
                # 데이터 로드
                rawdata = loader.load_rawdata(store_name, selected_date)
                swards = loader.load_swards(store_name)
                
                if len(rawdata) == 0 or len(swards) == 0:
                    st.warning(f"⚠️ No data for {store_name}")
                    continue
                
                # 위치 계산
                localizer = DeviceLocalizer(swards, alpha=ema_alpha)
                positions = localizer.calculate_positions(rawdata)
                
                store_positions[store_name] = positions
                
                # 트래픽 분석
                traffic_df = traffic_analyzer.classify_traffic(positions)
                store_traffic_data[store_name] = traffic_df
                
                progress_bar.progress((idx + 1) / len(selected_stores))
            
            # 결과 저장
            st.session_state.conversion_positions = store_positions
            st.session_state.conversion_traffic = store_traffic_data
            st.session_state.conversion_date = selected_date
        
        st.success("✅ Analysis completed!")
    
    # 결과 표시
    if 'conversion_positions' in st.session_state and st.session_state.conversion_positions:
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        from src.analytics import TrafficAnalyzer
        from src.visualization import MultiStoreVisualizer
        
        traffic_analyzer = TrafficAnalyzer(pass_by_threshold_minutes=pass_by_threshold)
        visualizer = MultiStoreVisualizer()
        
        # 1. 전환율 비교 요약
        st.subheader("1️⃣ Conversion Rate Summary")
        
        conversion_comparison = traffic_analyzer.compare_stores_conversion(
            st.session_state.conversion_positions
        )
        
        # 메트릭 표시
        cols = st.columns(len(selected_stores))
        for idx, (_, row) in enumerate(conversion_comparison.iterrows()):
            with cols[idx]:
                st.markdown(f"### {row['store_name']}")
                st.metric("Total Traffic", f"{row['total_traffic']:,}")
                st.metric("Conversion Rate", f"{row['conversion_rate']*100:.1f}%")
                st.metric("Visitors", f"{row['visit_count']:,}")
                st.metric("Pass-by", f"{row['pass_by_count']:,}")
        
        # 2. 전환율 비교 차트
        st.subheader("2️⃣ Conversion Rate Comparison")
        fig_conversion = visualizer.plot_conversion_rate_comparison(conversion_comparison)
        st.plotly_chart(fig_conversion, use_container_width=True)
        
        # 3. 시간대별 전환율 패턴
        st.subheader("3️⃣ Hourly Conversion Pattern")
        
        hourly_data = {}
        peak_data = {}
        
        for store_name, positions in st.session_state.conversion_positions.items():
            peak_analysis = traffic_analyzer.peak_time_analysis(positions)
            hourly_data[store_name] = peak_analysis['hourly_data']
            peak_data[store_name] = {
                'peak_traffic_hour': peak_analysis['peak_traffic_hour'],
                'peak_visit_hour': peak_analysis['peak_visit_hour'],
                'peak_conversion_hour': peak_analysis['peak_conversion_hour']
            }
        
        fig_hourly = visualizer.plot_hourly_conversion_pattern(hourly_data)
        st.plotly_chart(fig_hourly, use_container_width=True)
        
        # 4. 피크타임 비교
        st.subheader("4️⃣ Peak Time Comparison")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Peak Hours Summary**")
            for store_name, peak in peak_data.items():
                st.markdown(f"**{store_name}**")
                st.text(f"  Max Traffic: {peak['peak_traffic_hour']}시")
                st.text(f"  Max Visit: {peak['peak_visit_hour']}시")
                st.text(f"  Max Conversion: {peak['peak_conversion_hour']}시")
                st.markdown("")
        
        with col2:
            fig_peak = visualizer.plot_peak_time_comparison(peak_data)
            st.plotly_chart(fig_peak, use_container_width=True)
        
        # 5. 상세 데이터 테이블
        with st.expander("📋 Detailed Data Table"):
            st.dataframe(conversion_comparison, use_container_width=True)
        
        # 6. 인사이트 자동 생성
        st.subheader("💡 Insights")
        
        # 최고/최저 전환율
        best_conversion = conversion_comparison.loc[conversion_comparison['conversion_rate'].idxmax()]
        worst_conversion = conversion_comparison.loc[conversion_comparison['conversion_rate'].idxmin()]
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🏆 **Highest Conversion**: {best_conversion['store_name']} ({best_conversion['conversion_rate']*100:.1f}%)")
        with col2:
            st.info(f"📊 **Lowest Conversion**: {worst_conversion['store_name']} ({worst_conversion['conversion_rate']*100:.1f}%)")
        
        # 입지별 특성 추론
        st.markdown("**입지 유형별 특성 분석:**")
        for _, row in conversion_comparison.iterrows():
            store_name = row['store_name']
            conv_rate = row['conversion_rate'] * 100
            
            if conv_rate >= 70:
                profile = "주거지형 (High conversion - 단골 고객 중심)"
            elif conv_rate >= 40:
                profile = "병원인접형 (Medium conversion - 목적성 방문)"
            else:
                profile = "대형몰형 (Low conversion - 높은 유동인구)"
            
            st.markdown(f"- **{store_name}**: 전환율 {conv_rate:.1f}% → *{profile}*")
