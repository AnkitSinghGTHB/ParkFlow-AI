# ParkFlow AI: Prioritized Parking Enforcement & Traffic Disruption Analytics

ParkFlow AI is an intelligent parking enforcement prioritization engine built for the **Bengaluru Traffic Police (ASTraM)** and powered by **MapmyIndia** mapping infrastructure. Instead of simple hotspot counting, ParkFlow AI calculates the structural impact of parking violations on the road network using real-world datasets and OpenStreetMap (OSM) highway metrics, outputting a **Traffic Disruption Index (TDI)**.

---

## Features

1. **Traffic Disruption Index (TDI) Scoring**: Priorities are weighted by road classifications (Primary vs Residential) and lane counts. A violation on a 1-lane arterial gets prioritized over multiple violations on a 4-lane local street.
2. **Dynamic 3D Hotspot Map**: Powered by Pydeck and Mapbox overlays showing exact violation counts, lane widths blocked, and traffic disruption index levels.
3. **Machine Learning Predictive Patrol Scheduler**: Forecaster built with Random Forest Regressor suggesting optimal patrol deployment schedules for any hour and day.
4. **Interactive Capacity Simulator**: Run "What-If" scenarios to calculate recovered road lane-meters, delay reduction, economic savings, and carbon emission cuts.

---

## Installation & Setup

Ensure you have Python 3.9 or higher installed.

1. **Clone or navigate to the directory**:
   ```bash
   cd "round 2"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Data Preprocessing (Downloads, Clusters, and Matches OSM data)**:
   ```bash
   python preprocess.py
   ```
   *Note: This script will download the 298k police violation dataset, cache it locally, run DBSCAN spatial clustering, query the OSM Overpass API to get road metadata for the top hotspots, and output structured CSV files.*

4. **Train the ML Predictive Model**:
   ```bash
   python model.py
   ```
   *Note: Trains a Random Forest regressor on hourly aggregated violation frequencies and serializes the model to `data/predictor.pkl`.*

5. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```

---

## Repository Structure

* `app.py`: Streamlit dashboard implementation (UI, interactive maps, graphs, simulator).
* `preprocess.py`: Downloads the raw dataset, filters parking violations, runs DBSCAN, and fetches road data via OSM Overpass.
* `model.py`: Fits and evaluates the Random Forest forecasting model.
* `requirements.txt`: Python package dependencies.
* `data/`: Folder containing cached datasets and the trained model.
