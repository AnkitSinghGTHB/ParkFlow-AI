# ParkFlow AI
**Prioritized Parking Enforcement & Congestion Quantification for Bengaluru**

> “Not just *where* violations happen—but how much congestion they cause,  
> how much delay they create, and exactly where to send the tow‑truck.”

[![Streamlit Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://github.com/AnkitSinghGTHB/ParkFlow-AI)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## The Problem
Bengaluru Traffic Police issue thousands of parking violation tickets.  
But enforcement is reactive: all violations are treated equally, with no way to
prioritize the ones that actually choke the city’s arteries.

## What ParkFlow AI Does
- 🔥 **Traffic Disruption Index (TDI)** – weights violations by road class, lane count & proximity to hospitals/metro stations.  
- ⏱️ **Quantified Congestion Impact** – uses the Bureau of Public Roads (BPR) function to convert violations into **vehicle‑hours lost**, **₹ economic loss** & **CO₂ emitted**.  
- 🤖 **ML‑powered Hourly Forecasts** – Random Forest predicts violation surges per hotspot for the next hour.  
- 🚛 **Tow‑Truck Route Optimizer** – plans the shortest path from a police station to the most disruptive active hotspots.

**Result:** A one‑click dashboard that tells an enforcement officer **which 3 streets to clear now, how much delay they’ll save, and the exact route to take**.

---

## Live Demo
👉 [**Try it here**](https://github.com/AnkitSinghGTHB/ParkFlow-AI)

### Dashboard Interface Preview
![ParkFlow AI Dashboard Preview](screenshots/dashboard_home.png)

---

## How It Works (30‑second read)

1. **Data In** → Anonymized police violation logs (Jan–May 2024)  
2. **Preprocess** → DBSCAN clusters hotspots, OpenStreetMap enriches with lane/POI data  
3. **Predict** → Random Forest forecasts violation count per hotspot per hour (MAE 6.19)  
4. **Compute Impact** → TDI ranks hotspots; BPR formula calculates delay, ₹, CO₂ for each  
5. **Optimize Route** → Greedy nearest-neighbor route tracing using actual OSRM road geometries  
6. **Visualize** → Streamlit + Pydeck interactive map with live metrics & “clearance scenario” slider

*Deep dive:* See [HANDBOOK.md](HANDBOOK.md) for detailed engineering & math.

---

## Tech Stack
- **UI:** Streamlit, Pydeck, Plotly  
- **ML:** Scikit‑learn (Random Forest)  
- **Spatial:** DBSCAN, OpenStreetMap Overpass API  
- **Traffic Engineering:** Bureau of Public Roads (BPR) function  
- **Routing:** FOSSGIS OSRM Routing Service

---

## Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/AnkitSinghGTHB/ParkFlow-AI.git
   cd ParkFlow-AI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add the dataset**
   - Download the provided `jan_to_may_violations.csv`
   - Place it inside the `data/` folder.

4. **Pre‑process & train (one‑time)**
   ```bash
   python preprocess.py
   python model.py
   ```

5. **Launch the dashboard**
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## Repository Structure
```
.
├── app.py                # Streamlit dashboard, BPR impact formulas, & OSRM routing
├── preprocess.py         # Data cleaning, DBSCAN clustering, & OSM enrichment
├── model.py              # ML training (Random Forest Regressor)
├── data/
│   ├── (violations CSV)  # Place dataset here (ignored by git to stay under 50MB upload limit)
│   ├── osm_cache.json    # Cached OSM queries (prevents rate limits)
│   ├── parking_hotspots.csv  # Preprocessed cluster centers
│   └── hourly_trends.csv     # Historical hourly violation metrics
├── screenshots/          # High-resolution screenshots of the dashboard interface
├── requirements.txt      # Project dependencies
├── HANDBOOK.md           # Deep technical specifications & pitch blueprint
└── README.md             # This landing page
```

---

## Credits
Built for Flipkart Gridlock 2.0 Round 2 – Theme: *Poor Visibility on Parking‑Induced Congestion*.  
Dataset provided by Bengaluru Traffic Police (ASTraM).

[Demo Video](screenshots/interaction_demo.webp) | [Technical Handbook](HANDBOOK.md)
