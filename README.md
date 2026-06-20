# ParkFlow AI
**Prioritized Parking Enforcement & Congestion Quantification for Bengaluru**

> “Not just *where* violations happen—but how much congestion they cause, how much delay they create, and exactly where to send the tow‑truck.”

[![Streamlit Demo](https://img.shields.io/badge/demo-local-brightgreen?logo=streamlit)](http://localhost:8501)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/AnkitSinghGTHB/ParkFlow-AI)

---

## 📸 Dashboard Interface Hook
![Live Dashboard Map & Action Card](screenshots/dashboard_home.png)

---

## The Problem
Bengaluru Traffic Police issue thousands of parking violation tickets. But enforcement is reactive: all violations are treated equally, with no way to prioritize the ones that actually choke the city’s major arteries.

## What ParkFlow AI Does
* 🔥 **Traffic Disruption Index (TDI)** – weights violations by road class, lane count, and hospital/metro station proximity.
* ⏱️ **Quantified Congestion Impact** – integrates the Bureau of Public Roads (BPR) function to convert blockages into **commuter vehicle‑hours lost**, **₹ economic loss**, and **CO₂ emitted**.
* 🤖 **ML‑powered Hourly Forecasts** – Random Forest Regressor predicts violation surges per hotspot for the upcoming hour.
* 🚛 **OSRM Road Route Optimizer** – plans the shortest driving path along actual streets from local traffic police stations to active hotspots.
* 🎛️ **Clearance Scenario Simulator** – lets officers slide a slider to clear violations and see immediate animated delay recovery.

**Result:** A one‑click dashboard that tells an enforcement officer **which streets to clear now, how much delay they’ll save, and the exact route to take**.

---

## Live Demo
👉 **Run locally at `http://localhost:8501`** *(or connect your GitHub fork to Streamlit Community Cloud in 2 minutes)*

---

## How It Works (30‑second read)

1. **Data In** → Ingests anonymized police violation logs (Jan–May 2024).
2. **Preprocess** → DBSCAN clusters spatial coordinates; OpenStreetMap enriches lanes and POIs.
3. **Predict** → Random Forest forecasts hourly violations per hotspot (MAE 6.19).
4. **Compute Impact** → TDI ranks hotspots; BPR formula calculates delay, ₹, and CO₂ for each.
5. **Optimize Route** → Greedy nearest-neighbor routing queries OSRM driving geometries to plan routes.
6. **Visualize** → Streamlit + Pydeck dark map overlays road paths, white sequence labels, and live gauge graphs.

📖 **Deep Dive:** See [HANDBOOK.md](HANDBOOK.md) for detailed equations, architecture, and engineering resolutions.

---

## Tech Stack
* **UI:** Streamlit, Pydeck (WebGL), Plotly (Animated Indicator Gauges)
* **ML:** Scikit‑learn (Random Forest Regressor)
* **Spatial:** DBSCAN, OpenStreetMap Overpass REST API
* **Routing:** FOSSGIS OSRM Driving API
* **Traffic Engineering:** Bureau of Public Roads (BPR) function

---

## Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/AnkitSinghGTHB/ParkFlow-AI.git
   cd ParkFlow-AI/round%202
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Pre-process & cluster OSM metadata**
   ```bash
   python preprocess.py
   ```
   *(Downloads dataset and queries/caches OSM Overpass API to `data/osm_cache.json`)*

4. **Train the ML Predictive Model**
   ```bash
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
├── app.py                # Streamlit dashboard & BPR solver
├── preprocess.py         # Data cleaning, DBSCAN clustering, OSM Overpass queries
├── model.py              # ML training (Random Forest Regressor)
├── data/
│   ├── parking_hotspots.csv  # Preprocessed cluster metadata
│   ├── hourly_trends.csv     # Hour-by-hour aggregates for training
│   └── osm_cache.json        # Auto‑generated OSM cache (prevents rate limits)
├── screenshots/          # High-resolution visual assets
├── requirements.txt      # Project dependencies
├── HANDBOOK.md           # Deep technical specifications & pitch blueprint
└── README.md             # Landing page
```

---

## Credits
Built for Flipkart Gridlock Hackathon Round 2.  
Dataset provided by Bengaluru Traffic Police (ASTraM).

[Walkthrough Handbook](HANDBOOK.md) | [Demo Video](screenshots/interaction_demo.webp)
