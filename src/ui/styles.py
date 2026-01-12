"""
Custom CSS Styles for Professional Dashboard
White background with black text, clean and modern design
"""

CUSTOM_CSS = """
<style>
/* Global Styles */
.stApp {
    background-color: #FFFFFF;
}

/* Main container */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    color: #1a1a1a !important;
    font-weight: 600 !important;
}

h1 {
    font-size: 2.5rem !important;
    margin-bottom: 1rem !important;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 0.5rem;
}

h2 {
    font-size: 1.8rem !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    color: #2563eb !important;
}

h3 {
    font-size: 1.4rem !important;
    margin-top: 1.5rem !important;
    color: #374151 !important;
}

/* Text */
p, li, span, div {
    color: #1f2937 !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
}

/* Metric cards */
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;
    color: #6b7280 !important;
    font-weight: 500 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.85rem !important;
}

/* Info boxes */
.info-box {
    background-color: #f8fafc;
    border-left: 4px solid #2563eb;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    border-radius: 0.25rem;
}

.warning-box {
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    border-radius: 0.25rem;
}

.success-box {
    background-color: #d1fae5;
    border-left: 4px solid #10b981;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    border-radius: 0.25rem;
}

/* Buttons */
.stButton > button {
    background-color: #2563eb;
    color: white;
    font-weight: 600;
    border-radius: 0.375rem;
    padding: 0.5rem 2rem;
    border: none;
    transition: all 0.2s;
}

.stButton > button:hover {
    background-color: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Tabs Container - with scroll navigation */
.stTabs {
    position: relative;
}

/* Tabs - scrollable with native scrollbar */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background-color: #f9fafb;
    padding: 0.75rem 1rem;
    padding-bottom: 1.5rem;
    border-radius: 0.5rem;
    overflow-x: scroll !important;
    overflow-y: hidden !important;
    flex-wrap: nowrap !important;
    white-space: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scroll-behavior: smooth;
    position: relative;
}

/* Force visible scrollbar - Standard */
.stTabs [data-baseweb="tab-list"] {
    scrollbar-width: auto !important;
    scrollbar-color: #4b5563 #e5e7eb !important;
}

/* Force visible scrollbar - WebKit (Chrome, Safari, Edge) */
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    height: 14px !important;
    display: block !important;
    -webkit-appearance: none !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
    background: #d1d5db !important;
    border-radius: 7px !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
    background-color: #4b5563 !important;
    border-radius: 7px !important;
    border: 2px solid #d1d5db !important;
    min-width: 60px !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover {
    background-color: #374151 !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:active {
    background-color: #1f2937 !important;
}

/* Tab buttons */
.stTabs [data-baseweb="tab"] {
    color: #1f2937 !important;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    flex-shrink: 0 !important;
    min-width: fit-content !important;
    background-color: #e5e7eb;
    margin: 0.1rem;
    cursor: pointer;
}

.stTabs [aria-selected="true"] {
    background-color: #2563eb !important;
    color: white !important;
}

/* Dividers */
hr {
    margin: 2rem 0;
    border: 0;
    border-top: 2px solid #e5e7eb;
}

/* Cards */
div[data-testid="column"] {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #f9fafb;
    padding: 2rem 1rem;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #1a1a1a !important;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: #f3f4f6;
    color: #1f2937 !important;
    font-weight: 600;
    border-radius: 0.375rem;
}

.streamlit-expanderContent {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-top: none;
}

/* Dataframe */
.dataframe {
    font-size: 0.9rem !important;
}

.dataframe thead tr th {
    background-color: #f3f4f6 !important;
    color: #1f2937 !important;
    font-weight: 600 !important;
}

.dataframe tbody tr:hover {
    background-color: #f9fafb !important;
}

/* Select box / Dropdown - FORCE WHITE BACKGROUND */
.stSelectbox label {
    color: #374151 !important;
    font-weight: 600 !important;
}

.stSelectbox > div > div {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

.stSelectbox [data-baseweb="select"] {
    background-color: #ffffff !important;
}

.stSelectbox [data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

/* Dropdown menu - CRITICAL: Force white background everywhere */
[data-baseweb="popover"] {
    background-color: #ffffff !important;
}

[data-baseweb="popover"] > div {
    background-color: #ffffff !important;
}

[data-baseweb="menu"] {
    background-color: #ffffff !important;
}

[data-baseweb="menu"] > div {
    background-color: #ffffff !important;
}

[data-baseweb="menu"] ul {
    background-color: #ffffff !important;
}

[data-baseweb="menu"] li {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

[data-baseweb="menu"] li:hover {
    background-color: #f3f4f6 !important;
    color: #1f2937 !important;
}

/* BaseWeb List styles - dropdown items */
[data-baseweb="list"] {
    background-color: #ffffff !important;
}

[data-baseweb="list-item"] {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

[data-baseweb="list-item"]:hover {
    background-color: #f3f4f6 !important;
}

/* Select dropdown specific */
div[data-baseweb="select"] div[role="listbox"] {
    background-color: #ffffff !important;
}

div[data-baseweb="select"] div[role="option"] {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

div[data-baseweb="select"] div[role="option"]:hover {
    background-color: #f3f4f6 !important;
}

/* Highlighted/focused option */
div[data-baseweb="select"] div[aria-selected="true"] {
    background-color: #e0e7ff !important;
    color: #1f2937 !important;
}

[data-baseweb="select"] [data-baseweb="icon"] {
    color: #1f2937 !important;
}

/* Radio buttons */
.stRadio label {
    color: #374151 !important;
    font-weight: 500 !important;
}

.stRadio > div {
    background-color: #ffffff !important;
}

.stRadio [data-baseweb="radio"] span {
    color: #1f2937 !important;
}

/* Multiselect */
.stMultiSelect label {
    color: #374151 !important;
    font-weight: 600 !important;
}

/* Date input */
.stDateInput label {
    color: #374151 !important;
    font-weight: 600 !important;
}

/* Slider */
.stSlider label {
    color: #374151 !important;
    font-weight: 600 !important;
}

/* Progress bar */
.stProgress > div > div {
    background-color: #2563eb;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #2563eb !important;
}

/* Alert */
.stAlert {
    background-color: #eff6ff;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
}

/* Code blocks */
code {
    background-color: #f3f4f6;
    color: #1f2937;
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
}

pre {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 1rem;
}

/* Footer */
.footer {
    text-align: center;
    color: #9ca3af;
    font-size: 0.875rem;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #e5e7eb;
}

/* Plotly Charts - Force black text */
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle {
    fill: #000000 !important;
}

.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text {
    fill: #000000 !important;
}

.js-plotly-plot .plotly .legendtext {
    fill: #000000 !important;
}

.js-plotly-plot .plotly .annotation-text {
    fill: #000000 !important;
}

.js-plotly-plot .plotly .cbtitle {
    fill: #000000 !important;
}

.js-plotly-plot .plotly .crisp {
    fill: #000000 !important;
}

/* Plotly modebar */
.js-plotly-plot .plotly .modebar-btn {
    fill: #374151 !important;
}

/* Streamlit specific overrides */
[data-testid="stMarkdownContainer"] {
    color: #1f2937 !important;
}

[data-testid="stText"] {
    color: #1f2937 !important;
}

/* Dark mode override - force light theme */
@media (prefers-color-scheme: dark) {
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    .stSelectbox [data-baseweb="select"],
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="menu"] ul,
    [data-baseweb="menu"] li {
        background-color: #FFFFFF !important;
        color: #1f2937 !important;
    }
}
</style>
"""

# JavaScript for tab scrolling functionality
TAB_SCROLL_JS = """
<script>
(function() {
    function initTabScroll() {
        const tabLists = document.querySelectorAll('[data-baseweb="tab-list"]');
        
        tabLists.forEach(function(tabList) {
            if (tabList.dataset.scrollInitialized) return;
            tabList.dataset.scrollInitialized = 'true';
            
            let isDown = false;
            let startX;
            let scrollLeft;
            
            // Mouse drag scroll
            tabList.addEventListener('mousedown', function(e) {
                if (e.target.closest('[data-baseweb="tab"]')) return;
                isDown = true;
                tabList.style.cursor = 'grabbing';
                startX = e.pageX - tabList.offsetLeft;
                scrollLeft = tabList.scrollLeft;
            });
            
            tabList.addEventListener('mouseleave', function() {
                isDown = false;
                tabList.style.cursor = 'grab';
            });
            
            tabList.addEventListener('mouseup', function() {
                isDown = false;
                tabList.style.cursor = 'grab';
            });
            
            tabList.addEventListener('mousemove', function(e) {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - tabList.offsetLeft;
                const walk = (x - startX) * 2;
                tabList.scrollLeft = scrollLeft - walk;
            });
            
            // Mouse wheel horizontal scroll
            tabList.addEventListener('wheel', function(e) {
                if (Math.abs(e.deltaX) < Math.abs(e.deltaY)) {
                    e.preventDefault();
                    tabList.scrollLeft += e.deltaY;
                }
            }, { passive: false });
        });
    }
    
    // Run on load and periodically check for new tabs
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initTabScroll, 500);
        });
    } else {
        setTimeout(initTabScroll, 500);
    }
    
    // Also run on any DOM changes (for Streamlit rerenders)
    const observer = new MutationObserver(function(mutations) {
        setTimeout(initTabScroll, 100);
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""


def get_custom_css():
    """Return custom CSS for the dashboard"""
    return CUSTOM_CSS


def get_tab_scroll_js():
    """Return JavaScript for tab scrolling"""
    return TAB_SCROLL_JS
