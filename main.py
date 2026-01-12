"""
New main.py for Production Dashboard
Cache-based, English, Professional Design
"""
import streamlit as st
from pathlib import Path
import plotly.io as pio

# Must be first Streamlit command
st.set_page_config(
    page_title="Pharmacy Traffic Analysis",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Password protection
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Set Plotly default template for consistent black text
pio.templates.default = "plotly_white"

# Import after set_page_config
from src.ui import get_custom_css, CacheLoader


def main():
    """Main dashboard application"""
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
            🏥 Pharmacy Traffic & Conversion Analysis
        </h1>
        <p style='font-size: 1.2rem; color: #6b7280;'>
            Comparative Analysis of Three Small Pharmacy Locations
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize cache loader
    cache_folder = Path("Cache")
    
    if not (cache_folder / "conversion_analysis_cache.json").exists():
        st.error("""
        ❌ **Cache file not found!**
        
        Please run preprocessing first:
        ```bash
        python preprocess_conversion_data.py --data-folder Data/ChamYakSa --output Cache
        ```
        """)
        return
    
    # Load cache
    with st.spinner("Loading cached data..."):
        cache = CacheLoader(cache_folder="Cache")
        if not cache.load_cache():
            st.error("Failed to load cache. Please check cache file.")
            return
    
    stores = cache.get_available_stores()
    
    if not stores:
        st.warning("No stores found in cache.")
        return
    
    # Success message
    st.success(f"✅ Successfully loaded data for {len(stores)} stores")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📖 Overview",
        "📊 Store Comparison", 
        "🔍 Detailed Insights",
        "📈 Temporal Analysis",
        "⏰ Business Hours",
        "⏱️ Dwell Time",
        "🎌 Holiday Analysis",
        "🔥 Efficiency Heatmap",
        "📐 Efficiency Benchmark"
    ])
    
    # Tab 1: Overview
    with tab1:
        show_overview_page()
    
    # Tab 2: Store Comparison
    with tab2:
        show_comparison_page(cache, stores)
    
    # Tab 3: Detailed Insights
    with tab3:
        show_insights_page(cache, stores)
    
    # Tab 4: Temporal Analysis
    with tab4:
        show_temporal_analysis_page(cache, stores)
    
    # Tab 5: Business Hours Impact
    with tab5:
        show_business_hours_impact_page(cache, stores)
    
    # Tab 6: Dwell Time Distribution
    with tab6:
        show_dwell_time_page(cache, stores)
    
    # Tab 7: Holiday Analysis
    with tab7:
        show_holiday_analysis_page(cache, stores)
    
    # Tab 8: Efficiency Heatmap
    with tab8:
        show_efficiency_heatmap_page(cache, stores)
    
    # Tab 9: Efficiency Benchmarking
    with tab9:
        show_efficiency_benchmark_page(cache, stores)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class='footer'>
        <p><strong>Pharmacy Traffic Analysis Dashboard v2.0</strong></p>
        <p>Powered by TJ Labs | BLE-based Indoor Analytics</p>
    </div>
    """, unsafe_allow_html=True)


def show_overview_page():
    """Show overview and documentation"""
    
    st.markdown("## 📋 Dashboard Overview")
    
    st.markdown("""
    ### About This Dashboard
    
    This dashboard analyzes traffic patterns and conversion rates for three pharmacy locations 
    using BLE (Bluetooth Low Energy) sensor data collected over 48 days.
    
    ### Key Concepts
    - **Pass-by Traffic**: Visitors with < 2 minutes dwell time (currently set threshold)
    - **Visit Traffic**: Visitors with ≥ 2 minutes dwell time
    - **Conversion Rate**: Visits / Total Traffic × 100%
    
    ### Store Locations
    | Store | Type | Description |
    |-------|------|-------------|
    | Seoungbuk1 | Residential | Local pharmacy in residential area |
    | Starfield_Suwon | Shopping Mall | Inside large shopping complex |
    | Tyranno_Yongin | Mixed-Use Building | Building with offices, hospital, restaurants |
    """)


def show_comparison_page(cache: CacheLoader, stores: list):
    """Show store comparison analysis"""
    
    st.markdown("## 🏪 Multi-Store Comparison")
    
    # Store selection
    st.markdown("### Select Stores to Compare")
    
    cols = st.columns(len(stores))
    selected_stores = []
    
    for i, store_name in enumerate(stores):
        with cols[i]:
            profile = cache.get_store_profile(store_name)
            location_type = profile.get('type', 'Unknown')
            
            # Show store card
            st.markdown(f"""
            <div style='background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; 
                        border: 2px solid #e5e7eb; text-align: center;'>
                <h3>{store_name}</h3>
                <p style='color: #6b7280;'>{location_type}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.checkbox(f"Include {store_name}", value=True, key=f"select_{store_name}"):
                selected_stores.append(store_name)
    
    if not selected_stores:
        st.warning("⚠️ Please select at least one store to analyze.")
        return
    
    st.markdown("---")
    
    # Comparison metrics
    st.markdown("### 📊 Key Performance Metrics")
    
    comparison_data = cache.compare_stores(selected_stores)
    
    if not comparison_data['stores']:
        st.error("No data available for selected stores.")
        return
    
    # Display metrics in columns
    metric_cols = st.columns(len(selected_stores))
    
    for i, store_name in enumerate(comparison_data['stores']):
        idx = comparison_data['stores'].index(store_name)
        
        with metric_cols[i]:
            st.markdown(f"#### {store_name}")
            
            # Conversion rate
            conv_rate = comparison_data['conversion_rates'][idx]
            st.metric(
                "Conversion Rate",
                f"{conv_rate:.1f}%",
                help="Percentage of pass-by traffic that becomes visits"
            )
            
            # Average visits
            avg_visits = comparison_data['avg_visits'][idx]
            st.metric(
                "Avg Daily Visits",
                f"{avg_visits:.0f}",
                help="Average number of visits per day"
            )
            
            # Average traffic
            avg_traffic = comparison_data['avg_traffic'][idx]
            st.metric(
                "Avg Daily Traffic",
                f"{avg_traffic:.0f}",
                help="Total foot traffic (pass-by + visits)"
            )
            
            # Location type
            location_type = comparison_data['location_types'][idx]
            st.markdown(f"**Location**: {location_type}")
            
            # Data days
            total_days = comparison_data['total_days'][idx]
            st.markdown(f"**Data Period**: {total_days} days")
    
    st.markdown("---")
    
    # Visualization
    st.markdown("### 📈 Comparative Visualizations")
    
    import plotly.graph_objects as go
    
    # 1. Conversion Rate Comparison
    st.markdown("#### Conversion Rate by Store")
    
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=comparison_data['stores'],
        y=comparison_data['conversion_rates'],
        marker=dict(
            color=comparison_data['conversion_rates'],
            colorscale='Blues',
            showscale=False
        ),
        text=[f"{v:.1f}%" for v in comparison_data['conversion_rates']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Conversion Rate: %{y:.1f}%<extra></extra>'
    ))
    
    fig1.update_layout(
        title=None,
        xaxis_title="Store",
        yaxis_title="Conversion Rate (%)",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # 2. Traffic Volume Comparison
    st.markdown("#### Daily Traffic Volume Comparison")
    
    fig2 = go.Figure()
    
    # Visits
    fig2.add_trace(go.Bar(
        name='Visits',
        x=comparison_data['stores'],
        y=comparison_data['avg_visits'],
        marker_color='#2563eb',
        hovertemplate='<b>%{x}</b><br>Visits: %{y:.0f}<extra></extra>'
    ))
    
    # Pass-by (calculated)
    pass_by_traffic = [
        comparison_data['avg_traffic'][i] - comparison_data['avg_visits'][i]
        for i in range(len(comparison_data['stores']))
    ]
    
    fig2.add_trace(go.Bar(
        name='Pass-by',
        x=comparison_data['stores'],
        y=pass_by_traffic,
        marker_color='#9ca3af',
        hovertemplate='<b>%{x}</b><br>Pass-by: %{y:.0f}<extra></extra>'
    ))
    
    fig2.update_layout(
        title=None,
        xaxis_title="Store",
        yaxis_title="Average Daily Count",
        barmode='stack',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#000000')
        )
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # AI-Powered Insights Section
    st.markdown("### 🤖 AI-Powered Business Insights")
    
    # Calculate additional metrics for insights
    best_conv_idx = comparison_data['conversion_rates'].index(
        max(comparison_data['conversion_rates'])
    )
    best_conv_store = comparison_data['stores'][best_conv_idx]
    best_conv_rate = comparison_data['conversion_rates'][best_conv_idx]
    best_conv_type = comparison_data['location_types'][best_conv_idx]
    
    worst_conv_idx = comparison_data['conversion_rates'].index(
        min(comparison_data['conversion_rates'])
    )
    worst_conv_store = comparison_data['stores'][worst_conv_idx]
    worst_conv_rate = comparison_data['conversion_rates'][worst_conv_idx]
    
    best_traffic_idx = comparison_data['avg_traffic'].index(
        max(comparison_data['avg_traffic'])
    )
    best_traffic_store = comparison_data['stores'][best_traffic_idx]
    best_traffic_count = comparison_data['avg_traffic'][best_traffic_idx]
    best_traffic_type = comparison_data['location_types'][best_traffic_idx]
    
    # Calculate conversion gap
    conversion_gap = best_conv_rate - worst_conv_rate
    
    # Calculate potential visitors if worst matched best
    worst_traffic = comparison_data['avg_traffic'][worst_conv_idx]
    potential_gain = int(worst_traffic * (best_conv_rate - worst_conv_rate) / 100)
    
    # Performance Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class='success-box'>
            <h4>🏆 Top Performer: {best_conv_store}</h4>
            <p style='font-size: 1.1em;'><strong>{best_conv_rate:.1f}%</strong> conversion rate</p>
            <p><strong>Location:</strong> {best_conv_type}</p>
            <p><strong>Key Strength:</strong> High customer engagement with loyal visitor base</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='info-box'>
            <h4>📊 Traffic Leader: {best_traffic_store}</h4>
            <p style='font-size: 1.1em;'><strong>{best_traffic_count:.0f}</strong> daily visitors</p>
            <p><strong>Location:</strong> {best_traffic_type}</p>
            <p><strong>Opportunity:</strong> Large visitor pool for conversion optimization</p>
        </div>
        """, unsafe_allow_html=True)
    
    # AI Analysis & Recommendations
    st.markdown("#### 📈 Data-Driven Analysis")
    
    # Generate dynamic insights based on data
    insights_list = []
    
    # Insight 1: Conversion Gap Analysis
    if conversion_gap > 15:
        insights_list.append({
            'icon': '⚠️',
            'title': 'Significant Conversion Gap Detected',
            'text': f'{worst_conv_store} ({worst_conv_rate:.1f}%) is {conversion_gap:.1f}pp behind {best_conv_store} ({best_conv_rate:.1f}%).',
            'action': f'If {worst_conv_store} matched the top performer, it could gain ~{potential_gain} additional visitors/day.',
            'priority': 'High'
        })
    elif conversion_gap > 5:
        insights_list.append({
            'icon': '📊',
            'title': 'Moderate Conversion Variance',
            'text': f'Conversion rates range from {worst_conv_rate:.1f}% to {best_conv_rate:.1f}% ({conversion_gap:.1f}pp gap).',
            'action': 'Analyze successful practices from top performers for potential knowledge transfer.',
            'priority': 'Medium'
        })
    
    # Insight 2: Location-based performance
    for i, store in enumerate(comparison_data['stores']):
        loc_type = comparison_data['location_types'][i]
        conv_rate = comparison_data['conversion_rates'][i]
        
        if loc_type == 'Shopping Mall' and conv_rate < 10:
            insights_list.append({
                'icon': '🛒',
                'title': f'{store}: Low Mall Conversion',
                'text': f'Shopping mall locations typically see 25-35% conversion, but this store shows {conv_rate:.1f}%.',
                'action': 'Consider impulse-buy displays, visible signage, or promotional activities to capture passing traffic.',
                'priority': 'High'
            })
        elif loc_type == 'Residential' and conv_rate > 25:
            insights_list.append({
                'icon': '🏠',
                'title': f'{store}: Strong Residential Performance',
                'text': f'Achieving {conv_rate:.1f}% conversion in residential area indicates strong community loyalty.',
                'action': 'Leverage this loyalty with membership programs or referral incentives.',
                'priority': 'Opportunity'
            })
    
    # Insight 3: Traffic vs Conversion tradeoff
    if best_traffic_store != best_conv_store:
        traffic_store_conv = comparison_data['conversion_rates'][best_traffic_idx]
        insights_list.append({
            'icon': '🔄',
            'title': 'Traffic-Conversion Tradeoff Opportunity',
            'text': f'{best_traffic_store} has highest traffic but only {traffic_store_conv:.1f}% conversion.',
            'action': f'Even a 5% conversion improvement could mean ~{int(best_traffic_count * 0.05)} more visitors/day.',
            'priority': 'High'
        })
    
    # Display insights
    for insight in insights_list:
        priority_color = {'High': '#ef4444', 'Medium': '#f59e0b', 'Opportunity': '#22c55e'}.get(insight['priority'], '#6b7280')
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
                    padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.75rem;
                    border-left: 4px solid {priority_color};'>
            <p style='margin: 0; font-size: 1.1em;'><strong>{insight['icon']} {insight['title']}</strong>
            <span style='float: right; font-size: 0.8em; background: {priority_color}; color: white; 
                         padding: 2px 8px; border-radius: 4px;'>{insight['priority']}</span></p>
            <p style='margin: 0.5rem 0; color: #374151;'>{insight['text']}</p>
            <p style='margin: 0; color: #2563eb; font-weight: 500;'>💡 Action: {insight['action']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Actionable Recommendations
    st.markdown("#### 🎯 Strategic Recommendations")
    
    recommendations = []
    
    # Generate recommendations based on analysis
    recommendations.append({
        'store': worst_conv_store,
        'recommendation': 'Focus on conversion optimization',
        'details': f'Current conversion ({worst_conv_rate:.1f}%) is below potential. Implement customer engagement strategies.',
        'expected_impact': f'+{potential_gain} visitors/day potential'
    })
    
    if best_traffic_store != best_conv_store:
        recommendations.append({
            'store': best_traffic_store,
            'recommendation': 'Capitalize on high traffic',
            'details': 'High foot traffic presents opportunity. Consider promotional displays or quick-service options.',
            'expected_impact': '+5-10% conversion potential'
        })
    
    recommendations.append({
        'store': best_conv_store,
        'recommendation': 'Document best practices',
        'details': 'Analyze what drives high conversion and share learnings with other locations.',
        'expected_impact': 'Network-wide improvement'
    })
    
    for rec in recommendations:
        st.markdown(f"""
        <div style='background: #f0fdf4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;
                    border: 1px solid #86efac;'>
            <p style='margin: 0; font-weight: 600; color: #166534;'>📍 {rec['store']}</p>
            <p style='margin: 0.25rem 0; font-weight: 500;'>{rec['recommendation']}</p>
            <p style='margin: 0; font-size: 0.9em; color: #374151;'>{rec['details']}</p>
            <p style='margin: 0.25rem 0 0 0; font-size: 0.85em; color: #15803d;'>📈 Expected Impact: {rec['expected_impact']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Location Type Reference
    with st.expander("📍 Location Type Benchmarks", expanded=False):
        st.markdown("""
        | Location Type | Expected Conversion | Characteristics |
        |---------------|---------------------|-----------------|
        | **Residential** | 40-55% | Loyal local customers, regular prescriptions, predictable patterns |
        | **Shopping Mall** | 25-35% | Impulse visitors, high traffic, lower engagement |
        | **Mixed-Use** | 30-45% | Office workers, hospital patients, diverse needs |
        
        *Note: Conversion = visitors staying 2+ min with strong signal (iPhone > -75dBm, Android > -85dBm)*
        """)


def show_insights_page(cache: CacheLoader, stores: list):
    """Show detailed insights for individual stores"""
    
    st.markdown("## 🔍 Detailed Store Insights")
    
    # Store selector
    selected_store = st.selectbox(
        "Select a store for detailed analysis:",
        stores,
        key="detailed_store"
    )
    
    if not selected_store:
        return
    
    # Get data
    profile = cache.get_store_profile(selected_store)
    stats = cache.get_aggregated_stats(selected_store)
    hourly_df = cache.get_hourly_pattern(selected_store)
    weekday_df = cache.get_weekday_pattern(selected_store)
    peak_hours = cache.get_peak_hours(selected_store)
    
    st.markdown(f"### 🏪 {selected_store}")
    
    # Store profile
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class='info-box'>
            <h4>{profile.get('type', 'Unknown')} Location</h4>
            <p><strong>Description:</strong> {profile.get('description', 'N/A')}</p>
            <p><strong>Characteristics:</strong> {profile.get('characteristics', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Business hours
        business_hours = profile.get('business_hours', {})
        if business_hours:
            weekday = business_hours.get('weekday', {})
            saturday = business_hours.get('saturday', {})
            sunday = business_hours.get('sunday', {})
            
            hours_text = "<h4>🕐 Business Hours</h4><ul>"
            
            # Weekday
            if weekday:
                open_h = int(weekday['open'])
                open_m = int((weekday['open'] % 1) * 60)
                close_h = int(weekday['close'])
                close_m = int((weekday['close'] % 1) * 60)
                hours_text += f"<li><strong>Mon-Fri:</strong> {open_h:02d}:{open_m:02d} - {close_h:02d}:{close_m:02d}</li>"
            
            # Saturday
            if saturday:
                if saturday.get('closed'):
                    hours_text += "<li><strong>Saturday:</strong> Closed</li>"
                else:
                    open_h = int(saturday['open'])
                    open_m = int((saturday['open'] % 1) * 60)
                    close_h = int(saturday['close'])
                    close_m = int((saturday['close'] % 1) * 60)
                    hours_text += f"<li><strong>Saturday:</strong> {open_h:02d}:{open_m:02d} - {close_h:02d}:{close_m:02d}</li>"
            
            # Sunday
            if sunday:
                if sunday.get('closed'):
                    hours_text += "<li><strong>Sunday:</strong> Closed</li>"
                else:
                    open_h = int(sunday['open'])
                    open_m = int((sunday['open'] % 1) * 60)
                    close_h = int(sunday['close'])
                    close_m = int((sunday['close'] % 1) * 60)
                    hours_text += f"<li><strong>Sunday:</strong> {open_h:02d}:{open_m:02d} - {close_h:02d}:{close_m:02d}</li>"
            
            hours_text += "</ul>"
            
            st.markdown(f"""
            <div class='warning-box'>
                {hours_text}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        overall = stats.get('overall', {})
        st.metric(
            "Avg Conversion Rate",
            f"{overall.get('avg_conversion_rate', 0)*100:.1f}%"
        )
        st.metric(
            "Total Days Analyzed",
            f"{overall.get('total_days', 0)}"
        )
    
    st.markdown("---")
    
    # Hourly pattern
    if not hourly_df.empty:
        st.markdown("### ⏰ Hourly Traffic Pattern")
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hourly_df['hour'],
            y=hourly_df['conversion_rate'] * 100,
            mode='lines+markers',
            name='Conversion Rate',
            line=dict(color='#2563eb', width=3),
            marker=dict(size=8),
            yaxis='y2',
            hovertemplate='Hour: %{x}<br>Conversion: %{y:.1f}%<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=hourly_df['hour'],
            y=hourly_df['total_traffic'],
            name='Total Traffic',
            marker_color='#9ca3af',
            opacity=0.6,
            hovertemplate='Hour: %{x}<br>Traffic: %{y:.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=hourly_df['hour'],
            y=hourly_df['visit_count'],
            name='Visits',
            marker_color='#10b981',
            opacity=0.8,
            hovertemplate='Hour: %{x}<br>Visits: %{y:.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="Hour of Day",
            yaxis_title="Count",
            yaxis2=dict(
                title=dict(text="Conversion Rate (%)", font=dict(color='#000000')),
                overlaying='y',
                side='right',
                range=[0, 100],
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                title=dict(font=dict(color='#000000')),
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            yaxis=dict(
                title=dict(font=dict(color='#000000')),
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='#000000')
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Peak hours info
        st.markdown(f"""
        <div class='success-box'>
            <h4>⏰ Peak Hours Identified</h4>
            <ul>
                <li><strong>Peak Traffic Hour:</strong> {peak_hours.get('peak_traffic_hour', 'N/A')}:00</li>
                <li><strong>Peak Visit Hour:</strong> {peak_hours.get('peak_visit_hour', 'N/A')}:00</li>
                <li><strong>Peak Conversion Hour:</strong> {peak_hours.get('peak_conversion_hour', 'N/A')}:00</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Weekday pattern
    if not weekday_df.empty:
        st.markdown("### 📅 Weekday Pattern")
        
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weekday_df['weekday_name'] = weekday_df['weekday'].map(
            lambda x: weekday_names[x] if 0 <= x < 7 else 'Unknown'
        )
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=weekday_df['weekday_name'],
            y=weekday_df['avg_visit_count'],
            marker_color='#2563eb',
            name='Avg Visits',
            hovertemplate='%{x}<br>Visits: %{y:.1f}<extra></extra>'
        ))
        
        fig2.add_trace(go.Scatter(
            x=weekday_df['weekday_name'],
            y=weekday_df['avg_conversion_rate'] * 100,
            mode='lines+markers',
            name='Conversion Rate',
            line=dict(color='#f59e0b', width=3),
            marker=dict(size=10),
            yaxis='y2',
            hovertemplate='%{x}<br>Rate: %{y:.1f}%<extra></extra>'
        ))
        
        fig2.update_layout(
            title=None,
            xaxis_title="Day of Week",
            yaxis_title="Average Visit Count",
            yaxis2=dict(
                title=dict(text="Conversion Rate (%)", font=dict(color='#000000')),
                overlaying='y',
                side='right',
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#000000', size=12),
            xaxis=dict(
                title=dict(font=dict(color='#000000')),
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            yaxis=dict(
                title=dict(font=dict(color='#000000')),
                tickfont=dict(color='#000000'),
                gridcolor='#e5e7eb'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color='#000000')
            )
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # AI-Powered Store-Specific Insights
    st.markdown("---")
    st.markdown("### 🤖 AI-Powered Store Analysis")
    
    # Calculate store-specific metrics
    overall = stats.get('overall', {})
    conv_rate = overall.get('avg_conversion_rate', 0) * 100
    avg_daily_visits = overall.get('avg_daily_visits', 0)
    store_type = profile.get('type', 'Unknown')
    
    # Generate dynamic insights based on store performance
    store_insights = []
    
    # Conversion rate analysis based on location type
    type_benchmarks = {
        'Residential': {'min': 40, 'max': 55, 'name': 'Residential'},
        'Commercial': {'min': 25, 'max': 35, 'name': 'Commercial/Mall'},
        'Mixed-Use': {'min': 30, 'max': 45, 'name': 'Mixed-Use'}
    }
    
    benchmark = type_benchmarks.get(store_type, {'min': 30, 'max': 40, 'name': 'Average'})
    
    if conv_rate < benchmark['min']:
        gap = benchmark['min'] - conv_rate
        store_insights.append({
            'icon': '⚠️',
            'title': 'Conversion Below Benchmark',
            'text': f'Current rate ({conv_rate:.1f}%) is {gap:.1f}pp below {benchmark["name"]} benchmark ({benchmark["min"]}-{benchmark["max"]}%).',
            'action': 'Consider improving in-store experience, signage visibility, or customer engagement.',
            'priority': 'High'
        })
    elif conv_rate > benchmark['max']:
        excess = conv_rate - benchmark['max']
        store_insights.append({
            'icon': '🏆',
            'title': 'Excellent Conversion Performance',
            'text': f'Current rate ({conv_rate:.1f}%) exceeds {benchmark["name"]} benchmark by {excess:.1f}pp!',
            'action': 'Document success factors for replication in other locations.',
            'priority': 'Opportunity'
        })
    else:
        store_insights.append({
            'icon': '✅',
            'title': 'Conversion Within Target Range',
            'text': f'Current rate ({conv_rate:.1f}%) is within the expected {benchmark["name"]} range ({benchmark["min"]}-{benchmark["max"]}%).',
            'action': 'Focus on incremental improvements to move toward upper range.',
            'priority': 'Medium'
        })
    
    # Peak hours analysis
    if peak_hours:
        peak_traffic_hour = peak_hours.get('peak_traffic_hour', 12)
        peak_visit_hour = peak_hours.get('peak_visit_hour', 12)
        peak_conv_hour = peak_hours.get('peak_conversion_hour', 12)
        
        if peak_traffic_hour != peak_visit_hour:
            store_insights.append({
                'icon': '🔍',
                'title': 'Traffic vs Visit Hour Mismatch',
                'text': f'Peak traffic is at {peak_traffic_hour}:00 but peak visits are at {peak_visit_hour}:00.',
                'action': f'Analyze why {peak_traffic_hour}:00 traffic isn\'t converting. Consider promotional activities or staff optimization.',
                'priority': 'High'
            })
        
        if peak_conv_hour != peak_visit_hour:
            store_insights.append({
                'icon': '💡',
                'title': 'Conversion Efficiency Insight',
                'text': f'Best conversion rate is at {peak_conv_hour}:00 (not peak visit hour {peak_visit_hour}:00).',
                'action': f'Study what makes {peak_conv_hour}:00 effective - staffing, lower crowd, service speed?',
                'priority': 'Medium'
            })
    
    # Hourly pattern analysis
    if not hourly_df.empty:
        hourly_df['conversion_rate_pct'] = hourly_df['conversion_rate'] * 100
        low_conv_hours = hourly_df[hourly_df['conversion_rate_pct'] < hourly_df['conversion_rate_pct'].mean() * 0.7]
        
        if not low_conv_hours.empty and len(low_conv_hours) >= 2:
            low_hours = sorted(low_conv_hours['hour'].tolist())
            hour_ranges = []
            start = low_hours[0]
            end = low_hours[0]
            
            for h in low_hours[1:]:
                if h == end + 1:
                    end = h
                else:
                    if start == end:
                        hour_ranges.append(f"{start}:00")
                    else:
                        hour_ranges.append(f"{start}:00-{end}:00")
                    start = end = h
            
            if start == end:
                hour_ranges.append(f"{start}:00")
            else:
                hour_ranges.append(f"{start}:00-{end}:00")
            
            store_insights.append({
                'icon': '📉',
                'title': 'Low Conversion Time Windows',
                'text': f'Hours {", ".join(hour_ranges[:3])} show below-average conversion rates.',
                'action': 'Consider targeted promotions or improved staffing during these hours.',
                'priority': 'Medium'
            })
    
    # Weekday pattern analysis
    if not weekday_df.empty:
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        best_day = weekday_df.loc[weekday_df['avg_visit_count'].idxmax()]
        worst_day = weekday_df.loc[weekday_df['avg_visit_count'].idxmin()]
        
        best_name = weekday_names[int(best_day['weekday'])]
        worst_name = weekday_names[int(worst_day['weekday'])]
        
        visit_ratio = best_day['avg_visit_count'] / max(worst_day['avg_visit_count'], 1)
        
        if visit_ratio > 2:
            store_insights.append({
                'icon': '📊',
                'title': 'High Weekday Variation',
                'text': f'{best_name} has {visit_ratio:.1f}x more visits than {worst_name}.',
                'action': f'Consider {worst_name} promotions or analyze if {worst_name} has operational limitations.',
                'priority': 'Medium'
            })
    
    # Display insights with priority styling
    for insight in store_insights:
        if insight['priority'] == 'High':
            box_class = 'warning-box'
        elif insight['priority'] == 'Opportunity':
            box_class = 'success-box'
        else:
            box_class = 'info-box'
        
        st.markdown(f"""
        <div class='{box_class}'>
            <h4>{insight['icon']} {insight['title']} <span style='font-size: 0.8em; color: #666;'>({insight['priority']} Priority)</span></h4>
            <p>{insight['text']}</p>
            <p><strong>💡 Recommendation:</strong> {insight['action']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Strategic summary
    st.markdown("### 📋 Strategic Summary")
    
    summary_points = []
    
    # Staffing recommendation
    if peak_hours:
        peak_h = peak_hours.get('peak_visit_hour', 12)
        summary_points.append(f"**Peak Staffing**: Ensure adequate staff coverage around {peak_h}:00 ± 1 hour")
    
    # Promotion timing
    if store_type == 'Commercial':
        summary_points.append("**Promotional Timing**: Lunch hours (11:00-14:00) and after-work (17:00-19:00) are key windows")
    elif store_type == 'Residential':
        summary_points.append("**Promotional Timing**: Morning (09:00-11:00) and early evening (17:00-19:00) suit local residents")
    else:
        summary_points.append("**Promotional Timing**: Balance between commuter hours and local customer patterns")
    
    # Performance target
    if conv_rate < benchmark['min']:
        target = benchmark['min']
        summary_points.append(f"**Improvement Target**: Aim for {target:.0f}% conversion rate (+{target - conv_rate:.1f}pp)")
    else:
        summary_points.append(f"**Maintain Excellence**: Keep conversion at {conv_rate:.1f}% or higher")
    
    summary_html = "<ul>" + "".join([f"<li>{p}</li>" for p in summary_points]) + "</ul>"
    
    st.markdown(f"""
    <div class='success-box'>
        {summary_html}
    </div>
    """, unsafe_allow_html=True)


def show_temporal_analysis_page(cache: CacheLoader, stores: list):
    """Show temporal analysis - trends over time and weekday patterns"""
    
    st.markdown("## 📈 Temporal Analysis - Time-Based Trends")
    
    st.markdown("""
    This section analyzes how traffic and conversion patterns **change over time**.
    With 48 days of data, we can identify:
    - **Daily trends**: Are visits increasing or decreasing?
    - **Weekday patterns**: Which days have higher conversion?
    - **Consistency**: How stable are the patterns?
    """)
    
    # Store selection
    selected_store = st.selectbox(
        "Select a store for temporal analysis:",
        stores,
        key="temporal_store"
    )
    
    if not selected_store:
        return
    
    daily_results = cache.get_daily_results(selected_store)
    
    if not daily_results:
        st.warning(f"No daily data available for {selected_store}")
        return
    
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Convert to DataFrame
    df = pd.DataFrame(daily_results)
    
    # Extract conversion stats
    df['conversion_rate'] = df.apply(
        lambda x: x['conversion_stats']['conversion_rate'] * 100, axis=1
    )
    df['visit_count'] = df.apply(
        lambda x: x['conversion_stats']['visit_count'], axis=1
    )
    df['pass_by_count'] = df.apply(
        lambda x: x['conversion_stats']['pass_by_count'], axis=1
    )
    df['total_traffic'] = df.apply(
        lambda x: x['conversion_stats']['total_traffic'], axis=1
    )
    
    # Convert date strings to datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Add weekday names
    df['weekday_name'] = df['date'].dt.day_name()
    
    st.markdown(f"### 📅 Daily Trends for {selected_store}")
    st.markdown(f"**Analysis Period**: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')} ({len(df)} days)")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Avg Conversion Rate",
            f"{df['conversion_rate'].mean():.1f}%",
            f"{df['conversion_rate'].std():.1f}% σ"
        )
    
    with col2:
        st.metric(
            "Avg Daily Visits",
            f"{df['visit_count'].mean():.0f}",
            f"{df['visit_count'].std():.0f} σ"
        )
    
    with col3:
        st.metric(
            "Max Daily Visits",
            f"{df['visit_count'].max():.0f}",
            f"on {df.loc[df['visit_count'].idxmax(), 'date'].strftime('%m/%d')}"
        )
    
    with col4:
        st.metric(
            "Min Daily Visits",
            f"{df['visit_count'].min():.0f}",
            f"on {df.loc[df['visit_count'].idxmin(), 'date'].strftime('%m/%d')}"
        )
    
    st.markdown("---")
    
    # Time series plot
    st.markdown("### 📊 Daily Traffic & Conversion Rate Over Time")
    
    fig1 = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily Visit Count', 'Daily Conversion Rate'),
        vertical_spacing=0.12,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # Row 1: Visit count
    fig1.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['visit_count'],
            mode='lines+markers',
            name='Visits',
            line=dict(color='#2563eb', width=2),
            marker=dict(size=6),
            hovertemplate='%{x|%Y-%m-%d}<br>Visits: %{y:.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add trend line
    import numpy as np
    z = np.polyfit(range(len(df)), df['visit_count'], 1)
    p = np.poly1d(z)
    
    fig1.add_trace(
        go.Scatter(
            x=df['date'],
            y=p(range(len(df))),
            mode='lines',
            name='Trend',
            line=dict(color='#ef4444', width=2, dash='dash'),
            hovertemplate='Trend: %{y:.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Row 2: Conversion rate
    fig1.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['conversion_rate'],
            mode='lines+markers',
            name='Conversion Rate',
            line=dict(color='#10b981', width=2),
            marker=dict(size=6),
            hovertemplate='%{x|%Y-%m-%d}<br>Rate: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add mean line
    mean_conv = df['conversion_rate'].mean()
    fig1.add_trace(
        go.Scatter(
            x=[df['date'].min(), df['date'].max()],
            y=[mean_conv, mean_conv],
            mode='lines',
            name='Average',
            line=dict(color='#f59e0b', width=2, dash='dot'),
            hovertemplate=f'Average: {mean_conv:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig1.update_xaxes(title_text="Date", row=2, col=1, color='#000000', gridcolor='#e5e7eb')
    fig1.update_yaxes(title_text="Visit Count", row=1, col=1, color='#000000', gridcolor='#e5e7eb')
    fig1.update_yaxes(title_text="Conversion Rate (%)", row=2, col=1, color='#000000', gridcolor='#e5e7eb')
    
    fig1.update_layout(
        height=700,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#000000')
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Trend interpretation
    slope = z[0]
    if abs(slope) < 1:
        trend_text = "**Stable**: Visit count remains relatively constant over time."
        trend_color = "info-box"
    elif slope > 0:
        trend_text = f"**Increasing**: Visit count is growing by approximately {slope:.1f} visitors per day."
        trend_color = "success-box"
    else:
        trend_text = f"**Decreasing**: Visit count is declining by approximately {abs(slope):.1f} visitors per day."
        trend_color = "warning-box"
    
    st.markdown(f"""
    <div class='{trend_color}'>
        <h4>📊 Trend Analysis</h4>
        <p>{trend_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Weekday analysis
    st.markdown("### 📅 Weekday Comparison (48 days aggregated)")
    
    weekday_stats = df.groupby('weekday').agg({
        'conversion_rate': ['mean', 'std'],
        'visit_count': ['mean', 'std'],
        'total_traffic': ['mean', 'std']
    }).reset_index()
    
    weekday_stats.columns = ['weekday', 'conv_mean', 'conv_std', 'visit_mean', 'visit_std', 'traffic_mean', 'traffic_std']
    
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_stats['weekday_name'] = weekday_stats['weekday'].map(lambda x: weekday_names[x])
    
    # Weekday comparison chart
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=weekday_stats['weekday_name'],
        y=weekday_stats['visit_mean'],
        error_y=dict(type='data', array=weekday_stats['visit_std']),
        marker_color='#2563eb',
        name='Avg Visits',
        hovertemplate='%{x}<br>Visits: %{y:.1f} ± %{error_y.array:.1f}<extra></extra>'
    ))
    
    fig2.add_trace(go.Scatter(
        x=weekday_stats['weekday_name'],
        y=weekday_stats['conv_mean'],
        mode='lines+markers',
        name='Conversion Rate',
        line=dict(color='#10b981', width=3),
        marker=dict(size=10),
        yaxis='y2',
        hovertemplate='%{x}<br>Rate: %{y:.1f}%<extra></extra>'
    ))
    
    fig2.update_layout(
        title=None,
        xaxis_title="Day of Week",
        yaxis_title="Average Visit Count",
        yaxis2=dict(
            title=dict(text="Conversion Rate (%)", font=dict(color='#000000')),
            overlaying='y',
            side='right',
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#000000')
        )
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Best/worst days
    best_day = weekday_stats.loc[weekday_stats['visit_mean'].idxmax()]
    worst_day = weekday_stats.loc[weekday_stats['visit_mean'].idxmin()]
    best_conv_day = weekday_stats.loc[weekday_stats['conv_mean'].idxmax()]
    
    # Get business hours info
    profile = cache.get_store_profile(selected_store)
    business_hours = profile.get('business_hours', {})
    sunday_closed = business_hours.get('sunday', {}).get('closed', False)
    
    insights_list = [
        f"<li><strong>Highest Traffic Day</strong>: {best_day['weekday_name']} ({best_day['visit_mean']:.0f} visits)</li>",
        f"<li><strong>Lowest Traffic Day</strong>: {worst_day['weekday_name']} ({worst_day['visit_mean']:.0f} visits)</li>",
        f"<li><strong>Best Conversion Day</strong>: {best_conv_day['weekday_name']} ({best_conv_day['conv_mean']:.1f}%)</li>"
    ]
    
    # Add context about business hours
    if sunday_closed:
        insights_list.append("<li><strong>Note:</strong> Store is closed on Sundays</li>")
    
    if selected_store == 'Seoungbuk1':
        insights_list.append("<li><strong>Note:</strong> Saturday has shorter hours (08:30-15:00) vs weekdays (08:30-19:15)</li>")
    elif selected_store == 'Tyranno_Yongin':
        insights_list.append("<li><strong>Note:</strong> Weekdays open longest (08:00-23:00), weekends shorter (09:00-18:00)</li>")
    
    insights_html = ''.join(insights_list)
    st.markdown(f"""
    <div class='success-box'>
        <h4>📊 Weekday Insights</h4>
        <ul>
            {insights_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Weekly pattern heatmap
    st.markdown("### 🗓️ Weekly Pattern Heatmap")
    
    # Create week number
    df['week'] = (df['date'] - df['date'].min()).dt.days // 7
    df['weekday_short'] = df['date'].dt.strftime('%a')
    
    # Pivot for heatmap
    heatmap_data = df.pivot_table(
        values='visit_count',
        index='week',
        columns='weekday',
        aggfunc='mean'
    )
    
    # Map column names to weekday names
    heatmap_data.columns = [weekday_names[i][:3] for i in heatmap_data.columns]
    
    fig3 = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=[f'Week {i+1}' for i in heatmap_data.index],
        colorscale='Blues',
        hovertemplate='%{y}, %{x}<br>Visits: %{z:.0f}<extra></extra>',
        colorbar=dict(
            title=dict(text="Visits", font=dict(color='#000000')),
            tickfont=dict(color='#000000')
        )
    ))
    
    fig3.update_layout(
        title=None,
        xaxis_title="Day of Week",
        yaxis_title="Week",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            side='bottom'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000')
        )
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
    <div class='info-box'>
        <p><strong>Heatmap Interpretation</strong>: Darker colors indicate higher visit counts. 
        Look for consistent patterns across weeks to identify reliable traffic days.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AI-Powered Temporal Insights
    st.markdown("---")
    st.markdown("### 🤖 AI-Powered Temporal Insights")
    
    temporal_insights = []
    
    # Trend analysis
    if abs(slope) >= 1:
        if slope > 0:
            temporal_insights.append({
                'icon': '📈',
                'title': 'Growing Trend Detected',
                'text': f'Visit count is growing by ~{slope:.1f} visitors per day over the analysis period.',
                'action': 'Prepare for increased demand: consider inventory expansion, staffing optimization.',
                'priority': 'Opportunity'
            })
        else:
            temporal_insights.append({
                'icon': '📉',
                'title': 'Declining Trend Detected',
                'text': f'Visit count is declining by ~{abs(slope):.1f} visitors per day over the analysis period.',
                'action': 'Investigate causes: competition, seasonal factors, or service issues. Consider promotional campaigns.',
                'priority': 'High'
            })
    
    # Weekday optimization opportunities
    best_day = weekday_stats.loc[weekday_stats['visit_mean'].idxmax()]
    worst_day = weekday_stats.loc[weekday_stats['visit_mean'].idxmin()]
    
    visit_gap = best_day['visit_mean'] - worst_day['visit_mean']
    if visit_gap > 50:
        temporal_insights.append({
            'icon': '📊',
            'title': 'Significant Day-of-Week Variation',
            'text': f'{best_day["weekday_name"]} has {visit_gap:.0f} more visits than {worst_day["weekday_name"]}.',
            'action': f'Consider {worst_day["weekday_name"]}-specific promotions to balance weekly traffic.',
            'priority': 'Medium'
        })
    
    # Consistency analysis
    cv = df['visit_count'].std() / df['visit_count'].mean() * 100  # Coefficient of variation
    if cv > 50:
        temporal_insights.append({
            'icon': '⚠️',
            'title': 'High Traffic Volatility',
            'text': f'Daily visit count varies by {cv:.0f}% (high volatility).',
            'action': 'Analyze outlier days to understand factors causing extreme variations.',
            'priority': 'Medium'
        })
    elif cv < 20:
        temporal_insights.append({
            'icon': '✅',
            'title': 'Stable Traffic Pattern',
            'text': f'Daily visit count is consistent (CV: {cv:.0f}%), enabling reliable planning.',
            'action': 'Leverage predictability for efficient staffing and inventory management.',
            'priority': 'Opportunity'
        })
    
    # Display temporal insights
    for insight in temporal_insights:
        if insight['priority'] == 'High':
            box_class = 'warning-box'
        elif insight['priority'] == 'Opportunity':
            box_class = 'success-box'
        else:
            box_class = 'info-box'
        
        st.markdown(f"""
        <div class='{box_class}'>
            <h4>{insight['icon']} {insight['title']} <span style='font-size: 0.8em; color: #666;'>({insight['priority']} Priority)</span></h4>
            <p>{insight['text']}</p>
            <p><strong>💡 Recommendation:</strong> {insight['action']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if not temporal_insights:
        st.markdown("""
        <div class='info-box'>
            <p>✅ Traffic patterns are stable and within normal parameters.</p>
        </div>
        """, unsafe_allow_html=True)


def show_business_hours_impact_page(cache: CacheLoader, stores: list):
    """Analyze how business hours impact traffic and conversion"""
    
    st.markdown("## ⏰ Business Hours Impact Analysis")
    
    st.markdown("""
    This section analyzes how **different operating hours** affect each pharmacy's performance.
    Each store has unique business hours that significantly impact traffic patterns and conversion rates.
    """)
    
    # Display business hours comparison
    st.markdown("### 🕐 Business Hours Comparison")
    
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create business hours table
    hours_data = []
    for store_name in stores:
        profile = cache.get_store_profile(store_name)
        bh = profile.get('business_hours', {})
        
        # Weekday
        weekday = bh.get('weekday', {})
        weekday_hours = f"{int(weekday['open']):02d}:{int((weekday['open']%1)*60):02d} - {int(weekday['close']):02d}:{int((weekday['close']%1)*60):02d}" if weekday else "N/A"
        weekday_duration = weekday['close'] - weekday['open'] if weekday else 0
        
        # Saturday
        saturday = bh.get('saturday', {})
        if saturday.get('closed'):
            saturday_hours = "Closed"
            saturday_duration = 0
        else:
            saturday_hours = f"{int(saturday['open']):02d}:{int((saturday['open']%1)*60):02d} - {int(saturday['close']):02d}:{int((saturday['close']%1)*60):02d}" if saturday else "N/A"
            saturday_duration = saturday['close'] - saturday['open'] if saturday else 0
        
        # Sunday
        sunday = bh.get('sunday', {})
        if sunday.get('closed'):
            sunday_hours = "Closed"
            sunday_duration = 0
        else:
            sunday_hours = f"{int(sunday['open']):02d}:{int((sunday['open']%1)*60):02d} - {int(sunday['close']):02d}:{int((sunday['close']%1)*60):02d}" if sunday else "N/A"
            sunday_duration = sunday['close'] - sunday['open'] if sunday else 0
        
        hours_data.append({
            'Store': store_name,
            'Location Type': profile.get('type', 'Unknown'),
            'Weekday': weekday_hours,
            'Weekday Hours': weekday_duration,
            'Saturday': saturday_hours,
            'Saturday Hours': saturday_duration,
            'Sunday': sunday_hours,
            'Sunday Hours': sunday_duration,
            'Weekly Total': weekday_duration * 5 + saturday_duration + sunday_duration
        })
    
    df_hours = pd.DataFrame(hours_data)
    
    # Display table
    display_df = df_hours[['Store', 'Location Type', 'Weekday', 'Saturday', 'Sunday', 'Weekly Total']].copy()
    display_df['Weekly Total'] = display_df['Weekly Total'].apply(lambda x: f"{x:.1f} hrs")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Weekly operating hours comparison
    st.markdown("### 📊 Weekly Operating Hours")
    
    fig1 = go.Figure()
    
    colors = ['#2563eb', '#10b981', '#f59e0b']
    
    for i, store in enumerate(stores):
        store_data = df_hours[df_hours['Store'] == store].iloc[0]
        
        fig1.add_trace(go.Bar(
            name=store,
            x=['Weekday (×5)', 'Saturday', 'Sunday', 'Weekly Total'],
            y=[
                store_data['Weekday Hours'] * 5,
                store_data['Saturday Hours'],
                store_data['Sunday Hours'],
                store_data['Weekly Total']
            ],
            marker_color=colors[i],
            text=[
                f"{store_data['Weekday Hours']*5:.0f}h",
                f"{store_data['Saturday Hours']:.0f}h",
                f"{store_data['Sunday Hours']:.0f}h",
                f"{store_data['Weekly Total']:.0f}h"
            ],
            textposition='outside',
            hovertemplate='%{x}<br>Hours: %{y:.1f}<extra></extra>'
        ))
    
    fig1.update_layout(
        title=None,
        xaxis_title="Day Type",
        yaxis_title="Operating Hours",
        barmode='group',
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#000000')
        )
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("---")
    
    # Performance vs Operating Hours
    st.markdown("### 📈 Performance vs Operating Hours Analysis")
    
    # Get performance metrics
    comparison_data = cache.compare_stores(stores)
    
    # Combine data
    analysis_data = []
    for i, store in enumerate(comparison_data['stores']):
        store_hours = df_hours[df_hours['Store'] == store].iloc[0]
        analysis_data.append({
            'Store': store,
            'Location Type': comparison_data['location_types'][i],
            'Weekly Hours': store_hours['Weekly Total'],
            'Avg Daily Visits': comparison_data['avg_visits'][i],
            'Avg Daily Traffic': comparison_data['avg_traffic'][i],
            'Conversion Rate': comparison_data['conversion_rates'][i],
            'Visits per Hour': comparison_data['avg_visits'][i] / (store_hours['Weekly Total'] / 7) if store_hours['Weekly Total'] > 0 else 0
        })
    
    df_analysis = pd.DataFrame(analysis_data)
    
    # Scatter plot: Operating hours vs Visits per hour
    fig2 = go.Figure()
    
    for i, row in df_analysis.iterrows():
        fig2.add_trace(go.Scatter(
            x=[row['Weekly Hours']],
            y=[row['Visits per Hour']],
            mode='markers+text',
            name=row['Store'],
            marker=dict(size=20, color=colors[i]),
            text=[row['Store']],
            textposition='top center',
            textfont=dict(color='#000000', size=11),
            hovertemplate=f"<b>{row['Store']}</b><br>" +
                         f"Weekly Hours: {row['Weekly Hours']:.1f}<br>" +
                         f"Visits/Hour: {row['Visits per Hour']:.1f}<br>" +
                         f"<extra></extra>"
        ))
    
    fig2.update_layout(
        title=None,
        xaxis_title="Weekly Operating Hours",
        yaxis_title="Average Visits per Operating Hour",
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000', size=12),
        xaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            gridcolor='#e5e7eb'
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # Key insights
    st.markdown("### 💡 Business Hours Impact Insights")
    
    # Find extremes
    max_hours_store = df_analysis.loc[df_analysis['Weekly Hours'].idxmax()]
    min_hours_store = df_analysis.loc[df_analysis['Weekly Hours'].idxmin()]
    max_efficiency_store = df_analysis.loc[df_analysis['Visits per Hour'].idxmax()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class='info-box'>
            <h4>⏰ Operating Hours</h4>
            <ul>
                <li><strong>Longest Hours</strong>: {max_hours_store['Store']} ({max_hours_store['Weekly Hours']:.1f} hrs/week)</li>
                <li><strong>Shortest Hours</strong>: {min_hours_store['Store']} ({min_hours_store['Weekly Hours']:.1f} hrs/week)</li>
                <li><strong>Difference</strong>: {max_hours_store['Weekly Hours'] - min_hours_store['Weekly Hours']:.1f} hours/week</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='success-box'>
            <h4>📊 Efficiency Metrics</h4>
            <ul>
                <li><strong>Most Efficient</strong>: {max_efficiency_store['Store']} ({max_efficiency_store['Visits per Hour']:.1f} visits/hr)</li>
                <li><strong>Best Conversion</strong>: {df_analysis.loc[df_analysis['Conversion Rate'].idxmax(), 'Store']} ({df_analysis['Conversion Rate'].max():.1f}%)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed store insights
    st.markdown("### 🏪 Store-Specific Insights")
    
    for idx, row in df_analysis.iterrows():
        with st.expander(f"**{row['Store']}** - {row['Location Type']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Weekly Hours", f"{row['Weekly Hours']:.1f} hrs")
                st.metric("Daily Avg Hours", f"{row['Weekly Hours']/7:.1f} hrs")
            
            with col2:
                st.metric("Avg Daily Visits", f"{row['Avg Daily Visits']:.0f}")
                st.metric("Conversion Rate", f"{row['Conversion Rate']:.1f}%")
            
            with col3:
                st.metric("Visits per Hour", f"{row['Visits per Hour']:.1f}")
                efficiency_vs_avg = (row['Visits per Hour'] / df_analysis['Visits per Hour'].mean() - 1) * 100
                st.metric("Efficiency vs Avg", f"{efficiency_vs_avg:+.1f}%")
            
            # Store-specific recommendations
            store_hours = df_hours[df_hours['Store'] == row['Store']].iloc[0]
            
            recommendations = []
            
            # Seoungbuk1 insights
            if row['Store'] == 'Seoungbuk1':
                recommendations.append("🔒 **Sunday Closure**: No Sunday operations. Consider if weekend demand exists.")
                recommendations.append("⏰ **Short Saturday**: Only 6.5 hours on Saturday vs 10.75 hours on weekdays.")
                recommendations.append("📈 **High Efficiency**: Despite fewer hours, maintains strong conversion rate.")
                
            # Starfield_Suwon insights
            elif row['Store'] == 'Starfield_Suwon':
                recommendations.append("🔄 **Consistent Hours**: Same hours every day (10:00-22:00).")
                recommendations.append("🛍️ **Mall Alignment**: Hours match shopping mall operating times.")
                recommendations.append("📊 **Volume Strategy**: Maximizes exposure with consistent long hours.")
                
            # Tyranno_Yongin insights
            elif row['Store'] == 'Tyranno_Yongin':
                recommendations.append("⏰ **Longest Weekday Hours**: 15 hours on weekdays (08:00-23:00).")
                recommendations.append("📉 **Reduced Weekend**: Only 9 hours on weekends vs 15 on weekdays.")
                recommendations.append("🏢 **Building-Aligned**: Matches office/hospital hours on weekdays.")
            
            if recommendations:
                st.markdown("**Insights:**")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
    
    st.markdown("---")
    
    # Overall conclusions
    st.markdown("""
    <div class='warning-box'>
        <h4>🎯 Key Takeaways</h4>
        <ol>
            <li><strong>Hours ≠ Success</strong>: Longer operating hours don't guarantee more visits per hour. Efficiency matters.</li>
            <li><strong>Location Matters</strong>: Residential stores can succeed with shorter, strategic hours.</li>
            <li><strong>Weekend Strategy</strong>: Each store has different weekend approaches based on location type.</li>
            <li><strong>Consistency</strong>: Mall stores benefit from predictable daily hours; others adapt to customer patterns.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def show_dwell_time_page(cache: CacheLoader, stores: list):
    """Tab 6: Dwell Time Distribution Analysis"""
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    
    st.header("⏱️ Dwell Time Distribution Analysis")
    st.markdown("Understanding how long customers stay at each location")
    
    # NEW: Pharmacy-Specific Visit Segmentation
    st.subheader("🏥 Pharmacy Visit Segmentation")
    st.markdown("""
    <div class='info-box'>
        <strong>Customer behavior classification based on dwell time:</strong>
        <ul>
            <li><strong>Quick Visit (2-5 min)</strong>: OTC purchase, prescription pickup, brief inquiry</li>
            <li><strong>Standard Visit (5-15 min)</strong>: Medication counseling, general consultation</li>
            <li><strong>Extended Visit (15+ min)</strong>: Long wait, high-involvement products (supplements, etc.)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Get segmentation data
    seg_data = []
    for store in stores:
        stats = cache.get_aggregated_stats(store)
        if not stats:
            continue
        
        visit_seg = stats.get('visit_segmentation_total', {})
        visit_pct = stats.get('visit_segmentation_pct', {})
        
        if visit_seg:
            seg_data.append({
                'Store': store,
                'Quick Visit (2-5min)': visit_seg.get('quick_visit', 0),
                'Standard Visit (5-15min)': visit_seg.get('standard_visit', 0),
                'Extended Visit (15min+)': visit_seg.get('extended_visit', 0),
                'Quick %': visit_pct.get('quick_visit_pct', 0),
                'Standard %': visit_pct.get('standard_visit_pct', 0),
                'Extended %': visit_pct.get('extended_visit_pct', 0)
            })
    
    if seg_data:
        df_seg = pd.DataFrame(seg_data)
        
        # Display metrics
        cols = st.columns(len(stores))
        for idx, store in enumerate(stores):
            store_data = df_seg[df_seg['Store'] == store]
            if len(store_data) == 0:
                continue
            
            row = store_data.iloc[0]
            with cols[idx]:
                st.markdown(f"### {store}")
                
                # Pie chart for segmentation
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Quick (2-5min)', 'Standard (5-15min)', 'Extended (15min+)'],
                    values=[row['Quick Visit (2-5min)'], row['Standard Visit (5-15min)'], row['Extended Visit (15min+)']],
                    marker_colors=['#22c55e', '#3b82f6', '#8b5cf6'],
                    hole=0.4,
                    textinfo='percent',
                    textfont=dict(color='#000000')
                )])
                
                fig_pie.update_layout(
                    height=250,
                    margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor='white',
                    font=dict(color='#000000'),
                    showlegend=False
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
                
                st.metric("Quick Visit %", f"{row['Quick %']:.1f}%")
                st.metric("Standard Visit %", f"{row['Standard %']:.1f}%")
                st.metric("Extended Visit %", f"{row['Extended %']:.1f}%")
        
        st.markdown("---")
        
        # Comparative bar chart
        st.subheader("📊 Visit Type Comparison Across Stores")
        
        chart_data = []
        for _, row in df_seg.iterrows():
            chart_data.append({'Store': row['Store'], 'Visit Type': 'Quick (2-5min)', 'Percentage': row['Quick %']})
            chart_data.append({'Store': row['Store'], 'Visit Type': 'Standard (5-15min)', 'Percentage': row['Standard %']})
            chart_data.append({'Store': row['Store'], 'Visit Type': 'Extended (15min+)', 'Percentage': row['Extended %']})
        
        df_chart = pd.DataFrame(chart_data)
        
        fig = px.bar(
            df_chart,
            x='Store',
            y='Percentage',
            color='Visit Type',
            barmode='group',
            color_discrete_map={
                'Quick (2-5min)': '#22c55e',
                'Standard (5-15min)': '#3b82f6',
                'Extended (15min+)': '#8b5cf6'
            }
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#000000'),
            xaxis=dict(title='', tickfont=dict(color='#000000')),
            yaxis=dict(title='Percentage (%)', tickfont=dict(color='#000000')),
            legend=dict(font=dict(color='#000000'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.markdown("### 💡 Segmentation Insights")
        
        for store in stores:
            store_data = df_seg[df_seg['Store'] == store]
            if len(store_data) == 0:
                continue
            
            row = store_data.iloc[0]
            
            with st.expander(f"📍 {store} Analysis"):
                # Determine dominant pattern
                max_type = max([
                    ('Quick Visit', row['Quick %']),
                    ('Standard Visit', row['Standard %']),
                    ('Extended Visit', row['Extended %'])
                ], key=lambda x: x[1])
                
                st.markdown(f"**Dominant Pattern**: {max_type[0]} ({max_type[1]:.1f}%)")
                
                if store == 'Seoungbuk1':
                    st.markdown("""
                    - **Residential area**: Higher standard & extended visits
                    - Regular customers who know the pharmacist
                    - More consultation-heavy interactions
                    """)
                elif store == 'Starfield_Suwon':
                    st.markdown("""
                    - **Mall location**: Quick visits dominate
                    - Impulse OTC purchases
                    - Time-conscious shoppers
                    """)
                elif store == 'Tyranno_Yongin':
                    st.markdown("""
                    - **Mixed-use building**: Balanced distribution
                    - Hospital nearby → prescription customers
                    - Office workers + residents = diverse patterns
                    """)
    
    st.markdown("---")
    
    # Original dwell time analysis
    st.subheader("📈 Visitor Duration Distribution")
    st.markdown("*Only visitors who meet RSSI threshold (iPhone > -75dBm, Android > -85dBm)*")
    
    # Get aggregated dwell time data
    cols = st.columns(len(stores))
    
    dwell_data_all = {}
    
    for idx, store in enumerate(stores):
        stats = cache.get_aggregated_stats(store)
        
        if not stats:
            continue
        
        dwell_agg = stats.get('dwell_time_aggregate', {})
        dwell_cats = stats.get('dwell_categories_total', {})
        
        dwell_data_all[store] = {
            'stats': dwell_agg,
            'categories': dwell_cats
        }
        
        with cols[idx]:
            st.markdown(f"**{store}**")
            
            if dwell_agg:
                st.metric("Avg Duration", f"{dwell_agg.get('avg_mean', 0):.1f} min")
                st.metric("Median Duration", f"{dwell_agg.get('avg_median', 0):.1f} min")
    
    # Dwell time category comparison (visitors only - 2min+)
    # Realistic pharmacy dwell time categories
    category_labels = {
        '2_to_3min': '2-3 min',
        '3_to_6min': '3-6 min',
        '6_to_10min': '6-10 min',
        'over_10min': '10+ min'
    }
    
    chart_data = []
    for store, data in dwell_data_all.items():
        cats = data.get('categories', {})
        total = sum(cats.values()) if cats else 1
        
        for cat_key, cat_label in category_labels.items():
            count = cats.get(cat_key, 0)
            chart_data.append({
                'Store': store,
                'Duration': cat_label,
                'Count': count,
                'Percentage': (count / total * 100) if total > 0 else 0
            })
    
    if chart_data:
        df_chart = pd.DataFrame(chart_data)
        
        # Stacked bar chart (percentage)
        fig = px.bar(
            df_chart,
            x='Store',
            y='Percentage',
            color='Duration',
            title='Visitor Dwell Time Distribution (Realistic Pharmacy Durations)',
            color_discrete_sequence=['#22c55e', '#3b82f6', '#8b5cf6', '#ef4444'],
            barmode='stack'
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#000000'),
            xaxis=dict(title='', tickfont=dict(color='#000000')),
            yaxis=dict(title='Percentage (%)', tickfont=dict(color='#000000')),
            legend=dict(
                title=dict(text='Duration', font=dict(color='#000000')),
                font=dict(color='#000000')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_holiday_analysis_page(cache: CacheLoader, stores: list):
    """Tab 7: Holiday Impact Analysis"""
    import plotly.graph_objects as go
    import pandas as pd
    
    st.header("🎌 Holiday Impact Analysis")
    st.markdown("Comparing traffic patterns between holidays and regular days")
    
    # Collect holiday data from all stores
    holiday_comparison = []
    all_holidays = []
    
    for store in stores:
        stats = cache.get_aggregated_stats(store)
        
        if not stats:
            continue
        
        holiday_data = stats.get('holiday_analysis', {})
        
        if holiday_data:
            # Store holiday comparison
            holiday_comparison.append({
                'Store': store,
                'Holiday Days': holiday_data.get('total_holidays', 0),
                'Regular Days': holiday_data.get('total_non_holidays', 0),
                'Holiday Traffic': holiday_data.get('holiday_avg_traffic', 0),
                'Regular Traffic': holiday_data.get('non_holiday_avg_traffic', 0),
                'Holiday Conversion': holiday_data.get('holiday_avg_conversion', 0) * 100,
                'Regular Conversion': holiday_data.get('non_holiday_avg_conversion', 0) * 100
            })
            
            # Collect holiday dates
            if 'holiday_dates' in holiday_data:
                for hd in holiday_data['holiday_dates']:
                    all_holidays.append({
                        'Store': store,
                        'Date': hd['date'],
                        'Holiday': hd['name']
                    })
    
    if not holiday_comparison:
        st.warning("No holiday data available in the dataset.")
        return
    
    df_comparison = pd.DataFrame(holiday_comparison)
    
    # Summary metrics
    st.subheader("📊 Holiday vs Regular Day Comparison")
    
    cols = st.columns(len(stores))
    
    for idx, store in enumerate(stores):
        store_data = df_comparison[df_comparison['Store'] == store]
        
        if len(store_data) == 0:
            continue
        
        row = store_data.iloc[0]
        
        with cols[idx]:
            st.markdown(f"### {store}")
            
            # Traffic comparison
            traffic_diff = ((row['Holiday Traffic'] / row['Regular Traffic']) - 1) * 100 if row['Regular Traffic'] > 0 else 0
            st.metric(
                "Holiday Traffic",
                f"{row['Holiday Traffic']:.0f}",
                f"{traffic_diff:+.1f}% vs regular"
            )
            
            # Conversion comparison
            conv_diff = row['Holiday Conversion'] - row['Regular Conversion']
            st.metric(
                "Holiday Conversion",
                f"{row['Holiday Conversion']:.1f}%",
                f"{conv_diff:+.1f}pp vs regular"
            )
            
            st.caption(f"{row['Holiday Days']:.0f} holidays / {row['Regular Days']:.0f} regular days")
    
    st.markdown("---")
    
    # Visualization: Traffic comparison
    st.subheader("📈 Traffic Volume: Holiday vs Regular Days")
    
    fig = go.Figure()
    
    x = df_comparison['Store'].tolist()
    
    fig.add_trace(go.Bar(
        name='Holiday Days',
        x=x,
        y=df_comparison['Holiday Traffic'].tolist(),
        marker_color='#ef4444',
        text=[f"{v:.0f}" for v in df_comparison['Holiday Traffic']],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Regular Days',
        x=x,
        y=df_comparison['Regular Traffic'].tolist(),
        marker_color='#3b82f6',
        text=[f"{v:.0f}" for v in df_comparison['Regular Traffic']],
        textposition='outside'
    ))
    
    fig.update_layout(
        barmode='group',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000'),
        xaxis=dict(title='', tickfont=dict(color='#000000')),
        yaxis=dict(title='Average Daily Traffic', tickfont=dict(color='#000000')),
        legend=dict(font=dict(color='#000000'))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Visualization: Conversion comparison
    st.subheader("📊 Conversion Rate: Holiday vs Regular Days")
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        name='Holiday Days',
        x=x,
        y=df_comparison['Holiday Conversion'].tolist(),
        marker_color='#ef4444',
        text=[f"{v:.1f}%" for v in df_comparison['Holiday Conversion']],
        textposition='outside'
    ))
    
    fig2.add_trace(go.Bar(
        name='Regular Days',
        x=x,
        y=df_comparison['Regular Conversion'].tolist(),
        marker_color='#3b82f6',
        text=[f"{v:.1f}%" for v in df_comparison['Regular Conversion']],
        textposition='outside'
    ))
    
    fig2.update_layout(
        barmode='group',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000'),
        xaxis=dict(title='', tickfont=dict(color='#000000')),
        yaxis=dict(title='Conversion Rate (%)', tickfont=dict(color='#000000')),
        legend=dict(font=dict(color='#000000'))
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Holiday calendar
    if all_holidays:
        st.markdown("---")
        st.subheader("📅 Holidays in Dataset")
        
        df_holidays = pd.DataFrame(all_holidays)
        
        # Pivot to show which stores have data for each holiday
        holiday_summary = df_holidays.groupby(['Date', 'Holiday'])['Store'].apply(list).reset_index()
        holiday_summary.columns = ['Date', 'Holiday Name', 'Stores with Data']
        holiday_summary['Stores with Data'] = holiday_summary['Stores with Data'].apply(lambda x: ', '.join(x))
        
        st.dataframe(holiday_summary, use_container_width=True, hide_index=True)
    
    # Insights
    st.markdown("---")
    st.subheader("💡 Holiday Impact Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **General Observations:**
        - Holidays typically show different traffic patterns
        - Some stores see increases (destination shopping)
        - Others see decreases (reduced foot traffic areas)
        - Conversion rates often change during holidays
        """)
    
    with col2:
        st.markdown("""
        **Business Implications:**
        - Adjust staffing for holiday patterns
        - Plan inventory for holiday demands
        - Consider special promotions on holidays
        - Monitor specific holidays for your location type
        """)


def show_efficiency_heatmap_page(cache: CacheLoader, stores: list):
    """Tab 8: Hourly Efficiency Heatmap"""
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    
    st.header("🔥 Hourly Efficiency Heatmap")
    st.markdown("Visualizing traffic, visits, and conversion by day of week and hour")
    
    # Store selector
    selected_store = st.selectbox(
        "Select Store",
        stores,
        key="efficiency_store_select"
    )
    
    # Metric selector
    metric_option = st.radio(
        "Select Metric",
        ['Traffic Volume', 'Visit Count', 'Conversion Rate (%)'],
        horizontal=True
    )
    
    # Get heatmap data
    stats = cache.get_aggregated_stats(selected_store)
    
    if not stats:
        st.warning(f"No data available for {selected_store}")
        return
    
    matrix_data = stats.get('hourly_efficiency_matrix', {})
    
    if not matrix_data:
        st.warning("Heatmap data not available. Please regenerate cache with updated preprocessing.")
        return
    
    weekday_labels = matrix_data.get('weekday_labels', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    hour_labels = matrix_data.get('hour_labels', [f'{h:02d}:00' for h in range(24)])
    
    # Select matrix based on metric
    if metric_option == 'Traffic Volume':
        z_data = np.array(matrix_data.get('traffic_matrix', []))
        colorscale = 'Blues'
        title = f'{selected_store}: Traffic Volume by Day & Hour'
        colorbar_title = 'Traffic'
    elif metric_option == 'Visit Count':
        z_data = np.array(matrix_data.get('visit_matrix', []))
        colorscale = 'Greens'
        title = f'{selected_store}: Visit Count by Day & Hour'
        colorbar_title = 'Visits'
    else:
        z_data = np.array(matrix_data.get('conversion_matrix', []))
        colorscale = 'RdYlGn'
        title = f'{selected_store}: Conversion Rate by Day & Hour'
        colorbar_title = 'Rate (%)'
    
    if z_data.size == 0:
        st.warning("Matrix data is empty.")
        return
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=hour_labels,
        y=weekday_labels,
        colorscale=colorscale,
        colorbar=dict(
            title=dict(text=colorbar_title, font=dict(color='#000000')),
            tickfont=dict(color='#000000')
        ),
        hovertemplate='%{y}, %{x}<br>Value: %{z:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(color='#000000')),
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000'),
        xaxis=dict(
            title=dict(text='Hour of Day', font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            tickangle=45
        ),
        yaxis=dict(
            title=dict(text='Day of Week', font=dict(color='#000000')),
            tickfont=dict(color='#000000'),
            autorange='reversed'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Peak analysis
    st.subheader("📍 Peak Time Analysis")
    
    # Find peak times
    if z_data.size > 0:
        max_idx = np.unravel_index(np.argmax(z_data), z_data.shape)
        peak_day = weekday_labels[max_idx[0]]
        peak_hour = hour_labels[max_idx[1]]
        peak_value = z_data[max_idx]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Peak Day", peak_day)
        with col2:
            st.metric("Peak Hour", peak_hour)
        with col3:
            if metric_option == 'Conversion Rate (%)':
                st.metric("Peak Value", f"{peak_value:.1f}%")
            else:
                st.metric("Peak Value", f"{peak_value:.1f}")
        
        # Weekday vs Weekend comparison
        weekday_avg = np.mean(z_data[:5]) if z_data.shape[0] >= 5 else 0
        weekend_avg = np.mean(z_data[5:]) if z_data.shape[0] >= 7 else 0
        
        st.markdown("### 📊 Weekday vs Weekend")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Weekday Average", f"{weekday_avg:.1f}")
        with col2:
            st.metric("Weekend Average", f"{weekend_avg:.1f}")
    
    st.markdown("---")
    
    # All stores comparison (summary)
    st.subheader("🏪 All Stores Comparison")
    
    summary_data = []
    
    for store in stores:
        store_stats = cache.get_aggregated_stats(store)
        if not store_stats:
            continue
        
        store_matrix = store_stats.get('hourly_efficiency_matrix', {})
        if not store_matrix:
            continue
        
        traffic_matrix = np.array(store_matrix.get('traffic_matrix', []))
        visit_matrix = np.array(store_matrix.get('visit_matrix', []))
        conv_matrix = np.array(store_matrix.get('conversion_matrix', []))
        
        if traffic_matrix.size > 0:
            # Find peak for each metric
            traffic_peak = np.unravel_index(np.argmax(traffic_matrix), traffic_matrix.shape)
            visit_peak = np.unravel_index(np.argmax(visit_matrix), visit_matrix.shape)
            conv_peak = np.unravel_index(np.argmax(conv_matrix), conv_matrix.shape)
            
            wl = store_matrix.get('weekday_labels', weekday_labels)
            hl = store_matrix.get('hour_labels', hour_labels)
            
            summary_data.append({
                'Store': store,
                'Peak Traffic': f"{wl[traffic_peak[0]]} {hl[traffic_peak[1]]}",
                'Peak Visits': f"{wl[visit_peak[0]]} {hl[visit_peak[1]]}",
                'Peak Conversion': f"{wl[conv_peak[0]]} {hl[conv_peak[1]]}",
                'Best Day (Traffic)': wl[np.argmax(np.mean(traffic_matrix, axis=1))],
                'Best Hour (Traffic)': hl[np.argmax(np.mean(traffic_matrix, axis=0))]
            })
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # Insights
    st.markdown("""
    <div class='info-box'>
        <h4>💡 How to Use This Heatmap</h4>
        <ul>
            <li><strong>Identify Peak Hours</strong>: Dark colors indicate high activity periods</li>
            <li><strong>Staff Scheduling</strong>: Align staff with high-traffic hours</li>
            <li><strong>Promotions</strong>: Target low-traffic hours for promotional activities</li>
            <li><strong>Compare Days</strong>: Understand weekday vs weekend patterns</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def show_efficiency_benchmark_page(cache: CacheLoader, stores: list):
    """Tab 9: Efficiency Benchmarking Analysis"""
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import numpy as np
    
    st.header("📐 Efficiency Benchmarking")
    st.markdown("Analyzing operational efficiency: Visitors Per Hour (VPH) and time-slot performance")
    
    # Explanation
    st.markdown("""
    <div class='info-box'>
        <strong>Key Metrics:</strong>
        <ul>
            <li><strong>VPH (Visitors Per Hour)</strong>: Total weekly visitors ÷ Weekly operating hours</li>
            <li><strong>TPH (Traffic Per Hour)</strong>: Total weekly traffic ÷ Weekly operating hours</li>
            <li><strong>Efficiency Score</strong>: Normalized VPH score for comparison</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Get efficiency data for all stores
    efficiency_data = []
    hourly_vph_data = {}
    
    for store in stores:
        # Try to get efficiency metrics from cache
        try:
            cache_data = cache.cache.get(store, {})
            eff_metrics = cache_data.get('efficiency_metrics', {})
            
            if eff_metrics:
                efficiency_data.append({
                    'Store': store,
                    'Weekly Hours': eff_metrics.get('weekly_hours', 0),
                    'Avg Daily Visits': eff_metrics.get('avg_daily_visits', 0),
                    'Avg Daily Traffic': eff_metrics.get('avg_daily_traffic', 0),
                    'VPH': eff_metrics.get('visitors_per_hour', 0),
                    'TPH': eff_metrics.get('traffic_per_hour', 0),
                    'Efficiency Score': eff_metrics.get('efficiency_score', 0)
                })
                
                hourly_vph_data[store] = eff_metrics.get('hourly_vph', [])
        except:
            pass
    
    if not efficiency_data:
        st.warning("Efficiency metrics not available. Please regenerate cache with updated preprocessing.")
        return
    
    df_eff = pd.DataFrame(efficiency_data)
    
    # Overview metrics
    st.subheader("📊 Store Efficiency Overview")
    
    cols = st.columns(len(stores))
    
    for idx, store in enumerate(stores):
        store_data = df_eff[df_eff['Store'] == store]
        if len(store_data) == 0:
            continue
        
        row = store_data.iloc[0]
        
        with cols[idx]:
            st.markdown(f"### {store}")
            st.metric("Weekly Hours", f"{row['Weekly Hours']:.1f} hrs")
            st.metric("VPH", f"{row['VPH']:.2f}")
            st.metric("TPH", f"{row['TPH']:.2f}")
            
            # Compare to average
            avg_vph = df_eff['VPH'].mean()
            vph_diff = ((row['VPH'] / avg_vph) - 1) * 100 if avg_vph > 0 else 0
            st.metric("vs Average", f"{vph_diff:+.1f}%")
    
    st.markdown("---")
    
    # VPH Comparison Chart
    st.subheader("📈 Visitors Per Hour (VPH) Comparison")
    
    fig = go.Figure()
    
    # VPH bars
    fig.add_trace(go.Bar(
        name='VPH',
        x=df_eff['Store'].tolist(),
        y=df_eff['VPH'].tolist(),
        marker_color='#3b82f6',
        text=[f"{v:.2f}" for v in df_eff['VPH']],
        textposition='outside'
    ))
    
    # Average line
    avg_vph = df_eff['VPH'].mean()
    fig.add_hline(y=avg_vph, line_dash="dash", line_color="#ef4444",
                  annotation_text=f"Average: {avg_vph:.2f}")
    
    fig.update_layout(
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000'),
        xaxis=dict(title='', tickfont=dict(color='#000000')),
        yaxis=dict(title='Visitors Per Hour', tickfont=dict(color='#000000')),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Weekly Hours vs VPH Scatter
    st.subheader("⚖️ Operating Hours vs Efficiency Trade-off")
    
    fig2 = px.scatter(
        df_eff,
        x='Weekly Hours',
        y='VPH',
        size='Avg Daily Visits',
        color='Store',
        text='Store',
        color_discrete_sequence=['#ef4444', '#22c55e', '#3b82f6']
    )
    
    fig2.update_traces(textposition='top center', marker=dict(sizemin=20))
    
    fig2.update_layout(
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#000000'),
        xaxis=dict(title='Weekly Operating Hours', tickfont=dict(color='#000000')),
        yaxis=dict(title='Visitors Per Hour (VPH)', tickfont=dict(color='#000000')),
        legend=dict(font=dict(color='#000000'))
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("""
    <div class='warning-box'>
        <strong>💡 Key Insight:</strong> 
        Longer operating hours don't always mean higher efficiency. 
        Look for stores in the upper-left quadrant (high VPH, fewer hours) for optimal efficiency.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Hourly VPH Analysis
    st.subheader("⏰ Hourly Efficiency Analysis")
    
    selected_store = st.selectbox("Select Store for Hourly Analysis", stores, key="hourly_eff_store")
    
    if selected_store in hourly_vph_data and hourly_vph_data[selected_store]:
        hourly_data = hourly_vph_data[selected_store]
        
        df_hourly = pd.DataFrame(hourly_data)
        
        # Create hourly efficiency chart
        fig3 = go.Figure()
        
        fig3.add_trace(go.Bar(
            name='Visits/Hour',
            x=[f"{h:02d}:00" for h in df_hourly['hour']],
            y=df_hourly['avg_visits_per_hour'],
            marker_color='#22c55e'
        ))
        
        # Add average line
        avg_hourly = df_hourly['avg_visits_per_hour'].mean()
        fig3.add_hline(y=avg_hourly, line_dash="dash", line_color="#ef4444",
                      annotation_text=f"Avg: {avg_hourly:.2f}")
        
        fig3.update_layout(
            title=f'{selected_store}: Hourly Visit Rate',
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#000000'),
            xaxis=dict(title='Hour', tickfont=dict(color='#000000'), tickangle=45),
            yaxis=dict(title='Avg Visits per Hour', tickfont=dict(color='#000000'))
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # Most and least efficient hours
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Most Efficient Hours**")
            top_hours = df_hourly.nlargest(3, 'avg_visits_per_hour')
            for _, row in top_hours.iterrows():
                st.markdown(f"- {int(row['hour']):02d}:00 - {row['avg_visits_per_hour']:.2f} visits/hr")
        
        with col2:
            st.markdown("**🔴 Least Efficient Hours**")
            bottom_hours = df_hourly.nsmallest(3, 'avg_visits_per_hour')
            for _, row in bottom_hours.iterrows():
                st.markdown(f"- {int(row['hour']):02d}:00 - {row['avg_visits_per_hour']:.2f} visits/hr")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("📋 Efficiency Recommendations")
    
    for store in stores:
        store_data = df_eff[df_eff['Store'] == store]
        if len(store_data) == 0:
            continue
        
        row = store_data.iloc[0]
        
        with st.expander(f"📍 {store}"):
            # Calculate efficiency ranking
            vph_rank = df_eff['VPH'].rank(ascending=False)[df_eff['Store'] == store].values[0]
            hours_rank = df_eff['Weekly Hours'].rank(ascending=False)[df_eff['Store'] == store].values[0]
            
            st.markdown(f"**VPH Rank**: #{int(vph_rank)} of {len(stores)}")
            st.markdown(f"**Hours Rank**: #{int(hours_rank)} (most hours)")
            
            recommendations = []
            
            if store == 'Seoungbuk1':
                recommendations.extend([
                    "✅ **Highest Efficiency**: Despite shortest hours, achieves highest VPH",
                    "💡 **Strategy**: Focus on quality over quantity - current approach works",
                    "⚠️ **Consider**: Limited Sunday service may miss some demand"
                ])
            
            elif store == 'Starfield_Suwon':
                recommendations.extend([
                    "📊 **Mall Dynamics**: Lower VPH is expected due to high pass-by traffic",
                    "💡 **Strategy**: Focus on conversion improvement, not hour expansion",
                    "⚠️ **Consider**: Identify low-traffic hours for staff optimization"
                ])
            
            elif store == 'Tyranno_Yongin':
                recommendations.extend([
                    "⏰ **Longest Hours**: 93+ hours/week with moderate efficiency",
                    "💡 **Strategy**: Analyze if early morning (8-10) and late evening (21-23) justify staffing",
                    "⚠️ **Consider**: Weekend hours (9-18) may not match building traffic patterns"
                ])
            
            for rec in recommendations:
                st.markdown(rec)
    
    # Summary Table
    st.markdown("---")
    st.subheader("📊 Efficiency Summary Table")
    
    summary_df = df_eff.copy()
    summary_df['VPH Rank'] = summary_df['VPH'].rank(ascending=False).astype(int)
    summary_df['Efficiency Rating'] = summary_df['VPH'].apply(
        lambda x: '⭐⭐⭐' if x > df_eff['VPH'].mean() * 1.2 else 
                  ('⭐⭐' if x > df_eff['VPH'].mean() * 0.8 else '⭐')
    )
    
    st.dataframe(
        summary_df[['Store', 'Weekly Hours', 'Avg Daily Visits', 'VPH', 'VPH Rank', 'Efficiency Rating']],
        use_container_width=True,
        hide_index=True
    )


if __name__ == "__main__":
    main()
