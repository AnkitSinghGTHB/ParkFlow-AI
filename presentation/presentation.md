# ParkFlow AI Pitch Deck

---

## Slide 1: Title & Hook
# ParkFlow AI
### Predictive Priority Enforcement & Traffic-Impact Quantification

*“Not just where violations happen—but how much congestion they cause, how much delay they create, and exactly where to send the tow-truck.”*

- **Theme:** Poor Visibility on Parking-Induced Congestion
- **Built For:** Flipkart Gridlock 2.0 Round 2
- **Data Source:** ASTraM (Bengaluru Traffic Police)

---

## Slide 2: The Problem
### The "Heatmap Trap" in Modern Enforcement

* **Reactive vs. Proactive:** Standard traffic enforcement counts raw infraction density, creating static heatmaps.
* **The Structural Blindspot:** Heatmaps treat a double-parked delivery vehicle on an arterial road identically to one on a residential side street.
* **Cascading Gridlock:** Bengaluru's narrow streets and variable road capacities mean minor blockages at critical nodes cause major, city-wide delays.

---

## Slide 3: The Solution (TDI)
### Introducing the Traffic Disruption Index (TDI)

Evaluating each blockage by its actual structural cost to the network:

$$\text{TDI} = \frac{\text{Violation Count} \times \text{Road Classification Weight}}{\text{Number of Lanes}} \times \text{POI Proximity Multiplier}$$

* **Road Class Weights:** Motorways & Primary Roads = 3.5x | Secondary = 2.2x | Residential = 1.0x.
* **Lane Capacity Divider:** Blocking a single lane on a 1-lane road cuts capacity to 0%; multi-lane roads absorb spillover.
* **Critical POI Multiplier:** Proximity to emergency hospitals (1.5x) or transit hubs (1.3x) scales priority.

---

## Slide 4: BPR Traffic Physics
### Quantifying Congestion Impact mathematically

Fusing standard transportation planning equations to convert raw violations into physical delay metrics:

$$T_{\text{congested}} = T_{\text{free}} \times \left( 1 + 0.15 \times \left( \frac{V}{C_{\text{reduced}}} \right)^4 \right)$$

* **Free-Flow Time ($T_{\text{free}}$):** Derived from OpenStreetMap segment speed limits.
* **Logarithmic Capacity Reduction ($C_{\text{reduced}}$):**
  $$\text{blocked\_lanes} = \min\left(1.0, \frac{\log(1 + \text{count})}{2}\right)$$
  *Logarithmic constraint models diminishing marginal disruption (subsequent cars line up but don't block more lanes).*

---

## Slide 5: Technical Pipeline
### End-to-End Predictive Congestion Architecture

1. **ASTraM Logs In** → Raw police log ingestion (coordinates, timestamp, offence types).
2. **DBSCAN Clustering** → Groups spatial data to define coordinates of active hotspots within 50m.
3. **OSM Overpass API** → Enrich clusters with road classifications, lane counts, and POI indicators.
4. **Random Forest Regressor** → Predicts coordinate-based hourly violation spikes (MAE: 6.19).
5. **Greedy Routing & UI** → Runs priority routing & computes BPR values for real-time visualization.

---

## Slide 6: Dashboard Interface
### Live Dispatch & Network Disruption Map

* **WebGL Rendering:** High-performance pydeck map displaying hotspots sized by violation counts and color-coded by TDI severity.
* **Live Action Card:** Prescriptive dispatch recommendation that tells officers exactly *who* to send, *where*, *when*, and the *delay/economic hours saved*.
* **Correlation Panel:** Identifies patterns linking parking violations to secondary offences (helmet-less riding, one-way violations).

---

## Slide 7: Dispatch TSP Routing
### Priority-Weighted OSRM Route Optimizer

* **Station Origin Routing:** Officers select their starting traffic police station (e.g., Cubbon Park, Majestic).
* **Travelling Salesperson Problem (TSP):** A greedy solver routes the dispatch vector through the top-priority TDI hotspots.
* **Real Road Geometries:** Integrates OSRM geometries to draw paths along actual streets rather than straight lines, matching realistic police transit patterns.

---

## Slide 8: Economic & Climate Impact
### What-If Clearance Sandbox & Hard Metrics

* **Commuter Productivity Saved:** Recovers ₹250/hour of vehicle idling and commuter delays.
* **SLA Protection:** Safeguards hyper-local supply chains and delivery times across city corridors.
* **Carbon Reduction:** Saves 0.42 kg of CO₂ per vehicle-hour of reduced gridlock.
* **Interactive Sandbox:** Officers drag a slider to simulate clearing $X\%$ of violations, viewing real-time calculations of financial and emissions recovery.

---

## Slide 9: Scalability & Integration
### A Modular Architecture for Municipal Deployment

* **Enterprise Routing API:** The OSM-based router is designed to easily hot-swap with municipal routing engines (like MapmyIndia REST routing) by re-pointing environmental API base URLs.
* **Live Feed Compatibility:** The DBSCAN pipeline can be adapted to process streaming IoT camera feeds or ASTraM mobile app reporting in real-time.
* **Dynamic Fleet Dispatching:** Expands from standard tow-truck routing to allocate diverse enforcement assets (wheel-lock units vs. heavy towing rigs).

---

## Slide 10: Conclusion
### ParkFlow AI: The Modern Traffic Enforcement Standard

- ✅ **Operational Shift:** Moves traffic police from simple heatmaps to structural priority routing.
- ✅ **Validated Science:** Built on the BPR traffic flow equations and validated against empirical TomTom data.
- ✅ **Zero-Config Deployment:** Streamlit-powered dashboard that loads instantly with cached geometries.

---
Built for Flipkart Gridlock 2.0 Hackathon Round 2.
Dataset provided by Bengaluru Traffic Police (ASTraM).
