"""
Multi-Store Visualizer - 여러 매장 동시 시각화
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from PIL import Image
from typing import Dict, List, Optional, Tuple
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


class MultiStoreVisualizer:
    """
    여러 매장의 데이터를 동시에 시각화
    """
    
    def __init__(self, device_colors: Dict = None):
        """
        Args:
            device_colors: {device_type: color} 딕셔너리
        """
        if device_colors is None:
            self.device_colors = {
                1: '#00FF00',   # iPhone - Green
                10: '#0000FF',  # Android - Blue
                32: '#800080',  # T-Ward - Purple
                101: '#FF0000'  # Trace - Red
            }
        else:
            self.device_colors = device_colors
        
        self.store_colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
    
    def plot_maps_side_by_side(self, store_data: Dict[str, Dict]) -> plt.Figure:
        """
        여러 매장 지도를 나란히 표시
        
        Args:
            store_data: {
                store_name: {
                    'map': PIL Image,
                    'positions': DataFrame,
                    'swards': DataFrame
                }
            }
        
        Returns:
            matplotlib Figure
        """
        n_stores = len(store_data)
        
        if n_stores == 0:
            return None
        
        # 서브플롯 생성
        fig, axes = plt.subplots(1, n_stores, figsize=(6*n_stores, 6))
        
        if n_stores == 1:
            axes = [axes]
        
        for idx, (store_name, data) in enumerate(store_data.items()):
            ax = axes[idx]
            
            # 지도 표시
            if data.get('map') is not None:
                ax.imshow(data['map'], alpha=0.7)
            
            # S-Ward 표시
            if data.get('swards') is not None:
                swards = data['swards']
                ax.scatter(swards['x'], swards['y'], 
                          c='red', s=100, marker='s', 
                          alpha=0.8, edgecolors='black', linewidths=2,
                          label='S-Ward')
            
            # 디바이스 위치 표시
            if data.get('positions') is not None and len(data['positions']) > 0:
                positions = data['positions']
                
                for device_type in positions['device_type'].unique():
                    device_data = positions[positions['device_type'] == device_type]
                    color = self.device_colors.get(device_type, '#CCCCCC')
                    
                    device_name = {1: 'iPhone', 10: 'Android', 32: 'T-Ward', 101: 'Trace'}.get(device_type, f'Type {device_type}')
                    
                    ax.scatter(device_data['x'], device_data['y'],
                              c=color, s=10, alpha=0.3, label=device_name)
            
            ax.set_title(store_name, fontsize=14, fontweight='bold')
            ax.legend(loc='upper right')
            ax.axis('off')
        
        plt.tight_layout()
        return fig
    
    def plot_heatmap_comparison(self, store_data: Dict[str, Dict], 
                                bins: int = 50) -> plt.Figure:
        """
        매장별 히트맵 비교
        
        Args:
            store_data: {store_name: {'map': Image, 'positions': DataFrame}}
            bins: 히트맵 해상도
        """
        n_stores = len(store_data)
        
        if n_stores == 0:
            return None
        
        fig, axes = plt.subplots(1, n_stores, figsize=(6*n_stores, 6))
        
        if n_stores == 1:
            axes = [axes]
        
        for idx, (store_name, data) in enumerate(store_data.items()):
            ax = axes[idx]
            
            positions = data.get('positions')
            
            if positions is None or len(positions) == 0:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=20)
                ax.set_title(store_name)
                ax.axis('off')
                continue
            
            # 지도 표시
            if data.get('map') is not None:
                ax.imshow(data['map'], alpha=0.3)
            
            # 히트맵 생성
            x = positions['x'].values
            y = positions['y'].values
            
            # 2D 히스토그램
            if data.get('map') is not None:
                map_img = data['map']
                extent = [0, map_img.width, map_img.height, 0]
            else:
                extent = [x.min(), x.max(), y.max(), y.min()]
            
            heatmap, xedges, yedges = np.histogram2d(x, y, bins=bins)
            
            im = ax.imshow(heatmap.T, origin='lower', 
                          extent=extent, cmap='hot', alpha=0.6)
            
            plt.colorbar(im, ax=ax, label='Density')
            
            ax.set_title(store_name, fontsize=14, fontweight='bold')
            ax.axis('off')
        
        plt.tight_layout()
        return fig
    
    def plot_hourly_comparison(self, hourly_df: pd.DataFrame, title: str = 'Hourly Visitor Comparison') -> go.Figure:
        """
        시간대별 방문자 수 비교 (Plotly)
        
        Args:
            hourly_df: DataFrame (hour, store1, store2, ...)
            title: 그래프 제목
        """
        fig = go.Figure()
        
        stores = [col for col in hourly_df.columns if col != 'hour']
        
        for idx, store in enumerate(stores):
            color = self.store_colors[idx % len(self.store_colors)]
            
            fig.add_trace(go.Scatter(
                x=hourly_df['hour'],
                y=hourly_df[store],
                mode='lines+markers',
                name=store,
                line=dict(color=color, width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Hour',
            yaxis_title='Average Visitors per Minute',
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def plot_hourly_comparison_integrated(self, hourly_data: Dict[str, pd.DataFrame], 
                                         store_name: str) -> go.Figure:
        """
        시간대별 3가지 카테고리 통합 그래프 - 꺾은선 (정확한 수치 비교용)
        
        Args:
            hourly_data: {'total': df, 'visitors': df, 'passers': df}
            store_name: 매장명
        """
        fig = go.Figure()
        
        categories = {
            'total': ('전체 센싱', '#1f77b4', 'solid'),
            'visitors': ('내부 방문자', '#2ca02c', 'dash'),
            'passers': ('외부 유동인구', '#ff7f0e', 'dot')
        }
        
        for key, (label, color, dash) in categories.items():
            df = hourly_data[key]
            if store_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['hour'],
                    y=df[store_name],
                    mode='lines+markers',
                    name=label,
                    line=dict(color=color, width=3, dash=dash),
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title=f'{store_name} - Hourly Traffic (Line Chart)',
            xaxis_title='Hour',
            yaxis_title='Average Visitors per Minute',
            hovermode='x unified',
            height=450,
            template='plotly_white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
        
        return fig
    
    def plot_hourly_comparison_area(self, hourly_data: Dict[str, pd.DataFrame], 
                                   store_name: str) -> go.Figure:
        """
        시간대별 3가지 카테고리 통합 그래프 - 면적 (비율 직관성용)
        전체를 꺾은선으로 보여주고, 그 아래를 방문자/유동인구로 면적 구분
        
        Args:
            hourly_data: {'total': df, 'visitors': df, 'passers': df}
            store_name: 매장명
        """
        fig = go.Figure()
        
        total_df = hourly_data['total']
        visitors_df = hourly_data['visitors']
        passers_df = hourly_data['passers']
        
        if store_name not in total_df.columns:
            return fig
        
        hours = total_df['hour'].values
        total_vals = total_df[store_name].values
        visitor_vals = visitors_df[store_name].values if store_name in visitors_df.columns else np.zeros(len(hours))
        passer_vals = passers_df[store_name].values if store_name in passers_df.columns else np.zeros(len(hours))
        
        # 1. 내부 방문자 (아래 면적)
        fig.add_trace(go.Scatter(
            x=hours,
            y=visitor_vals,
            mode='lines',
            name='내부 방문자',
            fill='tozeroy',
            fillcolor='rgba(44, 160, 44, 0.5)',  # 초록색
            line=dict(color='rgb(44, 160, 44)', width=2)
        ))
        
        # 2. 외부 유동인구 (스택)
        fig.add_trace(go.Scatter(
            x=hours,
            y=visitor_vals + passer_vals,  # 스택
            mode='lines',
            name='외부 유동인구',
            fill='tonexty',
            fillcolor='rgba(255, 127, 14, 0.5)',  # 주황색
            line=dict(color='rgb(255, 127, 14)', width=2)
        ))
        
        # 3. 전체 센싱 (경계선 - 검증용)
        fig.add_trace(go.Scatter(
            x=hours,
            y=total_vals,
            mode='lines',
            name='전체 센싱',
            line=dict(color='rgb(31, 119, 180)', width=3, dash='solid')
        ))
        
        fig.update_layout(
            title=f'{store_name} - Hourly Traffic (Area Chart)',
            xaxis_title='Hour',
            yaxis_title='Average Visitors per Minute',
            hovermode='x unified',
            height=450,
            template='plotly_white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
        
        return fig
    
    def plot_weekday_comparison(self, weekday_df: pd.DataFrame) -> go.Figure:
        """
        요일별 방문자 수 비교
        """
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        fig = go.Figure()
        
        stores = [col for col in weekday_df.columns if col != 'weekday']
        
        for idx, store in enumerate(stores):
            color = self.store_colors[idx % len(self.store_colors)]
            
            fig.add_trace(go.Bar(
                x=[weekday_names[int(i)] for i in weekday_df['weekday']],
                y=weekday_df[store],
                name=store,
                marker_color=color
            ))
        
        fig.update_layout(
            title='Weekday Visitor Comparison',
            xaxis_title='Day of Week',
            yaxis_title='Number of Visitors',
            barmode='group',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def plot_stats_comparison(self, stats_list: List[Dict]) -> go.Figure:
        """
        기본 통계 비교 (막대 차트)
        
        Args:
            stats_list: [{'store_name': ..., 'total_visitors': ..., ...}, ...]
        """
        stores = [s['store_name'] for s in stats_list]
        visitors = [s['total_visitors'] for s in stats_list]
        dwell_times = [s['avg_dwell_time'] for s in stats_list]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Total Visitors',
            x=stores,
            y=visitors,
            marker_color='#4ECDC4',
            yaxis='y',
            offsetgroup=1
        ))
        
        fig.add_trace(go.Bar(
            name='Avg Dwell Time (min)',
            x=stores,
            y=dwell_times,
            marker_color='#FFE66D',
            yaxis='y2',
            offsetgroup=2
        ))
        
        fig.update_layout(
            title='Store Statistics Comparison',
            yaxis=dict(title='Total Visitors', side='left'),
            yaxis2=dict(title='Avg Dwell Time (min)', side='right', overlaying='y'),
            barmode='group',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def plot_dwell_time_distribution(self, duration_df: pd.DataFrame) -> go.Figure:
        """
        체류 시간 분포 비교
        """
        stores = duration_df['store'].tolist()
        categories = [col for col in duration_df.columns if col != 'store']
        
        fig = go.Figure()
        
        for idx, category in enumerate(categories):
            color = self.store_colors[idx % len(self.store_colors)]
            
            fig.add_trace(go.Bar(
                name=category,
                x=stores,
                y=duration_df[category],
                marker_color=color
            ))
        
        fig.update_layout(
            title='Dwell Time Distribution Comparison',
            xaxis_title='Store',
            yaxis_title='Number of Visitors',
            barmode='stack',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def plot_conversion_rate_comparison(self, conversion_df: pd.DataFrame) -> go.Figure:
        """
        매장별 전환율 비교 차트
        
        Args:
            conversion_df: TrafficAnalyzer.compare_stores_conversion() 결과
            
        Returns:
            Plotly Figure
        """
        if len(conversion_df) == 0:
            return go.Figure()
        
        fig = go.Figure()
        
        # 총 트래픽 (유동 + 방문)
        fig.add_trace(go.Bar(
            name='Pass-by (유동인구)',
            x=conversion_df['store_name'],
            y=conversion_df['pass_by_count'],
            marker_color='#FFA726',
            text=conversion_df['pass_by_count'],
            textposition='inside'
        ))
        
        fig.add_trace(go.Bar(
            name='Visit (방문인구)',
            x=conversion_df['store_name'],
            y=conversion_df['visit_count'],
            marker_color='#66BB6A',
            text=conversion_df['visit_count'],
            textposition='inside'
        ))
        
        # 전환율 라인 (보조 축)
        fig.add_trace(go.Scatter(
            name='Conversion Rate (전환율)',
            x=conversion_df['store_name'],
            y=conversion_df['conversion_rate'] * 100,
            mode='lines+markers+text',
            marker=dict(size=12, color='#EF5350'),
            line=dict(width=3, color='#EF5350'),
            text=[f"{x:.1f}%" for x in conversion_df['conversion_rate'] * 100],
            textposition='top center',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Traffic Conversion Rate Comparison (유동/방문 전환율 비교)',
            xaxis_title='Store',
            yaxis=dict(
                title='Number of People (인원)',
                side='left'
            ),
            yaxis2=dict(
                title='Conversion Rate (%)',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            barmode='stack',
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def plot_hourly_conversion_pattern(self, 
                                      hourly_data: Dict[str, pd.DataFrame]) -> go.Figure:
        """
        시간대별 전환율 패턴 비교
        
        Args:
            hourly_data: {store_name: hourly_conversion_df, ...}
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        for idx, (store_name, hourly_df) in enumerate(hourly_data.items()):
            color = self.store_colors[idx % len(self.store_colors)]
            
            # 전환율 라인
            fig.add_trace(go.Scatter(
                name=f'{store_name} - Conversion',
                x=hourly_df['hour'],
                y=hourly_df['conversion_rate'] * 100,
                mode='lines+markers',
                marker=dict(size=6, color=color),
                line=dict(width=2, color=color),
                hovertemplate='%{x}시: %{y:.1f}%<extra></extra>'
            ))
        
        fig.update_layout(
            title='Hourly Conversion Rate Pattern (시간대별 전환율 패턴)',
            xaxis_title='Hour (시간)',
            yaxis_title='Conversion Rate (%)',
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=2,
                range=[0, 23]
            ),
            yaxis=dict(range=[0, 100]),
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def plot_peak_time_comparison(self, peak_data: Dict[str, Dict]) -> go.Figure:
        """
        매장별 피크타임 비교 차트
        
        Args:
            peak_data: {
                store_name: {
                    'peak_traffic_hour': int,
                    'peak_visit_hour': int,
                    'peak_conversion_hour': int
                }
            }
            
        Returns:
            Plotly Figure
        """
        stores = list(peak_data.keys())
        traffic_peaks = [data['peak_traffic_hour'] for data in peak_data.values()]
        visit_peaks = [data['peak_visit_hour'] for data in peak_data.values()]
        conversion_peaks = [data['peak_conversion_hour'] for data in peak_data.values()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Peak Traffic Hour (최대 트래픽)',
            x=stores,
            y=traffic_peaks,
            marker_color='#FFA726',
            text=[f"{h}시" for h in traffic_peaks],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Peak Visit Hour (최대 방문)',
            x=stores,
            y=visit_peaks,
            marker_color='#66BB6A',
            text=[f"{h}시" for h in visit_peaks],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Peak Conversion Hour (최대 전환율)',
            x=stores,
            y=conversion_peaks,
            marker_color='#EF5350',
            text=[f"{h}시" for h in conversion_peaks],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Peak Time Comparison (피크타임 비교)',
            xaxis_title='Store',
            yaxis_title='Hour (시간)',
            yaxis=dict(range=[0, 24], tickmode='linear', dtick=2),
            barmode='group',
            height=500,
            template='plotly_white'
        )
        
        return fig
