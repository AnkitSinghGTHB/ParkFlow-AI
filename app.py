import os
import pickle
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="ParkFlow AI - Priority Enforcement Dashboard",
    page_icon="🛑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Bold Minimalistic UI
st.markdown("""
<style>
    /* Clean System Fonts */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Clean Title Area */
    .title-area {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #21262d;
    }
    
    .main-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #f0f6fc;
        margin: 0;
    }
    
    .main-subtitle {
        color: #8b949e;
        font-size: 1rem;
        margin-top: 0.25rem;
    }
    
    /* Bold Minimalist Card Style */
    .bold-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Metrics Styles */
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.1em;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.2em 0.6em;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .badge-primary {
        background-color: rgba(240, 82, 82, 0.1);
        color: #f05252;
        border: 1px solid #f05252;
    }
    .badge-secondary {
        background-color: rgba(255, 159, 10, 0.1);
        color: #ff9f0a;
        border: 1px solid #ff9f0a;
    }
</style>
""", unsafe_allow_html=True)

# Helper Paths
HOTSPOTS_FILE = os.path.join("data", "parking_hotspots.csv")
MODEL_FILE = os.path.join("data", "predictor.pkl")

# Load Datasets safely
def load_hotspots():
    if os.path.exists(HOTSPOTS_FILE):
        return pd.read_csv(HOTSPOTS_FILE)
    return None

def load_predictor():
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, 'rb') as f:
            return pickle.load(f)
    return None

hotspots_df = load_hotspots()
predictor_model = load_predictor()

if hotspots_df is None:
    st.error("Missing Data: Please make sure 'parking_hotspots.csv' exists in the 'data' directory.")
    st.stop()

# Police Station Locations for Dispatch Planner
POLICE_STATIONS = {
    "Cubbon Park Station": (12.9738, 77.5960),
    "Halasuru Station": (12.9734, 77.6256),
    "Majestic Station": (12.9756, 77.5689),
    "Koramangala Station": (12.9348, 77.6189)
}

# Header Dashboard (Plain and Bold)
st.markdown("""
<div class="title-area">
    <div class="main-title">ParkFlow AI</div>
    <div class="main-subtitle">Prioritized Traffic Enforcement & Capacity Analytics</div>
    <div style="margin-top: 0.75rem;">
        <span class="badge badge-primary">ASTraM (Bengaluru Traffic Police)</span>
        <span class="badge badge-secondary">MapmyIndia Infrastructure</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar UI Controls
st.sidebar.markdown("### Enforcement Controls", unsafe_allow_html=True)

# Day of week selector
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_day_str = st.sidebar.selectbox("Target Day", days, key="day_select")
day_of_week = days.index(selected_day_str)

# Hour of day selector
hour = st.sidebar.slider("Target Hour", 0, 23, 17, key="hour_select")

# Enable other violations overlay
overlay_other = st.sidebar.checkbox("Overlay Secondary Offences", value=False, key="other_violations_chk")
st.sidebar.caption("Correlates with Helmet, One-Way, and License Plate violations.")

# Route Planner Settings
st.sidebar.markdown("---")
st.sidebar.markdown("### Tow-Truck Dispatch Route", unsafe_allow_html=True)
enable_routing = st.sidebar.checkbox("Enable Route Planner Overlay", value=True)
start_station = st.sidebar.selectbox("Select Start Police Station", list(POLICE_STATIONS.keys()))
route_stops_count = st.sidebar.slider("Number of Hotspots to Visit", 2, 5, 3)

# Simulator controls
st.sidebar.markdown("---")
st.sidebar.markdown("### Capacity Simulator", unsafe_allow_html=True)
enforcement_reduction = st.sidebar.slider(
    "Target Clearance Rate (%)",
    min_value=0, max_value=100, value=40, step=5,
    key="enforcement_slider"
)
st.sidebar.caption("Percentage of active parking blockages cleared.")

def calculate_bpr_delay(violations_count, lanes, highway_type, maxspeed, clearance_rate=0.0):
    speed = float(maxspeed) if float(maxspeed) > 0 else 40.0
    t_free = (1.0 / speed) * 60.0
    hw = str(highway_type).lower().split(';')[0].strip()
    if hw in ['motorway', 'trunk', 'primary']:
        v = 1200 * lanes
    elif hw == 'secondary':
        v = 800 * lanes
    elif hw == 'tertiary':
        v = 500 * lanes
    else:
        v = 200 * lanes
    cap_base = lanes * 1500.0
    violations_present = violations_count * (1.0 - (clearance_rate / 100.0))
    if violations_present > 0:
        blocked_lanes = min(1.0, np.log1p(violations_present) / 2.0)
    else:
        blocked_lanes = 0.0
    cap_reduced = max(300.0, (lanes - blocked_lanes) * 1500.0)
    t_congested = t_free * (1.0 + 0.15 * (v / cap_reduced)**4)
    delay_per_vehicle = max(0.0, t_congested - t_free)
    vehicle_hours_lost = (delay_per_vehicle / 60.0) * v
    return vehicle_hours_lost

# Calculate local predictions per hotspot (Coordinates based)
current_month = datetime.now().month
if predictor_model is not None:
    preds = []
    for idx, row in hotspots_df.iterrows():
        lat, lon = row['center_lat'], row['center_lon']
        inp = pd.DataFrame([[lat, lon, current_month, day_of_week, hour]], columns=['center_lat', 'center_lon', 'month', 'day_of_week', 'hour'])
        preds.append(predictor_model.predict(inp)[0])
    hotspots_df['predicted_count'] = preds
else:
    hotspots_df['predicted_count'] = hotspots_df['violation_count'] / (5 * 30) # fallback average

# Calculate BPR congestion delays
total_delay_base = 0.0
total_delay_enforced = 0.0
for idx, row in hotspots_df.iterrows():
    pred_count = row['predicted_count']
    lanes = row['lanes']
    hw = row['highway']
    maxspeed = row['maxspeed']
    total_delay_base += calculate_bpr_delay(pred_count, lanes, hw, maxspeed, clearance_rate=0.0)
    total_delay_enforced += calculate_bpr_delay(pred_count, lanes, hw, maxspeed, clearance_rate=enforcement_reduction)

delay_hours_saved = total_delay_base - total_delay_enforced
economic_savings = delay_hours_saved * 250.0  # ₹250/hr average delay cost in Bengaluru
co2_saved = delay_hours_saved * 0.42  # 0.42 kg CO2 per vehicle-hour saved

# Compute statistics based on selection
total_violations = hotspots_df['violation_count'].sum()
max_tdi = hotspots_df['tdi'].max()
cars_cleared = int(total_violations * (enforcement_reduction / 100.0))
road_space_recovered = cars_cleared * 4.5 

# Layout: Main KPI Cards
col1, col2, col3 = st.columns(3)
col1.metric("Active Hotspots Identified", f"{len(hotspots_df)}")
col2.metric("Peak Traffic Disruption Index", f"{max_tdi:.1f}")
col3.metric("Est. Lane-Meters Recovered", f"{road_space_recovered:,.0f} m")

# Layout: Tabs
tab_map, tab_comparison, tab_prediction = st.tabs([
    "Network Disruption Map", 
    "TDI vs Naive Ranking", 
    "Predictive Patrol Scheduler"
])

# TAB 1: Pydeck Map & Routing
with tab_map:
    st.markdown("### Priority Hotspots (Weighted by Network Importance)")
    st.write("Hotspots are sized by total violations and colored by their Traffic Disruption Index (TDI). Red indicates high disruption on narrow, high-classification arterials.")

    # Prepare color mapping based on TDI score
    def get_color(tdi_val):
        if tdi_val > 15000:
            return [240, 82, 82, 220]  # Red
        elif tdi_val > 8000:
            return [255, 159, 10, 220]  # Orange
        else:
            return [250, 204, 21, 220]  # Yellow

    hotspots_df['color'] = hotspots_df['tdi'].apply(get_color)
    # Radius based on violation count (scaled)
    hotspots_df['radius'] = np.sqrt(hotspots_df['violation_count']) * 15

    # Define Pydeck Layers
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            hotspots_df,
            get_position=["center_lon", "center_lat"],
            get_fill_color="color",
            get_radius="radius",
            pickable=True,
            auto_highlight=True,
        )
    ]

    # Calculate and Add Route LineLayer if enabled
    route_df = pd.DataFrame()
    if enable_routing:
        start_coords = POLICE_STATIONS[start_station]
        
        # Sort hotspots by current TDI to find top targets
        top_targets = hotspots_df.head(route_stops_count).copy()
        
        # Greedy Nearest Neighbor routing solver
        route_data = []
        curr_lat, curr_lon = start_coords[0], start_coords[1]
        remaining_points = list(zip(top_targets['center_lat'], top_targets['center_lon'], top_targets['name']))
        
        while remaining_points:
            # Find closest remaining coordinate
            distances = [np.sqrt((curr_lat - p[0])**2 + (curr_lon - p[1])**2) for p in remaining_points]
            closest_idx = np.argmin(distances)
            next_point = remaining_points.pop(closest_idx)
            route_data.append({
                'start_lat': curr_lat,
                'start_lon': curr_lon,
                'end_lat': next_point[0],
                'end_lon': next_point[1],
                'name': next_point[2]
            })
            curr_lat, curr_lon = next_point[0], next_point[1]
            
        route_df = pd.DataFrame(route_data)
        
        layers.append(
            pdk.Layer(
                "LineLayer",
                route_df,
                get_source_position=["start_lon", "start_lat"],
                get_target_position=["end_lon", "end_lat"],
                get_color=[240, 82, 82, 255], # Solid Red route line
                get_width=4,
                pickable=True
            )
        )

    # Map state: center around Bengaluru
    view_state = pdk.ViewState(
        latitude=12.9716,
        longitude=77.5946,
        zoom=11.5,
        pitch=45
    )

    # Render Pydeck Map
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="dark",
        tooltip={
            "html": "<b>Location ID:</b> {cluster_id}<br/>"
                    "<b>Road Name:</b> {name}<br/>"
                    "<b>Class:</b> {highway}<br/>"
                    "<b>Lanes:</b> {lanes}<br/>"
                    "<b>Violations:</b> {violation_count}<br/>"
                    "<b>Two-Wheelers:</b> {two_wheeler_pct:.1f}%<br/>"
                    "<b>POIs (200m):</b> {poi_details}<br/>"
                    "<b>Disruption Index (TDI):</b> {tdi:,.1f}",
            "style": {"backgroundColor": "#161b22", "color": "white", "borderColor": "#30363d", "borderWidth": "1px"}
        }
    )
    st.pydeck_chart(r)

    # Render Dispatch Route Summary if enabled
    if enable_routing and not route_df.empty:
        st.markdown(f"### 📍 Dispatch Route Path ({start_station} Start)")
        route_text = f"**Start** ({start_station})"
        for idx, row in route_df.iterrows():
            route_text += f" ➡️ **Stop {idx+1}**: {row['name']}"
        st.markdown(route_text)

    # Show secondary violations correlation if selected
    if overlay_other:
        st.markdown("### Multi-Offence Correlation Analysis")
        st.write("Areas with high parking violations often show significant overlap with secondary violations.")
        
        # Plot correlations
        top_10 = hotspots_df.head(10)
        fig_corr = go.Figure()
        fig_corr.add_trace(go.Bar(name='Parking', x=top_10['name'], y=top_10['violation_count'], marker_color='#f05252'))
        fig_corr.add_trace(go.Bar(name='Helmet', x=top_10['name'], y=top_10['helmet_count'], marker_color='#ff9f0a'))
        fig_corr.add_trace(go.Bar(name='One-Way', x=top_10['name'], y=top_10['one_way_count'], marker_color='#facc15'))
        fig_corr.update_layout(
            barmode='group',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Hotspot Location",
            yaxis_title="Offence Count",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# TAB 2: TDI vs Naive Ranking Comparison
with tab_comparison:
    st.markdown("### Traffic Disruption Index vs. Raw Violations")
    st.markdown("""
    Standard models simply count violation frequencies. **ParkFlow AI** evaluates each hotspot's **structural impact on the road network**. 
    A single car parked on a **1-lane arterial (Primary)** causes more gridlock than 10 cars parked on a **4-lane residential side street**.
    """)

    # Get data ranked by TDI vs. ranked by Raw Violations
    df_tdi = hotspots_df.copy().sort_values(by='tdi', ascending=False).reset_index(drop=True)
    df_violations = hotspots_df.copy().sort_values(by='violation_count', ascending=False).reset_index(drop=True)

    # Rank indices
    df_tdi['tdi_rank'] = df_tdi.index + 1
    df_violations['violation_rank'] = df_violations.index + 1

    # Merge on cluster ID to see rank changes
    comparison_df = df_tdi[['cluster_id', 'name', 'highway', 'lanes', 'violation_count', 'tdi', 'tdi_rank']].merge(
        df_violations[['cluster_id', 'violation_rank']], on='cluster_id'
    )

    comparison_df['rank_change'] = comparison_df['violation_rank'] - comparison_df['tdi_rank']

    # Display rank changes
    col_chart, col_case = st.columns([2, 1])

    with col_chart:
        st.markdown("#### Top 10 Priority Shifts")
        top_10_comp = comparison_df.head(10)
        
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name='TDI Rank (Network-Aware)', 
            y=top_10_comp['name'], 
            x=top_10_comp['tdi_rank'], 
            orientation='h',
            marker_color='#f05252',
            text=top_10_comp['tdi_rank'].apply(lambda x: f"TDI #{x}")
        ))
        fig_comp.add_trace(go.Bar(
            name='Raw Violation Rank', 
            y=top_10_comp['name'], 
            x=top_10_comp['violation_rank'], 
            orientation='h',
            marker_color='#4b5563',
            text=top_10_comp['violation_rank'].apply(lambda x: f"Raw #{x}")
        ))
        fig_comp.update_layout(
            barmode='group',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange="reversed"),
            xaxis_title="Rank (Lower is Higher Priority)",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_case:
        st.markdown("#### Case Study")
        # Highlight top rank change
        up_shifted = comparison_df[comparison_df['rank_change'] > 0].sort_values(by='rank_change', ascending=False)
        if len(up_shifted) > 0:
            best_case = up_shifted.iloc[0]
            st.markdown(f"""
            ##### Priority Shift: {best_case['name']}
            *{best_case['highway'].capitalize()} Road, {best_case['lanes']:.0f} Lanes*

            * **Raw Count Rank**: #{best_case['violation_rank']}
            * **TDI (Network) Rank**: #{best_case['tdi_rank']}
            * **Priority Gain**: +{best_case['rank_change']} positions

            **Rationale**  
            This street has a lower volume of raw parking violations, but its low lane count and high highway classification make illegal parking extremely disruptive. Clearing this spot unlocks a critical node in the network.
            """)
        else:
            st.write("TDI ranks correlate strongly with counts, but lanes and classification refine priority.")

# TAB 3: Predictive Planner & Patrol Scheduler
with tab_prediction:
    st.markdown("### Localized Predictive Patrol Scheduler")
    st.write(f"Displaying hotspot-specific predictions for **{selected_day_str}** around **{hour}:00** using the granular Random Forest model.")

    if predictor_model is None:
        st.warning("Model file 'data/predictor.pkl' not found. Run model.py to enable ML forecasting.")
    else:
        # Predict citywide volume (sum of all predicted hotspots)
        pred_vol = hotspots_df['predicted_count'].sum()

        col_pred_info, col_pred_chart = st.columns([1, 1])

        with col_pred_info:
            st.metric("Predicted Total Volume (Selected Window)", f"{pred_vol:.0f} violations/hr")
            
            st.markdown(f"""
            **Prescriptive Dispatch & Enforcement Schedule**  
            Target window: {selected_day_str} at {hour:02d}:00:
            """)
            
            # Formulate detailed schedule listing top 3 hotspots, POIs, vehicle breakdowns and strategies
            for idx in range(3):
                row = hotspots_df.iloc[idx]
                lock_team = "Wheel-Locking Unit" if row['two_wheeler_pct'] >= 55 else "Towed Dispatch"
                vehicle_str = f"({row['two_wheeler_pct']:.0f}% Two-Wheelers)"
                st.markdown(f"""
                **{idx+1}. {row['name']}** (TDI: {row['tdi']:,.0f})
                * **Predicted Volume**: {row['predicted_count']:.1f} blockages/hr
                * **Enforcement Type**: `{lock_team}` {vehicle_str}
                * **OSM Context**: Near {row['poi_details']}
                """)

        with col_pred_chart:
            # Predict for all 24 hours for the top hotspot to show its specific cycle
            all_hours = list(range(24))
            top_spot = hotspots_df.iloc[0]
            predictions = []
            for h in all_hours:
                inp = pd.DataFrame([[top_spot['center_lat'], top_spot['center_lon'], current_month, day_of_week, h]], columns=['center_lat', 'center_lon', 'month', 'day_of_week', 'hour'])
                predictions.append(predictor_model.predict(inp)[0])

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=all_hours, 
                y=predictions, 
                mode='lines+markers',
                line=dict(color='#f05252', width=3),
                marker=dict(size=6),
                name=top_spot['name']
            ))
            # Highlight selected hour
            fig_line.add_trace(go.Scatter(
                x=[hour],
                y=[top_spot['predicted_count']],
                mode='markers',
                marker=dict(color='#ff9f0a', size=14, line=dict(color='white', width=2)),
                name='Selected Hour'
            ))
            fig_line.update_layout(
                title=f"Hourly Forecast for {top_spot['name']}",
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickmode='linear', tick0=0, dtick=2),
                xaxis_title="Hour of Day",
                yaxis_title="Estimated Violations",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_line, use_container_width=True)

# Interactive Capacity Simulation Section
st.markdown("---")
st.markdown("### Microscopic Capacity Simulation")
st.write(f"Simulating target clearance of **{enforcement_reduction}%** of parking violations using historical citywide flow models.")

sim_col1, sim_col2, sim_col3 = st.columns(3)

with sim_col1:
    st.metric(
        label="Towing Actions Required",
        value=f"{cars_cleared:,} vehicles",
        delta=f"-{enforcement_reduction}%",
        delta_color="inverse"
    )

with sim_col2:
    st.metric(
        label="Estimated Delay Saved",
        value=f"{delay_hours_saved:,.1f} veh-hours",
        delta=f"{(delay_hours_saved * 60):,.0f} min-flow equiv",
        delta_color="normal"
    )

with sim_col3:
    st.metric(
        label="Est. Economic Value Recaptured",
        value=f"₹ {economic_savings:,.2f}",
        delta="Fuel & Idling Savings",
        delta_color="normal"
    )

st.markdown(f"""
**Carbon Footprint Impact**  
By preventing vehicle idling and stop-and-go conditions through clearing critical parking spots, the estimated daily carbon emission reduction for these intersections is **{co2_saved:.2f} kg of CO₂** (based on standard emission factors for commuter cars in heavy traffic).
""")
