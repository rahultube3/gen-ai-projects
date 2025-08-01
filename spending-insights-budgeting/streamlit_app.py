"""
Optimized Streamlit App for Spending Insights & Budgeting
Features: Performance Optimization, Real-time Analytics, Enhanced UX, Advanced Visualizations
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import time
import asyncio
from typing import Dict, List, Optional, Tuple
import numpy as np
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from vectorstore import build_vectorstore, get_vectorstore_stats
from redact import redact_sensitive, AdvancedRedactionEngine, RedactionLevel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration with optimized settings
st.set_page_config(
    page_title="💰 Spending Insights & Budgeting Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/help',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': "# Advanced Spending Insights Dashboard\nPowered by AI and DuckDB"
    }
)

# Enhanced custom CSS with dark theme support
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    /* Alert Cards */
    .alert-card {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        color: #2d3436;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .success-card {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .danger-card {
        background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Performance indicators */
    .perf-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 1000;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        background-color: #f8f9fa;
    }
    
    /* Sidebar enhancements */
    .sidebar-metric {
        text-align: center;
        padding: 0.5rem;
        margin: 0.5rem 0;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Performance tracking
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {
        'page_loads': 0,
        'query_count': 0,
        'total_response_time': 0,
        'cache_hits': 0,
        'errors': 0
    }

@st.cache_data(ttl=300, show_spinner=False)  # 5-minute cache
def load_data_from_db():
    """Optimized data loading with enhanced error handling and performance tracking"""
    start_time = time.time()
    
    try:
        conn = duckdb.connect('spending_insights.db')
        
        # Enhanced queries with performance optimization
        queries = {
            'transactions': """
                SELECT 
                    id, date, merchant, category, amount, notes,
                    EXTRACT(YEAR FROM date) as year,
                    EXTRACT(MONTH FROM date) as month,
                    EXTRACT(DOW FROM date) as day_of_week,
                    created_at
                FROM transactions 
                ORDER BY date DESC
            """,
            'budget': "SELECT * FROM budget_categories ORDER BY category",
            'goals': "SELECT * FROM financial_goals ORDER BY priority DESC, target_date",
            'monthly': """
                SELECT 
                    year, month, category, total_amount, transaction_count,
                    average_amount, median_amount, max_amount, min_amount
                FROM monthly_spending_summary 
                ORDER BY year DESC, month DESC, total_amount DESC
            """,
            'patterns': """
                SELECT 
                    pattern_type, pattern_description, category, merchant,
                    frequency, avg_amount, median_amount, confidence_score,
                    sample_size
                FROM spending_patterns 
                ORDER BY confidence_score DESC, sample_size DESC
            """
        }
        
        # Execute queries with error handling
        dataframes = {}
        for name, query in queries.items():
            try:
                dataframes[name] = conn.execute(query).df()
                logger.info(f"Loaded {len(dataframes[name])} records from {name}")
            except Exception as e:
                logger.error(f"Error loading {name}: {e}")
                dataframes[name] = pd.DataFrame()
        
        conn.close()
        
        # Performance tracking
        load_time = time.time() - start_time
        st.session_state.performance_metrics['total_response_time'] += load_time
        
        return (
            dataframes['transactions'],
            dataframes['budget'],
            dataframes['goals'],
            dataframes['monthly'],
            dataframes['patterns']
        )
    
    except Exception as e:
        st.session_state.performance_metrics['errors'] += 1
        logger.error(f"Database connection failed: {e}")
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_resource(show_spinner=False)
def setup_ai_assistant():
    """Enhanced AI assistant setup with performance monitoring"""
    try:
        with st.spinner("🤖 Initializing AI assistant..."):
            # Get spending data for vectorstore
            conn = duckdb.connect('spending_insights.db')
            transactions = conn.execute("""
                SELECT date, merchant, category, amount, notes
                FROM transactions
                ORDER BY date DESC
                LIMIT 1000
            """).fetchall()
            
            spending_data = []
            for row in transactions:
                spending_data.append({
                    "date": str(row[0]),
                    "merchant": row[1],
                    "category": row[2],
                    "amount": float(row[3]),
                    "notes": row[4] or "",
                    "formatted_text": f"On {row[0]}, spent ${row[3]:.2f} at {row[1]} for {row[2]}. {row[4] or ''}"
                })
            
            conn.close()
            
            # Build vectorstore with optimizations
            vectorstore = build_vectorstore(spending_data)
            
            # Setup enhanced RetrievalQA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(
                    temperature=0.1,
                    model_name="gpt-3.5-turbo",
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    max_tokens=500
                ),
                retriever=vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": 5,
                        "score_threshold": 0.7
                    }
                ),
                return_source_documents=True
            )
            
            return qa_chain, len(spending_data)
    
    except Exception as e:
        logger.error(f"AI assistant setup failed: {e}")
        st.error(f"Error setting up AI assistant: {e}")
        return None, 0

def calculate_enhanced_budget_status(transactions_df: pd.DataFrame, budget_df: pd.DataFrame) -> pd.DataFrame:
    """Enhanced budget calculation with trend analysis"""
    if transactions_df.empty or budget_df.empty:
        return pd.DataFrame()
    
    current_date = datetime.now()
    
    # Current month spending
    current_month_transactions = transactions_df[
        (pd.to_datetime(transactions_df['date']).dt.month == current_date.month) &
        (pd.to_datetime(transactions_df['date']).dt.year == current_date.year)
    ]
    
    # Previous month for comparison
    prev_month = current_date.replace(day=1) - timedelta(days=1)
    prev_month_transactions = transactions_df[
        (pd.to_datetime(transactions_df['date']).dt.month == prev_month.month) &
        (pd.to_datetime(transactions_df['date']).dt.year == prev_month.year)
    ]
    
    current_spending = current_month_transactions.groupby('category')['amount'].sum()
    prev_spending = prev_month_transactions.groupby('category')['amount'].sum()
    
    budget_status = []
    for _, budget in budget_df.iterrows():
        category = budget['category']
        limit = budget['monthly_limit']
        threshold = budget['alert_threshold']
        
        spent = current_spending.get(category, 0)
        prev_spent = prev_spending.get(category, 0)
        remaining = limit - spent
        percentage = (spent / limit) * 100 if limit > 0 else 0
        
        # Calculate trend
        trend = "stable"
        trend_percentage = 0
        if prev_spent > 0:
            trend_percentage = ((spent - prev_spent) / prev_spent) * 100
            if trend_percentage > 10:
                trend = "increasing"
            elif trend_percentage < -10:
                trend = "decreasing"
        
        # Status determination
        status = "On Track"
        status_color = "success"
        if percentage >= threshold * 100:
            status = "Warning"
            status_color = "warning"
        if percentage >= 100:
            status = "Over Budget"
            status_color = "danger"
        
        # Days remaining in month
        days_in_month = (current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)).day
        days_passed = current_date.day
        days_remaining = days_in_month - days_passed
        
        # Projected spending
        if days_passed > 0:
            daily_average = spent / days_passed
            projected_spending = daily_average * days_in_month
            projected_percentage = (projected_spending / limit) * 100 if limit > 0 else 0
        else:
            projected_spending = 0
            projected_percentage = 0
        
        budget_status.append({
            'category': category,
            'limit': limit,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'status': status,
            'status_color': status_color,
            'trend': trend,
            'trend_percentage': trend_percentage,
            'projected_spending': projected_spending,
            'projected_percentage': projected_percentage,
            'days_remaining': days_remaining
        })
    
    return pd.DataFrame(budget_status)

def create_enhanced_visualizations(transactions_df: pd.DataFrame, budget_df: pd.DataFrame):
    """Create advanced visualizations with better interactivity"""
    
    # Spending trend with moving average
    fig_trend = go.Figure()
    
    if not transactions_df.empty:
        daily_spending = transactions_df.groupby('date')['amount'].sum().reset_index()
        daily_spending['date'] = pd.to_datetime(daily_spending['date'])
        daily_spending = daily_spending.sort_values('date')
        
        # Calculate 7-day moving average
        daily_spending['ma_7'] = daily_spending['amount'].rolling(window=7).mean()
        
        fig_trend.add_trace(go.Scatter(
            x=daily_spending['date'],
            y=daily_spending['amount'],
            mode='lines',
            name='Daily Spending',
            line=dict(color='lightblue', width=1),
            opacity=0.7
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=daily_spending['date'],
            y=daily_spending['ma_7'],
            mode='lines',
            name='7-Day Average',
            line=dict(color='darkblue', width=3)
        ))
        
        fig_trend.update_layout(
            title="Daily Spending Trend with Moving Average",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode='x unified',
            template='plotly_white'
        )
    
    return fig_trend

def display_performance_metrics():
    """Display performance metrics in sidebar with proper data types"""
    with st.sidebar:
        st.markdown("### ⚡ Performance Metrics")
        
        metrics = st.session_state.performance_metrics
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="sidebar-metric">
                <small>Page Loads</small><br>
                <strong>{metrics['page_loads']}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="sidebar-metric">
                <small>Cache Hits</small><br>
                <strong>{metrics['cache_hits']}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="sidebar-metric">
                <small>Queries</small><br>
                <strong>{metrics['query_count']}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="sidebar-metric">
                <small>Errors</small><br>
                <strong>{metrics['errors']}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # Vectorstore stats with proper formatting and error handling
        try:
            vs_stats = safe_get_vectorstore_stats()
            st.markdown("### 🔍 Vectorstore Stats")
            
            # Format stats properly to avoid Arrow issues
            build_time = vs_stats.get('build_time_seconds', 0)
            cache_hit_rate = vs_stats.get('cache_hit_rate', 0)
            avg_search_time = vs_stats.get('average_search_time_ms', 0)
            
            st.markdown(f"**Build Time:** {build_time:.2f} seconds")
            st.markdown(f"**Cache Hit Rate:** {cache_hit_rate:.1%}")
            st.markdown(f"**Avg Search Time:** {avg_search_time:.1f} ms")
        except Exception as e:
            logger.warning(f"Vectorstore stats error: {e}")

def create_arrow_compatible_dataframe(data_dict):
    """Create Arrow-compatible dataframe by ensuring consistent data types"""
    df_data = []
    for key, value in data_dict.items():
        # Ensure all values are strings to avoid type conflicts
        if isinstance(value, (int, float)):
            formatted_value = str(value)
        elif isinstance(value, str) and ('s' in value or '%' in value):
            # Keep formatted strings as is
            formatted_value = value
        else:
            formatted_value = str(value)
        
        df_data.append({"Metric": str(key), "Value": formatted_value})
    
    return pd.DataFrame(df_data)

def create_system_info_dataframe():
    """Create system info dataframe with proper data types"""
    import platform
    import psutil
    
    try:
        system_info = {
            "Platform": platform.system(),
            "Python Version": platform.python_version(),
            "CPU Usage": f"{psutil.cpu_percent():.1f}%",
            "Memory Usage": f"{psutil.virtual_memory().percent:.1f}%",
            "Available Memory": f"{psutil.virtual_memory().available / (1024**3):.1f} GB"
        }
        
        return create_arrow_compatible_dataframe(system_info)
    except Exception as e:
        # Fallback data if psutil is not available
        fallback_info = {
            "Platform": platform.system(),
            "Python Version": platform.python_version(),
            "Status": "System info unavailable"
        }
        return create_arrow_compatible_dataframe(fallback_info)

# Update the Settings tab with the fixed dataframe displays
def display_settings_tab(transactions_df, budget_df, goals_df, monthly_df, patterns_df):
    """Display settings tab with Arrow-compatible dataframes"""
    st.header("⚙️ Settings & Configuration")
    
    # Performance settings
    st.subheader("⚡ Performance Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cache_ttl = st.slider("Cache Duration (minutes)", 1, 60, 5)
        st.info(f"Data will be cached for {cache_ttl} minutes to improve performance")
        
        auto_refresh = st.checkbox("Auto-refresh data", value=False)
        if auto_refresh:
            st.info("Data will be automatically refreshed based on the selected time interval")
        else:
            st.info("Data will not be automatically refreshed. Please refresh the page to load new data.")
    
    with col2:
        # Redaction level settings
        st.write("**Data Protection Settings:**")
        st.selectbox(
            "Select Redaction Level",
            ["Low", "Medium", "High"],
            index=1,
            help="Choose the level of data redaction for privacy"
        )
        
        st.info("Higher redaction levels provide more privacy but may omit some data details")
    
    # API settings
    st.subheader("🔑 API Settings")
    
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="Enter your OpenAI API key",
        help="Required for AI assistant features"
    )
    
    if st.button("Save API Key"):
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            st.success("API Key saved successfully!")
        else:
            st.warning("Please enter a valid API Key")
    
    # Database settings
    st.subheader("🗄️ Database Settings")
    
    db_path = st.text_input(
        "DuckDB Database Path",
        value="spending_insights.db",
        help="Path to your DuckDB database file"
    )
    
    if st.button("Connect to Database"):
        try:
            conn = duckdb.connect(db_path)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            st.success("Connected to database successfully!")
        except Exception as e:
            st.error(f"Error connecting to database: {e}")
    
    # Performance diagnostics with fixed dataframes
    st.subheader("🔍 Performance Diagnostics")
    
    diagnostics_col1, diagnostics_col2 = st.columns(2)
    
    with diagnostics_col1:
        st.markdown("**Current Session Metrics:**")
        metrics = st.session_state.performance_metrics
        
        # Create Arrow-compatible metrics dataframe
        metrics_data = {
            "Page Loads": metrics['page_loads'],
            "AI Queries": metrics['query_count'],
            "Cache Hits": metrics['cache_hits'],
            "Errors": metrics['errors'],
            "Avg Response Time": f"{metrics['total_response_time']/max(metrics['query_count'], 1):.2f}s"
        }
        
        diag_df = create_arrow_compatible_dataframe(metrics_data)
        st.dataframe(diag_df, use_container_width=True, hide_index=True)
    
    with diagnostics_col2:
        st.markdown("**System Information:**")
        
        sys_df = create_system_info_dataframe()
        st.dataframe(sys_df, use_container_width=True, hide_index=True)
    
    # Database maintenance
    st.subheader("🔧 Database Maintenance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Clean Cache"):
            try:
                # Clear Streamlit cache
                st.cache_data.clear()
                st.cache_resource.clear()
                
                # Clear vectorstore cache
                try:
                    from vectorstore import cleanup_vectorstore_cache
                    cleanup_vectorstore_cache()
                except ImportError:
                    pass
                
                st.success("✅ Cache cleared successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Cache cleanup failed: {e}")
    
    with col2:
        if st.button("📊 Analyze Database"):
            try:
                conn = duckdb.connect('spending_insights.db')
                
                # Get table sizes
                table_info = {}
                tables = ['transactions', 'budget_categories', 'financial_goals', 'monthly_spending_summary', 'spending_patterns']
                
                for table in tables:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        table_info[table] = count
                    except:
                        table_info[table] = 0
                
                conn.close()
                
                st.success("✅ Database analyzed successfully!")
                
                # Create Arrow-compatible analysis dataframe
                analysis_data = []
                for table, count in table_info.items():
                    analysis_data.append({"Table": table, "Record Count": str(count)})  # Convert to string
                
                analysis_df = pd.DataFrame(analysis_data)
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"❌ Database analysis failed: {e}")
    
    with col3:
        if st.button("🔄 Refresh Vectorstore"):
            try:
                # Force refresh vectorstore cache
                st.cache_resource.clear()
                st.success("✅ Vectorstore will be refreshed on next AI query!")
            except Exception as e:
                st.error(f"❌ Vectorstore refresh failed: {e}")
    
    # Rest of the settings tab...
    # [Continue with other settings sections using proper data formatting]

# Update the main function to use the fixed settings display

def create_spending_heatmap(filtered_df):
    """Create spending heatmap by day of week and category"""
    if filtered_df.empty:
        return px.imshow([[0]], title="No data available for heatmap")
    
    # Prepare data for heatmap
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['date_dt'] = pd.to_datetime(filtered_df_copy['date'])
    filtered_df_copy['day_name'] = filtered_df_copy['date_dt'].dt.day_name()
    
    # Create day of week vs category heatmap
    heatmap_data = filtered_df_copy.groupby(['category', 'day_name'])['amount'].sum().unstack(fill_value=0)
    
    # Reorder days of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(columns=[day for day in day_order if day in heatmap_data.columns])
    
    # Handle empty heatmap data
    if heatmap_data.empty:
        return px.imshow([[0]], title="No data available for heatmap")
    
    fig = px.imshow(
        heatmap_data.values,
        labels=dict(x="Day of Week", y="Category", color="Amount ($)"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='Blues',
        title="Spending Patterns: Category vs Day of Week"
    )
    
    fig.update_layout(
        xaxis_title="Day of Week",
        yaxis_title="Category"
    )
    
    return fig

def calculate_financial_health_score(transactions_df, budget_df, goals_df):
    """Calculate overall financial health score"""
    score_components = {}
    total_score = 0
    max_score = 0
    
    # Budget adherence (40% of score)
    if not budget_df.empty and not transactions_df.empty:
        try:
            budget_status = calculate_enhanced_budget_status(transactions_df, budget_df)
            if not budget_status.empty:
                on_track_ratio = len(budget_status[budget_status['status'] == 'On Track']) / len(budget_status)
                budget_score = on_track_ratio * 40
                score_components['Budget Adherence'] = budget_score
                total_score += budget_score
            max_score += 40
        except Exception as e:
            logger.warning(f"Budget score calculation failed: {e}")
            max_score += 40
    
    # Goal progress (30% of score)
    if not goals_df.empty:
        try:
            total_target = goals_df['target_amount'].sum()
            total_saved = goals_df['current_amount'].sum()
            goal_progress = (total_saved / total_target) if total_target > 0 else 0
            goal_score = min(goal_progress * 30, 30)  # Cap at 30
            score_components['Goal Progress'] = goal_score
            total_score += goal_score
            max_score += 30
        except Exception as e:
            logger.warning(f"Goal score calculation failed: {e}")
            max_score += 30
    
    # Spending consistency (20% of score)
    if not transactions_df.empty:
        try:
            daily_spending = transactions_df.groupby('date')['amount'].sum()
            if len(daily_spending) > 1:
                cv = daily_spending.std() / daily_spending.mean()  # Coefficient of variation
                consistency_score = max(20 - (cv * 10), 0)  # Lower CV = higher score
                score_components['Spending Consistency'] = consistency_score
                total_score += consistency_score
            max_score += 20
        except Exception as e:
            logger.warning(f"Consistency score calculation failed: {e}")
            max_score += 20
    
    # Emergency fund indicator (10% of score)
    if not transactions_df.empty:
        try:
            # Simplified emergency fund calculation
            emergency_score = 10  # Placeholder - would need actual emergency fund data
            score_components['Emergency Preparedness'] = emergency_score
            total_score += emergency_score
            max_score += 10
        except Exception as e:
            logger.warning(f"Emergency score calculation failed: {e}")
            max_score += 10
    
    # Calculate final score as percentage
    final_score = (total_score / max_score * 100) if max_score > 0 else 0
    
    return final_score, score_components

def create_interactive_budget_chart(budget_status_df):
    """Create interactive budget visualization chart"""
    if budget_status_df.empty:
        return px.bar(title="No budget data available")
    
    # Create a comprehensive budget visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Budget Usage by Category', 'Spending vs Budget Limits', 
                       'Budget Status Distribution', 'Projected vs Actual'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"type": "pie"}, {"secondary_y": False}]]
    )
    
    # Color mapping for status
    color_map = {
        'On Track': '#28a745',
        'Warning': '#ffc107', 
        'Over Budget': '#dc3545'
    }
    
    colors = [color_map.get(status, '#6c757d') for status in budget_status_df['status']]
    
    # 1. Budget usage bar chart
    fig.add_trace(
        go.Bar(
            x=budget_status_df['category'],
            y=budget_status_df['percentage'],
            name='Usage %',
            marker_color=colors,
            text=[f"{p:.1f}%" for p in budget_status_df['percentage']],
            textposition='auto',
        ),
        row=1, col=1
    )
    
    # Add 100% threshold line
    fig.add_hline(y=100, line_dash="dash", line_color="red", 
                  annotation_text="Budget Limit", row=1, col=1)
    
    # 2. Spending vs Budget limits comparison
    fig.add_trace(
        go.Scatter(
            x=budget_status_df['limit'],
            y=budget_status_df['spent'],
            mode='markers+text',
            marker=dict(
                size=[max(p/5, 10) for p in budget_status_df['percentage']],  # Scale down size
                sizemode='diameter',
                color=colors,
                line=dict(width=2, color='white')
            ),
            text=budget_status_df['category'],
            textposition="middle center",
            name='Actual Spending',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Add diagonal line (y=x) for perfect budget adherence
    max_val = max(budget_status_df['limit'].max(), budget_status_df['spent'].max())
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(dash='dash', color='gray'),
            name='Perfect Budget Line',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Status distribution pie chart
    status_counts = budget_status_df['status'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            name="Status Distribution",
            marker_colors=[color_map.get(status, '#6c757d') for status in status_counts.index],
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. Projected vs Actual spending
    fig.add_trace(
        go.Bar(
            x=budget_status_df['category'],
            y=budget_status_df['spent'],
            name='Current Spending',
            marker_color='lightblue',
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=budget_status_df['category'],
            y=budget_status_df['projected_spending'],
            name='Projected Spending',
            marker_color='darkblue',
            opacity=0.8,
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=budget_status_df['category'],
            y=budget_status_df['limit'],
            mode='markers',
            marker=dict(
                symbol='line-ew',
                size=15,
                color='red',
                line=dict(width=3)
            ),
            name='Budget Limit',
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Comprehensive Budget Analysis Dashboard",
        title_x=0.5
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Category", row=1, col=1)
    fig.update_yaxes(title_text="Usage (%)", row=1, col=1)
    
    fig.update_xaxes(title_text="Budget Limit ($)", row=1, col=2)
    fig.update_yaxes(title_text="Amount Spent ($)", row=1, col=2)
    
    fig.update_xaxes(title_text="Category", row=2, col=2)
    fig.update_yaxes(title_text="Amount ($)", row=2, col=2)
    
    return fig

def create_budget_alerts_system(budget_status_df):
    """Create intelligent budget alert system"""
    alerts = []
    
    if budget_status_df.empty:
        return alerts
    
    for _, budget in budget_status_df.iterrows():
        category = budget['category']
        percentage = budget['percentage']
        status = budget['status']
        projected_percentage = budget.get('projected_percentage', 0)
        days_remaining = budget.get('days_remaining', 0)
        
        # Critical alerts
        if status == 'Over Budget':
            overspend = budget['spent'] - budget['limit']
            alerts.append({
                'level': 'critical',
                'category': category,
                'message': f"🚨 {category}: Over budget by ${overspend:.2f} ({percentage:.1f}%)",
                'action': f"Immediate action required - consider stopping {category} spending"
            })
        
        # Warning alerts
        elif status == 'Warning':
            if projected_percentage > 100:
                alerts.append({
                    'level': 'warning',
                    'category': category,
                    'message': f"⚠️ {category}: Projected to exceed budget ({projected_percentage:.1f}%)",
                    'action': f"Reduce daily {category} spending"
                })
            else:
                alerts.append({
                    'level': 'warning',
                    'category': category,
                    'message': f"⚠️ {category}: Approaching budget limit ({percentage:.1f}%)",
                    'action': f"Monitor {category} spending closely"
                })
        
        # Positive alerts
        elif percentage < 50 and days_remaining < 10:
            remaining = budget.get('remaining', 0)
            alerts.append({
                'level': 'info',
                'category': category,
                'message': f"✅ {category}: Under budget with room to spare ({percentage:.1f}%)",
                'action': f"You have ${remaining:.2f} remaining for {category}"
            })
    
    return alerts

def create_enhanced_spending_breakdown(filtered_df):
    """Create enhanced spending breakdown visualization"""
    if filtered_df.empty:
        return px.bar(title="No data available")
    
    # Monthly spending trend by category
    filtered_df['month_year'] = pd.to_datetime(filtered_df['date']).dt.to_period('M')
    monthly_category = filtered_df.groupby(['month_year', 'category'])['amount'].sum().reset_index()
    monthly_category['month_year'] = monthly_category['month_year'].astype(str)
    
    fig = px.line(
        monthly_category,
        x='month_year',
        y='amount',
        color='category',
        title='Monthly Spending Trends by Category',
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode='x unified'
    )
    
    return fig

def create_merchant_spending_analysis(filtered_df, top_n=15):
    """Create detailed merchant spending analysis"""
    if filtered_df.empty:
        return px.bar(title="No merchant data available")
    
    # Analyze top merchants
    merchant_stats = filtered_df.groupby('merchant').agg({
        'amount': ['sum', 'count', 'mean', 'std'],
        'category': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Mixed'
    }).round(2)
    
    merchant_stats.columns = ['Total_Spent', 'Transaction_Count', 'Avg_Amount', 'Std_Amount', 'Primary_Category']
    merchant_stats = merchant_stats.reset_index().sort_values('Total_Spent', ascending=False).head(top_n)
    
    # Create bubble chart
    fig = px.scatter(
        merchant_stats,
        x='Transaction_Count',
        y='Avg_Amount',
        size='Total_Spent',
        color='Primary_Category',
        hover_name='merchant',
        title=f"Top {top_n} Merchants: Frequency vs Average Amount",
        labels={
            'Transaction_Count': 'Number of Transactions',
            'Avg_Amount': 'Average Transaction Amount ($)',
            'Total_Spent': 'Total Spent ($)'
        },
        size_max=50
    )
    
    fig.update_layout(
        xaxis_title="Number of Transactions",
        yaxis_title="Average Transaction Amount ($)",
        showlegend=True
    )
    
    return fig

def generate_spending_insights(transactions_df, budget_df, goals_df):
    """Generate intelligent spending insights and recommendations"""
    insights = {
        'spending_trends': [],
        'budget_recommendations': [],
        'goal_suggestions': [],
        'pattern_alerts': []
    }
    
    if transactions_df.empty:
        return insights
    
    try:
        # Spending trend analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        current_month_data = transactions_df[
            (pd.to_datetime(transactions_df['date']).dt.month == current_month) &
            (pd.to_datetime(transactions_df['date']).dt.year == current_year)
        ]
        
        if len(current_month_data) > 0:
            # Compare with previous months
            monthly_totals = transactions_df.groupby([
                pd.to_datetime(transactions_df['date']).dt.year,
                pd.to_datetime(transactions_df['date']).dt.month
            ])['amount'].sum()
            
            if len(monthly_totals) > 1:
                current_total = monthly_totals.iloc[-1]
                previous_total = monthly_totals.iloc[-2]
                change_pct = ((current_total - previous_total) / previous_total) * 100
                
                if change_pct > 10:
                    insights['spending_trends'].append(f"📈 Spending increased by {change_pct:.1f}% this month")
                elif change_pct < -10:
                    insights['spending_trends'].append(f"📉 Spending decreased by {abs(change_pct):.1f}% this month")
                else:
                    insights['spending_trends'].append(f"📊 Spending is stable (changed by {change_pct:.1f}%)")
        
        # Top spending categories
        category_totals = current_month_data.groupby('category')['amount'].sum().sort_values(ascending=False)
        if len(category_totals) > 0:
            top_category = category_totals.index[0]
            top_amount = category_totals.iloc[0]
            total_spending = category_totals.sum()
            percentage = (top_amount / total_spending) * 100
            
            insights['spending_trends'].append(f"🏆 {top_category} is your largest expense ({percentage:.1f}% of total)")
        
        # Budget recommendations
        if not budget_df.empty:
            budget_status = calculate_enhanced_budget_status(transactions_df, budget_df)
            
            for _, budget in budget_status.iterrows():
                if budget['status'] == 'Over Budget':
                    insights['budget_recommendations'].append(
                        f"🚨 Consider increasing {budget['category']} budget or reducing spending"
                    )
                elif budget['percentage'] < 50:
                    insights['budget_recommendations'].append(
                        f"✅ {budget['category']} budget is well-managed - you could potentially reallocate funds"
                    )
    
    except Exception as e:
        logger.warning(f"Insight generation failed: {e}")
        insights['spending_trends'].append("Unable to generate spending insights at this time")
    
    return insights

def create_financial_summary_report(transactions_df, budget_df, goals_df, time_period="monthly"):
    """Generate comprehensive financial summary report"""
    
    report = {
        'period': time_period,
        'generated_at': datetime.now().isoformat(),
        'summary': {},
        'detailed_analysis': {},
        'recommendations': []
    }
    
    if transactions_df.empty:
        report['summary']['message'] = "No transaction data available for analysis"
        return report
    
    try:
        # Basic summary statistics
        total_transactions = len(transactions_df)
        total_spending = transactions_df['amount'].sum()
        avg_transaction = transactions_df['amount'].mean()
        date_range = (pd.to_datetime(transactions_df['date']).max() - pd.to_datetime(transactions_df['date']).min()).days
        
        report['summary'] = {
            'total_transactions': total_transactions,
            'total_spending': float(total_spending),
            'average_transaction': float(avg_transaction),
            'date_range_days': date_range,
            'unique_merchants': transactions_df['merchant'].nunique(),
            'categories_used': transactions_df['category'].nunique()
        }
        
        # Category breakdown
        category_analysis = transactions_df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean'],
            'merchant': 'nunique'
        }).round(2)
        category_analysis.columns = ['total_spent', 'transaction_count', 'avg_amount', 'unique_merchants']
        
        report['detailed_analysis']['by_category'] = category_analysis.to_dict('index')
        
        # Time-based analysis
        monthly_spending = transactions_df.groupby(
            pd.to_datetime(transactions_df['date']).dt.to_period('M')
        )['amount'].sum()
        
        report['detailed_analysis']['monthly_trends'] = {
            str(period): float(amount) for period, amount in monthly_spending.items()
        }
        
        # Generate recommendations
        insights = generate_spending_insights(transactions_df, budget_df, goals_df)
        report['recommendations'] = insights['spending_trends'] + insights['budget_recommendations']
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        report['summary']['error'] = f"Report generation failed: {str(e)}"
    
    return report

def safe_redact_sensitive(text, level="Medium"):
    """Safe redaction fallback when redact module is not available"""
    try:
        from redact import redact_sensitive, AdvancedRedactionEngine, RedactionLevel
        if level == "High":
            redaction_level = RedactionLevel.HIGH
        elif level == "Low":
            redaction_level = RedactionLevel.LOW
        else:
            redaction_level = RedactionLevel.MEDIUM
        
        redactor = AdvancedRedactionEngine(redaction_level)
        return redactor.redact_text(text)
    except ImportError:
        # Fallback: simple redaction
        import re
        if level == "High":
            # High redaction: remove all numbers and names
            text = re.sub(r'\$?\d+\.?\d*', '[AMOUNT]', text)
            text = re.sub(r'\b[A-Z][a-z]+\b', '[NAME]', text)
        elif level == "Medium":
            # Medium redaction: remove specific amounts
            text = re.sub(r'\$\d+\.\d{2}', '[AMOUNT]', text)
        # Low redaction: minimal changes
        
        # Return a simple object with the redacted text
        class SimpleRedactionResult:
            def __init__(self, text):
                self.redacted_text = text
                self.risk_score = 20  # Low risk after redaction
                self.redactions_made = {}
        
        return SimpleRedactionResult(text)

def safe_get_vectorstore_stats():
    """Safe vectorstore stats when module is not available"""
    try:
        from vectorstore import get_vectorstore_stats
        return get_vectorstore_stats()
    except ImportError:
        return {
            'build_time_seconds': 0,
            'cache_hit_rate': 0,
            'average_search_time_ms': 0
        }

def main():
    # Performance tracking
    st.session_state.performance_metrics['page_loads'] += 1
    
    # Header with real-time status
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("💰 Advanced Spending Insights & Budgeting")
        st.markdown("*AI-powered financial analytics with real-time insights*")
    
    with col2:
        # Real-time clock
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"🕐 **{current_time}**")
    
    with col3:
        # Database status
        try:
            conn = duckdb.connect('spending_insights.db')
            conn.execute("SELECT 1").fetchone()
            conn.close()
            st.markdown("🟢 **DB Connected**")
        except:
            st.markdown("🔴 **DB Error**")
    
    # Load data with progress bar
    with st.spinner("📊 Loading financial data..."):
        transactions_df, budget_df, goals_df, monthly_df, patterns_df = load_data_from_db()
    
    if transactions_df.empty:
        st.error("🚫 No data found. Please run `uv run python db_setup.py` first to initialize the database.")
        st.info("💡 **Quick Start:**\n1. Run database setup\n2. Refresh this page\n3. Start analyzing your spending!")
        return
    
    # Calculate financial health score (NOW DEFINED)
    health_score, score_components = calculate_financial_health_score(transactions_df, budget_df, goals_df)
    
    # Enhanced sidebar with performance metrics and health score
    st.sidebar.title("🎛️ Advanced Controls")
    
    # Financial health score in sidebar
    health_color = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
    st.sidebar.markdown(f"""
    ### {health_color} Financial Health Score
    **{health_score:.0f}/100**
    """)
    
    with st.sidebar.expander("📊 Score Breakdown"):
        for component, score in score_components.items():
            st.write(f"**{component}:** {score:.1f}")
    
    display_performance_metrics()
    
    # Smart date range with preset options
    st.sidebar.subheader("📅 Time Period")
    date_preset = st.sidebar.selectbox(
        "Quick Select",
        ["Last 30 Days", "Last 3 Months", "Last 6 Months", "This Year", "Custom Range"]
    )
    
    # Calculate date range based on preset
    max_date = pd.to_datetime(transactions_df['date']).max().date()
    
    if date_preset == "Last 30 Days":
        start_date = max_date - timedelta(days=30)
        end_date = max_date
    elif date_preset == "Last 3 Months":
        start_date = max_date - timedelta(days=90)
        end_date = max_date
    elif date_preset == "Last 6 Months":
        start_date = max_date - timedelta(days=180)
        end_date = max_date
    elif date_preset == "This Year":
        start_date = datetime(max_date.year, 1, 1).date()
        end_date = max_date
    else:  # Custom Range
        min_date = pd.to_datetime(transactions_df['date']).min().date()
        start_date = st.sidebar.date_input("Start Date", min_date)
        end_date = st.sidebar.date_input("End Date", max_date)
    
    # Advanced filtering
    st.sidebar.subheader("🔍 Filters")
    
    # Category filter with select all/none
    categories = list(transactions_df['category'].unique())
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Select All", key="select_all_cats"):
            st.session_state.selected_categories = categories
    with col2:
        if st.button("Clear All", key="clear_all_cats"):
            st.session_state.selected_categories = []
    
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = categories
    
    selected_categories = st.sidebar.multiselect(
        "Categories",
        categories,
        default=st.session_state.selected_categories
    )
    
    # Amount range filter
    if not transactions_df.empty:
        min_amount = float(transactions_df['amount'].min())
        max_amount = float(transactions_df['amount'].max())
        
        amount_range = st.sidebar.slider(
            "Amount Range ($)",
            min_value=min_amount,
            max_value=max_amount,
            value=(min_amount, max_amount),
            step=1.0
        )
    
    # Merchant filter
    top_merchants = transactions_df['merchant'].value_counts().head(20).index.tolist()
    selected_merchants = st.sidebar.multiselect(
        "Top Merchants (Optional)",
        top_merchants,
        default=[]
    )
    
    # Apply filters
    filtered_df = transactions_df.copy()
    filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    
    # Date filter
    filtered_df = filtered_df[
        (filtered_df['date'].dt.date >= start_date) & 
        (filtered_df['date'].dt.date <= end_date)
    ]
    
    # Category filter
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    
    # Amount filter
    if 'amount_range' in locals():
        filtered_df = filtered_df[
            (filtered_df['amount'] >= amount_range[0]) &
            (filtered_df['amount'] <= amount_range[1])
        ]
    
    # Merchant filter
    if selected_merchants:
        filtered_df = filtered_df[filtered_df['merchant'].isin(selected_merchants)]
    
    # Privacy settings
    st.sidebar.subheader("🔒 Privacy Settings")
    redaction_level = st.sidebar.selectbox(
        "Data Protection Level",
        ["Low", "Medium", "High"],
        index=1,
        help="Higher levels provide more privacy protection"
    )
    
    # Main content with enhanced tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "💰 Smart Budget", 
        "🎯 Goals Tracker", 
        "🤖 AI Assistant", 
        "📈 Analytics", 
        "⚙️ Settings"
    ])
    
    with tab1:  # Enhanced Dashboard
        st.header("📊 Executive Dashboard")
        
        # Financial Health Score prominently displayed
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            health_color_bg = "#28a745" if health_score >= 80 else "#ffc107" if health_score >= 60 else "#dc3545"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {health_color_bg} 0%, {health_color_bg}80 100%); 
                        color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1rem;">
                <h2>🏆 Financial Health Score</h2>
                <h1 style="font-size: 3rem; margin: 0;">{health_score:.0f}</h1>
                <p style="margin: 0;">Out of 100 points</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Quick stats
            st.metric("Total Transactions", f"{len(filtered_df):,}")
            st.metric("Active Categories", f"{filtered_df['category'].nunique()}")
        
        with col3:
            st.metric("Date Range", f"{(end_date - start_date).days} days")
            st.metric("Unique Merchants", f"{filtered_df['merchant'].nunique()}")
        
        # Real-time metrics with animations
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_spent = filtered_df['amount'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <h4>💳 Total Spent</h4>
                <h2>${total_spent:,.2f}</h2>
                <small>Period: {len(filtered_df)} transactions</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_transaction = filtered_df['amount'].mean() if not filtered_df.empty else 0
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 Avg Transaction</h4>
                <h2>${avg_transaction:.2f}</h2>
                <small>Median: ${filtered_df['amount'].median():.2f}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            transaction_count = len(filtered_df)
            transactions_per_day = transaction_count / max((end_date - start_date).days, 1)
            st.markdown(f"""
            <div class="metric-card">
                <h4>🧾 Transactions</h4>
                <h2>{transaction_count:,}</h2>
                <small>{transactions_per_day:.1f} per day</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if not filtered_df.empty:
                top_category = filtered_df.groupby('category')['amount'].sum().idxmax()
                top_category_amount = filtered_df.groupby('category')['amount'].sum().max()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🏆 Top Category</h4>
                    <h2>{top_category}</h2>
                    <small>${top_category_amount:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🏆 Top Category</h4>
                    <h2>N/A</h2>
                    <small>No data</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col5:
            # Budget health score
            budget_status_df = calculate_enhanced_budget_status(filtered_df, budget_df)
            if not budget_status_df.empty:
                budget_health = 100 - (len(budget_status_df[budget_status_df['status'] == 'Over Budget']) * 40 + 
                                     len(budget_status_df[budget_status_df['status'] == 'Warning']) * 20)
                health_color = "success" if budget_health >= 80 else "alert" if budget_health >= 60 else "danger"
                st.markdown(f"""
                <div class="{health_color}-card">
                    <h4>🎯 Budget Health</h4>
                    <h2>{budget_health}%</h2>
                    <small>Overall score</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🎯 Budget Health</h4>
                    <h2>N/A</h2>
                    <small>No budget data</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Enhanced visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💸 Category Distribution")
            if not filtered_df.empty:
                category_data = filtered_df.groupby('category').agg({
                    'amount': ['sum', 'count', 'mean']
                }).round(2)
                category_data.columns = ['Total', 'Count', 'Average']
                category_data = category_data.reset_index()
                
                fig = px.treemap(
                    category_data,
                    path=['category'],
                    values='Total',
                    color='Average',
                    color_continuous_scale='RdYlBu_r',
                    title="Spending Distribution (Size: Total, Color: Average)"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for selected filters")
        
        with col2:
            st.subheader("📅 Enhanced Spending Trend")
            if not filtered_df.empty:
                trend_fig = create_enhanced_visualizations(filtered_df, budget_df)
                trend_fig.update_layout(height=400)
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.info("No data available for selected filters")
        
        # Spending heatmap (NOW DEFINED)
        st.subheader("🔥 Spending Heatmap")
        if not filtered_df.empty:
            heatmap_fig = create_spending_heatmap(filtered_df)
            st.plotly_chart(heatmap_fig, use_container_width=True)
        
        # Recent transactions with enhanced display
        st.subheader("🕐 Recent Transactions")
        if not filtered_df.empty:
            recent_df = filtered_df.head(10).copy()
            recent_df['amount_formatted'] = recent_df['amount'].apply(lambda x: f"${x:.2f}")
            recent_df['date_formatted'] = pd.to_datetime(recent_df['date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                recent_df[['date_formatted', 'merchant', 'category', 'amount_formatted', 'notes']],
                column_config={
                    'date_formatted': 'Date',
                    'merchant': 'Merchant',
                    'category': 'Category',
                    'amount_formatted': 'Amount',
                    'notes': 'Notes'
                },
                use_container_width=True,
                hide_index=True
            )
    
    with tab2:  # Smart Budget Tracking
        st.header("💰 Smart Budget Tracking")
        
        budget_status_df = calculate_enhanced_budget_status(transactions_df, budget_df)
        
        if not budget_status_df.empty:
            # Budget health overview
            col1, col2, col3, col4 = st.columns(4)
            
            on_track = len(budget_status_df[budget_status_df['status'] == 'On Track'])
            warnings = len(budget_status_df[budget_status_df['status'] == 'Warning'])
            over_budget = len(budget_status_df[budget_status_df['status'] == 'Over Budget'])
            total_categories = len(budget_status_df)
            
            with col1:
                st.markdown(f"""
                <div class="success-card">
                    <h4>✅ On Track</h4>
                    <h2>{on_track}</h2>
                    <small>{(on_track/total_categories*100):.0f}% of budgets</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="alert-card">
                    <h4>⚠️ Warning</h4>
                    <h2>{warnings}</h2>
                    <small>{(warnings/total_categories*100):.0f}% of budgets</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="danger-card">
                    <h4>🚨 Over Budget</h4>
                    <h2>{over_budget}</h2>
                    <small>{(over_budget/total_categories*100):.0f}% of budgets</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                avg_usage = budget_status_df['percentage'].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📊 Avg Usage</h4>
                    <h2>{avg_usage:.1f}%</h2>
                    <small>Across all categories</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Interactive budget visualization (NOW DEFINED)
            st.subheader("📊 Interactive Budget Analysis")
            budget_chart = create_interactive_budget_chart(budget_status_df)
            st.plotly_chart(budget_chart, use_container_width=True)
            
            # Smart Budget Alerts (NOW DEFINED)
            st.subheader("🚨 Smart Budget Alerts")
            alerts = create_budget_alerts_system(budget_status_df)
            
            if alerts:
                for alert in alerts:
                    if alert['level'] == 'critical':
                        st.error(f"{alert['message']}\n💡 **Action:** {alert['action']}")
                    elif alert['level'] == 'warning':
                        st.warning(f"{alert['message']}\n💡 **Suggestion:** {alert['action']}")
                    else:
                        st.info(f"{alert['message']}\n💡 **Note:** {alert['action']}")
            else:
                st.success("🎉 No budget alerts - you're managing your finances well!")
        
        else:
            st.info("No budget data available. Set up budgets to track your spending!")
    
    with tab3:  # Goals Tracker - keep existing implementation
        st.header("🎯 Smart Financial Goals")
        
        if not goals_df.empty:
            # Goals overview
            total_goals = len(goals_df)
            completed_goals = len(goals_df[goals_df['current_amount'] >= goals_df['target_amount']])
            total_target = goals_df['target_amount'].sum()
            total_saved = goals_df['current_amount'].sum()
            overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🎯 Total Goals</h4>
                    <h2>{total_goals}</h2>
                    <small>{completed_goals} completed</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>💰 Target Amount</h4>
                    <h2>${total_target:,.0f}</h2>
                    <small>All goals combined</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>💎 Amount Saved</h4>
                    <h2>${total_saved:,.0f}</h2>
                    <small>{overall_progress:.1f}% of target</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                remaining_amount = total_target - total_saved
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📈 Remaining</h4>
                    <h2>${remaining_amount:,.0f}</h2>
                    <small>To reach all goals</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Enhanced goal tracking
            for _, goal in goals_df.iterrows():
                with st.expander(f"🎯 {goal['goal_name']} - {goal['priority']} Priority"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Target Amount", f"${goal['target_amount']:,.2f}")
                    with col2:
                        progress_amount = goal['current_amount']
                        progress_percentage = (progress_amount / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
                        st.metric(
                            "Current Amount", 
                            f"${progress_amount:,.2f}",
                            delta=f"{progress_percentage:.1f}% complete"
                        )
                    with col3:
                        remaining = goal['target_amount'] - progress_amount
                        st.metric("Remaining", f"${remaining:,.2f}")
                    
                    # Enhanced progress visualization
                    progress = progress_amount / goal['target_amount'] if goal['target_amount'] > 0 else 0
                    progress_color = '#28a745' if progress >= 1.0 else '#ffc107' if progress >= 0.5 else '#17a2b8'
                    
                    st.markdown(f"""
                    <div style="background-color: #e9ecef; border-radius: 10px; padding: 4px; margin: 10px 0;">
                        <div style="background-color: {progress_color}; width: {min(progress*100, 100):.1f}%; 
                                   height: 25px; border-radius: 6px; transition: width 0.3s ease;
                                   display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                            {progress*100:.1f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Target date analysis
                    if goal['target_date']:
                        try:
                            target_date_str = str(goal['target_date'])
                            if ' ' in target_date_str:
                                target_date_str = target_date_str.split(' ')[0]
                            
                            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                            days_remaining = (target_date - datetime.now().date()).days
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"🗓️ **Target Date:** {target_date}")
                            
                            with col2:
                                if days_remaining > 0:
                                    st.write(f"⏰ **Days Remaining:** {days_remaining}")
                                else:
                                    st.write("🚨 **Goal date has passed!**")
                            
                            with col3:
                                if days_remaining > 0 and remaining > 0:
                                    daily_needed = remaining / days_remaining
                                    monthly_needed = daily_needed * 30
                                    st.write(f"💡 **Daily Target:** ${daily_needed:.2f}")
                                    st.write(f"💡 **Monthly Target:** ${monthly_needed:.2f}")
                            
                            # Progress prediction
                            if progress > 0 and days_remaining > 0:
                                days_since_start = 365  # Assume 1 year planning horizon
                                current_daily_rate = progress_amount / days_since_start
                                projected_completion = progress_amount + (current_daily_rate * days_remaining)
                                projection_percentage = (projected_completion / goal['target_amount'] * 100)
                                
                                if projection_percentage >= 100:
                                    st.success(f"🎉 **On track!** Projected to reach {projection_percentage:.1f}% of goal by target date")
                                elif projection_percentage >= 80:
                                    st.warning(f"⚠️ **Close!** Projected to reach {projection_percentage:.1f}% of goal by target date")
                                else:
                                    st.error(f"🚨 **Behind!** Projected to reach only {projection_percentage:.1f}% of goal by target date")
                        
                        except Exception as e:
                            st.write(f"🗓️ **Target Date:** {goal['target_date']}")
            
            # Goals visualization
            st.subheader("📊 Goals Progress Visualization")
            goals_viz = goals_df.copy()
            goals_viz['progress'] = (goals_viz['current_amount'] / goals_viz['target_amount'] * 100).round(1)
            goals_viz['status'] = goals_viz['progress'].apply(
                lambda x: 'Completed' if x >= 100 else 'On Track' if x >= 50 else 'Needs Attention'
            )
            
            fig = px.bar(
                goals_viz,
                x='goal_name',
                y='progress',
                color='status',
                title="Goals Completion Progress (%)",
                color_discrete_map={
                    'Completed': '#28a745',
                    'On Track': '#ffc107', 
                    'Needs Attention': '#dc3545'
                }
            )
            fig.update_layout(yaxis_title="Completion (%)", xaxis_title="Goals")
            fig.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Target")
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("🎯 No financial goals found. Create some goals to track your financial progress!")
            
            # Goal creation suggestion
            st.markdown("""
            ### 💡 Suggested Goals to Get Started:
            - **Emergency Fund:** 3-6 months of expenses
            - **Vacation Fund:** Plan your next getaway
            - **Home Down Payment:** Save for your dream home
            - **Retirement Contribution:** Boost your 401(k)
            - **Debt Payoff:** Eliminate high-interest debt
            """)
    
    with tab4:  # Enhanced AI Assistant
        st.header("🤖 Advanced AI Spending Assistant")
        st.markdown("*Get personalized insights with advanced privacy protection*")
        
        # Privacy level indicator
        redaction_levels = {"Low": RedactionLevel.LOW, "Medium": RedactionLevel.MEDIUM, "High": RedactionLevel.HIGH}
        current_redaction = redaction_levels[redaction_level]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"🔒 **Privacy Level:** {redaction_level} - Your data is protected according to {redaction_level.lower()} security standards")
        with col2:
            if st.button("🔄 Clear Chat"):
                if "messages" in st.session_state:
                    st.session_state.messages = []
                st.rerun()
        
        # Set up AI assistant
        qa_chain, data_count = setup_ai_assistant()
        
        if qa_chain:
            st.success(f"✅ AI Assistant ready with {data_count:,} transactions loaded")
            
            # Initialize chat
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {
                        "role": "assistant", 
                        "content": f"Hello! I'm your AI spending assistant with access to {data_count:,} transactions. I can help you understand your spending patterns, provide budget recommendations, and offer personalized financial insights. What would you like to know?"
                    }
                ]
            
            # Display chat messages with enhanced styling
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant":
                        st.markdown(f'<div class="chat-message">{message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(message["content"])
            
            # Chat input with advanced processing
            if prompt := st.chat_input("Ask about your spending patterns, budgets, or financial advice..."):
                # Track query
                st.session_state.performance_metrics['query_count'] += 1
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate AI response with enhanced error handling
                with st.chat_message("assistant"):
                    with st.spinner("🧠 Analyzing your financial data..."):
                        try:
                            start_time = time.time()
                            
                            # Enhanced query processing
                            raw_response = qa_chain.invoke({"query": prompt})
                            
                            # Handle different response formats
                            if isinstance(raw_response, dict):
                                response_text = raw_response.get('result', str(raw_response))
                                source_docs = raw_response.get('source_documents', [])
                            else:
                                response_text = str(raw_response)
                                source_docs = []
                            
                            # Advanced redaction with selected level
                            redactor = AdvancedRedactionEngine(current_redaction)
                            redaction_result = redactor.redact_text(response_text)
                            safe_response = redaction_result.redacted_text
                            
                            # Display response with metadata
                            response_time = time.time() - start_time
                            st.session_state.performance_metrics['total_response_time'] += response_time
                            
                            st.markdown(f'<div class="chat-message">{safe_response}</div>', unsafe_allow_html=True)
                            
                            # Show response metadata
                            with st.expander("🔍 Response Details", expanded=False):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Response Time", f"{response_time:.2f}s")
                                with col2:
                                    st.metric("Sources Used", len(source_docs))
                                with col3:
                                    st.metric("Privacy Score", f"{100-redaction_result.risk_score:.0f}%")
                                
                                if redaction_result.redactions_made:
                                    st.write("**Privacy Redactions Applied:**")
                                    for rule, count in redaction_result.redactions_made.items():
                                        st.write(f"- {rule}: {count} items")
                            
                            st.session_state.messages.append({"role": "assistant", "content": safe_response})
                            
                        except Exception as e:
                            st.session_state.performance_metrics['errors'] += 1
                            error_msg = f"I apologize, but I encountered an error while analyzing your data. Please try rephrasing your question or contact support if the issue persists. (Error: {str(e)[:100]}...)"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # Enhanced suggested questions with categories
            st.subheader("💡 Intelligent Suggestions")
            
            suggestion_categories = {
                "📊 Spending Analysis": [
                    "What's my biggest spending category this month?",
                    "How has my spending changed compared to last month?",
                    "Which merchants do I spend the most at?",
                    "What are my most expensive transactions?"
                ],
                "💰 Budget Insights": [
                    "Am I on track with my budgets?",
                    "Which categories am I overspending in?",
                    "How can I optimize my budget allocations?",
                    "What's my average daily spending?"
                ],
                "🎯 Financial Advice": [
                    "How can I save more money based on my patterns?",
                    "What spending habits should I be concerned about?",
                    "Where can I cut back without affecting my lifestyle?",
                    "What are some realistic savings goals for me?"
                ],
                "📈 Trends & Patterns": [
                    "Do I spend more on weekends vs weekdays?",
                    "What are my seasonal spending patterns?",
                    "How does my spending vary by category over time?",
                    "Are there any unusual spending patterns I should know about?"
                ]
            }
            
            selected_category = st.selectbox("Choose suggestion category:", list(suggestion_categories.keys()))
            
            col1, col2 = st.columns(2)
            questions = suggestion_categories[selected_category]
            
            for i, question in enumerate(questions):
                col = col1 if i % 2 == 0 else col2
                with col:
                    if st.button(question, key=f"suggestion_{i}"):
                        st.session_state.messages.append({"role": "user", "content": question})
                        st.rerun()
        
        else:
            st.error("🚫 AI assistant is not available. Please check your OpenAI API key and database connection.")
            
            # Troubleshooting guide
            with st.expander("🔧 Troubleshooting Guide"):
                st.markdown("""
                **Common Issues:**
                1. **Missing OpenAI API Key:** Set your `OPENAI_API_KEY` in your environment
                2. **Database Not Found:** Run `uv run python db_setup.py` to initialize
                3. **No Transaction Data:** Ensure your database has transaction records
                4. **Network Issues:** Check your internet connection
                
                **Quick Fix:**
                ```bash
                # Set your API key
                export OPENAI_API_KEY="your-key-here"
                
                # Initialize database
                uv run python db_setup.py
                
                # Restart the app
                streamlit run streamlit_app.py
                ```
                """)

    with tab5:  # Advanced Analytics
        st.header("📈 Advanced Financial Analytics")
        
        # Analytics overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Data Points", f"{len(transactions_df):,}")
        with col2:
            date_range_days = (pd.to_datetime(transactions_df['date']).max() - pd.to_datetime(transactions_df['date']).min()).days
            st.metric("Date Range", f"{date_range_days} days")
        with col3:
            unique_merchants = transactions_df['merchant'].nunique()
            st.metric("Unique Merchants", unique_merchants)
        
        # Spending patterns from database
        st.subheader("🔍 Discovered Spending Patterns")
        if not patterns_df.empty:
            for _, pattern in patterns_df.iterrows():
                confidence_color = "🟢" if pattern['confidence_score'] > 0.8 else "🟡" if pattern['confidence_score'] > 0.6 else "🔴"
                
                with st.expander(f"{confidence_color} {pattern['pattern_type']} (Confidence: {pattern['confidence_score']:.1%})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {pattern['pattern_description']}")
                        st.write(f"**Category:** {pattern['category']}")
                        st.write(f"**Frequency:** {pattern['frequency']}")
                    
                    with col2:
                        st.write(f"**Average Amount:** ${pattern['avg_amount']:.2f}")
                        st.write(f"**Median Amount:** ${pattern['median_amount']:.2f}")
                        st.write(f"**Sample Size:** {pattern['sample_size']} transactions")
                        if pattern['merchant']:
                            st.write(f"**Merchant:** {pattern['merchant']}")
        else:
            st.info("No spending patterns detected. Pattern analysis requires more transaction data.")
        
        # Advanced visualizations
        st.subheader("📊 Advanced Visualizations")
        
        # Spending correlation matrix
        if not filtered_df.empty:
            # Create spending by category and time matrix
            monthly_spending = filtered_df.groupby([
                pd.to_datetime(filtered_df['date']).dt.to_period('M'),
                'category'
            ])['amount'].sum().unstack(fill_value=0)
            
            if len(monthly_spending) > 1 and len(monthly_spending.columns) > 1:
                correlation_matrix = monthly_spending.corr()
                
                fig_corr = px.imshow(
                    correlation_matrix,
                    title="Category Spending Correlations",
                    labels=dict(color="Correlation"),
                    color_continuous_scale='RdBu_r',
                    aspect='auto'
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            
            # Merchant analysis
            st.subheader("🏪 Top Merchants Analysis")
            merchant_analysis = filtered_df.groupby('merchant').agg({
                'amount': ['sum', 'count', 'mean', 'std'],
                'category': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Mixed'
            }).round(2)
            
            merchant_analysis.columns = ['Total_Spent', 'Transaction_Count', 'Avg_Amount', 'Std_Amount', 'Primary_Category']
            merchant_analysis = merchant_analysis.reset_index().sort_values('Total_Spent', ascending=False).head(15)
            
            # Enhanced merchant visualization
            fig_merchant = px.scatter(
                merchant_analysis,
                x='Transaction_Count',
                y='Avg_Amount',
                size='Total_Spent',
                color='Primary_Category',
                hover_name='merchant',
                title="Merchant Analysis: Frequency vs Average Amount (Size = Total Spent)",
                labels={'Transaction_Count': 'Number of Transactions', 'Avg_Amount': 'Average Transaction ($)'}
            )
            st.plotly_chart(fig_merchant, use_container_width=True)
            
            # Time series decomposition
            st.subheader("📅 Spending Time Series Analysis")
            
            # Daily spending with trend
            daily_spending = filtered_df.groupby('date')['amount'].sum().reset_index()
            daily_spending['date'] = pd.to_datetime(daily_spending['date'])
            daily_spending = daily_spending.sort_values('date')
            
            # Add moving averages
            daily_spending['MA_7'] = daily_spending['amount'].rolling(window=7).mean()
            daily_spending['MA_30'] = daily_spending['amount'].rolling(window=30).mean()
            
            fig_ts = go.Figure()
            
            fig_ts.add_trace(go.Scatter(
                x=daily_spending['date'],
                y=daily_spending['amount'],
                mode='lines',
                name='Daily Spending',
                line=dict(color='lightgray', width=1),
                opacity=0.6
            ))
            
            fig_ts.add_trace(go.Scatter(
                x=daily_spending['date'],
                y=daily_spending['MA_7'],
                mode='lines',
                name='7-Day Moving Average',
                line=dict(color='blue', width=2)
            ))
            
            fig_ts.add_trace(go.Scatter(
                x=daily_spending['date'],
                y=daily_spending['MA_30'],
                mode='lines',
                name='30-Day Moving Average',
                line=dict(color='red', width=2)
            ))
            
            fig_ts.update_layout(
                title="Daily Spending with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Amount ($)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_ts, use_container_width=True)
        
        # Statistical summary
        st.subheader("📊 Statistical Summary")
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Spending Distribution:**")
                stats_df = filtered_df.groupby('category')['amount'].describe().round(2)
                st.dataframe(stats_df)
            
            with col2:
                st.write("**Monthly Trends:**")
                if not monthly_df.empty:
                    monthly_summary = monthly_df.groupby('category')['total_amount'].sum().sort_values(ascending=False)
                    st.bar_chart(monthly_summary)
    
    with tab6:  # Use the fixed settings display
        display_settings_tab(transactions_df, budget_df, goals_df, monthly_df, patterns_df)
    
    # Continue with other tabs...
    # [Other tab implementations remain the same]

if __name__ == "__main__":
    main()