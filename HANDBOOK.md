# ParkFlow AI: Technical Walkthrough & Engineering Handbook

This handbook details the engineering architecture, mathematical models, and operational frameworks driving ParkFlow AI.

---

## 1. The Core Philosophy (Why ParkFlow AI Wins)

Most software interventions in urban mobility suffer from the **"Heatmap Trap"**—they ingest historical violation logs, run spatial clustering, and draw a static heatmap indicating where infractions are frequent.

However, enforcement agencies like the **Bengaluru Traffic Police (ASTraM)** already know where hotspots are. The missing operational intelligence lies in answering:
* Which specific structural violations cause the most severe, cascading network choke-points?
* How can deployment resources (tow-trucks, patrol units) be dynamically routed in real-time based on predictive traffic disruption?

### The Core Metric: Traffic Disruption Index (TDI)
ParkFlow AI shifts focus from frequency to severity by calculating a custom network-aware score for each hotspot:

$$\text{TDI} = \frac{\text{Violation Count} \times \text{Road Classification Weight}}{\text{Number of Lanes}} \times \text{POI Proximity Multiplier}$$

* **Road Class Weight:** Higher weights for major corridors (Motorway/Primary = 3.5x) where blocks cause cascading regional slowdowns, compared to residential streets (1.0x).
* **Lane Capacity Divider:** Blocking a single-lane road reduces throughput capacity to 0% (total gridlock), while a multi-lane road absorbs spillover. Dividing by lane count mathematically targets narrow bottleneck channels.
* **POI Multiplier:** Multipliers scale priority based on proximity to critical municipal anchors—emergency hospital zones (1.5x) and metro/bus transit stations (1.3x).

---

## 2. Advanced Traffic Engineering: The Bureau of Public Roads (BPR) Delay Model

To rigorously validate the TDI heuristic, the backend integrates the industry-standard **Bureau of Public Roads (BPR) travel time function** to compute real-time delay metrics in commuter-minutes and vehicle-hours:

$$T_{\text{congested}} = T_{\text{free}} \times \left( 1 + 0.15 \times \left( \frac{V}{C_{\text{reduced}}} \right)^4 \right)$$

### Algorithmic Execution in `app.py`:

1. **Free-Flow Time ($T_{\text{free}}$):** Extracted systematically from OpenStreetMap `maxspeed` tags over a normalized 1 km segment corridor:
   $$T_{\text{free}} = \frac{1}{\text{maxspeed}} \times 60 \text{ minutes}$$

2. **Traffic Volume ($V$):** Modeled dynamically using empirical urban baseline flows scaled by road tier classification (Primary = 1200 vehicles/hr per lane, Secondary = 800, Tertiary = 500, Residential = 200).

3. **Logarithmic Capacity Reduction ($C_{\text{reduced}}$):**
   Standard lane capacity is benchmarked at 1500 vehicles/hour per lane. An active parking violation blocks a portion of the road. We scale the blocked capacity logarithmically based on predicted violation accumulation:
   $$\text{blocked\_lanes} = \min\left(1.0, \frac{\log(1 + \text{count})}{2}\right)$$
   
   > **The Logarithmic Rationale:** We implement a logarithmic constraint to model diminishing marginal disruption. The first two illegally parked vehicles cause a massive initial layout bottleneck; subsequent vehicles parking behind them create a longer line but do not proportionally block *additional* lanes.

   $$C_{\text{reduced}} = (\text{lanes} - \text{blocked\_lanes}) \times 1500$$

### Macroeconomic & Climate Quantifications:
* **Commuter Delay Saved:** Evaluated as $\text{Delay} = (T_{\text{congested}} - T_{\text{free}}) \times V$ summed across all active hotspots.
* **Economic Value Recaptured:** Evaluated at **₹250 per hour**, reflecting the combined loss of local productivity, corporate delay, and fleet idling fuel waste in Bengaluru traffic.
* **Supply Chain/Last-Mile Delivery SLA Protection:** Quantifies the mitigation of delivery delays, protecting critical operational windows for hyper-local fulfillment networks.
* **CO₂ Emission Reduction:** Evaluated at **0.42 kg of CO₂ saved** per vehicle-hour of reduced congestion.

---

## 3. Technical Architecture & Data Pipeline

```
[Raw ASTraM Police Logs]
           │
           ▼
    (preprocess.py)
    ┌──────┴──────┐
    ▼             ▼
[DBSCAN Space]   [OSM Queries via Overpass API]
    │             │
    └──────┬──────┘
           ▼
 (osm_cache.json Cache)
           │
           ▼
  (hourly_trends.csv)
           │
           ▼
      (model.py)
      ── RandomForestRegressor (center_lat, center_lon, hour)
           │
           ▼
      (app.py UI)
   ┌───────┼───────┐
   ▼       ▼       ▼
[Pydeck] [Plotly] [Priority TSP Solver]
```

### The Tech Stack
* **UI & Dashboard Engine:** Streamlit (clean, unboxed dark theme layout).
* **Geospatial Visualization:** Pydeck (High-performance WebGL rendering for spatial scatterplots and route vectors) over a CartoDB Dark Matter keyless open basemap.
* **Analytical Matrix Computations:** Pandas and NumPy.
* **Machine Learning Framework:** Scikit-Learn (Random Forest Regressor).
* **Geospatial Microservices:** OpenStreetMap Overpass REST API (via Python `requests`).

---

## 4. Operational Code Execution Under the Hood

### Step A: Data Preprocessing & Localized Caching (`preprocess.py`)
* **Spatial Filtering:** Ingests and cleans the 298k row ASTraM dataset, isolating bounding boxes to the geographic limits of Bengaluru.
* **DBSCAN Clustering:** Groups historical coordinates within a strict 50-meter radius epsilon. Low-frequency spatial noise is automatically pruned.
* **OSM Enrichment & Network Memoization:** For the top 60 identified hotspot vectors, the pipeline queries OpenStreetMap to resolve road metadata (class, lane configurations) and POIs within 200 meters.
* **Local Cache Layer (`data/osm_cache.json`):** To circumvent Overpass API rate limits and avoid blocking execution loops during evaluation, all raw API network responses are stored in a local JSON cache, bringing subsequent hot-reloads down to sub-millisecond speeds.

### Step B: Spatial Machine Learning Pipeline (`model.py`)
* **Predictive Framework:** Trains a highly granular ensemble regressor to forecast hyper-local, hour-by-hour violation spikes.
* **Feature Engineering:** Features include `center_lat`, `center_lon`, `month`, `day_of_week`, and `hour`. The model targets the `violation_count`.
* **Model Validation:** Evaluates with a robust Mean Absolute Error (MAE) of **6.19 violations/hour** per individual hotspot.

### Step C: Route Optimization & Map Rendering (`app.py`)
* **Predictive Surge Aggregator:** Computes the current hour's predictive violation vector for all active nodes, sorting them automatically by total TDI impact.
* **Priority-Weighted Nearest-Neighbor TSP Heuristic:** Calculates the most efficient deployment path starting from a selected base (e.g., Cubbon Park Traffic Police Station) to navigate through active top-priority bottlenecks without backtracking.
* **Multi-Layer Pydeck Visuals:**
  - `ScatterplotLayer`: Renders hotspots dynamically scaled by violation density and color-coded by TDI severity boundaries (Red = Critical, Orange = High, Yellow = Moderate).
  - `PathLayer` (OSM Road Route): Traces proper routes along actual roads (using openstreetmap.de OSRM API) instead of drawing straight lines.
  - `TextLayer`: Overlays white visual indicators ("★ START", "Stop 1", etc.) above the circles with a clean pixel offset.

---

## 5. Engineering Hurdles & Resolutions (Where We Got Stuck)

* 🛠️ **The Machine Learning "cluster_id" Splitting Bug**
  * *Issue:* The pipeline originally passed `cluster_id` as a raw numeric feature. Because decision-tree ensembles treat integers as continuous values, the model attempted to split on arbitrary values (e.g., `cluster_id <= 25.5`). This introduced major spatial nonsense because the IDs were merely sequential array indices.
  * *Fix:* Dropped `cluster_id` and explicitly refactored the feature matrix to rely on `center_lat` and `center_lon`. The Random Forest now splits on geographic coordinates logically, creating spatial bounding boxes representing actual physical neighborhoods.

* 🛠️ **DateTime Format Variance Exception**
  * *Issue:* `pandas.to_datetime` crashed unexpectedly during execution due to floating fractional seconds within incoming timestamp vectors (e.g., `.022782+00`).
  * *Fix:* Configured `format='ISO8601'` explicitly inside the I/O parser, forcing Pandas to drop native regex loops and leverage its optimized internal C-based ISO parser.

* 🛠️ **Stale Memory Polling via Streamlit Cache**
  * *Issue:* When retraining the predictive model or changing the underlying training parameters, the frontend visualization persistently served outdated model architectures, triggering a `ValueError`.
  * *Fix:* Discovered that `@st.cache_resource` was pinning the initial un-pickled model instance directly in the application's warm in-memory layer. Removed the global decorator to force clean disk-level re-polling on user execution.

* 🛠️ **Blank Map Canvas (Token Auth Failures)**
  * *Issue:* Pydeck’s default Mapbox base style required a remote `MAPBOX_API_KEY`, causing the mapping layer to load as a blank black canvas on fresh machines.
  * *Fix:* Migrated the map style token configuration from `"mapbox://styles/mapbox/dark-v9"` to `"dark"`. This reroutes the engine to use Pydeck’s native, open-source CartoDB Dark Matter tileset, achieving zero-config rendering instantly.

* 🛠️ **Pydeck Tooltip Raw Template Rendering Bug:**
  * *Issue:* Deck.gl's client-side JavaScript template engine parsed Python-style formatting (e.g., `{predicted_count:.1f}`) as raw text, showing raw curly braces.
  * *Fix:* Formatted columns into strings in Python first (e.g. `predicted_count_str`) and updated tooltip templates to refer to these clean variables. Set pickable to False on secondary layers.

---

## 6. Submission Evaluation & Pitch Blueprint

| Slide Number | Slide Title | Key Presenting Narrative |
| :---: | :--- | :--- |
| **1** | Title & Framework | **ParkFlow AI:** Prioritized Enforcement & Dispatch Optimization Pipelines. |
| **2** | The Problem | Traditional enforcement tracks absolute violation volume, treating an obstruction in a residential alleyway identically to an arterial road block. |
| **3** | The Solution (TDI) | Introducing the **Traffic Disruption Index (TDI)**. We mathematically weigh violations by structural lane capacity, network road class, and critical POI (hospital) proximity. |
| **4** | BPR Traffic Physics | Validating heuristic priority using the **Bureau of Public Roads (BPR) delay model**, mapping raw infractions directly into commuter-minutes and vehicle-hours lost. |
| **5** | Tech Architecture | Fusing raw ASTraM police logs with OpenStreetMap/MapmyIndia network layers combined with coordinate-based Random Forest predictions. |
| **6** | Core Live Demo | Display the dashboard interface. Show the operational shift from basic infraction counting to true TDI severe-risk mapping. |
| **7** | Dynamic TSP Dispatch | Demonstrate the Priority TSP routing module generating optimal enforcement paths directly from local sector traffic police stations. |
| **8** | Economic Metrics | Display live calculations of vehicle-hours saved, fuel/productivity recaptured (₹250/hr), and systemic CO₂ emission cuts. |
| **9** | Production Scaling | Demonstrate the modular architecture: OpenStreetMap network configurations can be seamlessly hot-swapped for enterprise MapmyIndia REST routing APIs by simply changing the environmental base URL endpoint. |
| **10** | Execution & Handoff | Summary of deliverables: Production-ready, keyless, zero-config web app ready for deployment testing. |
