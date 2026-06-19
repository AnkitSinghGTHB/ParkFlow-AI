import os
import requests
import json
import time
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

# Constants
DATA_URL = "https://uc.hackerearth.com/he-public-ap-south-1/jan%20to%20may%20police%20violation_anonymized791b166.csv"
DATA_DIR = "data"
RAW_FILE = os.path.join(DATA_DIR, "jan_to_may_violations.csv")
HOTSPOTS_FILE = os.path.join(DATA_DIR, "parking_hotspots.csv")
HOURLY_FILE = os.path.join(DATA_DIR, "hourly_trends.csv")
CACHE_FILE = os.path.join(DATA_DIR, "osm_cache.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)

# Load local cache if it exists
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        osm_cache = json.load(f)
else:
    osm_cache = {}

def save_cache():
    with open(CACHE_FILE, 'w') as f:
        json.dump(osm_cache, f, indent=4)

def download_data():
    if os.path.exists(RAW_FILE):
        print("Raw dataset already cached locally.")
        return
    print(f"Downloading dataset from {DATA_URL}...")
    response = requests.get(DATA_URL, stream=True)
    with open(RAW_FILE, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print("Download completed and saved to cache.")

def get_osm_road_info(lat, lon):
    """
    Queries the OpenStreetMap Overpass API to get the closest highway features.
    Caches the results locally.
    """
    cache_key = f"road_{lat:.4f}_{lon:.4f}"
    if cache_key in osm_cache:
        return osm_cache[cache_key]

    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:15];
    way(around:60, {lat}, {lon})[highway];
    out tags;
    """
    try:
        response = requests.post(url, data={'data': query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'elements' in data and len(data['elements']) > 0:
                elements = data['elements']
                best_element = elements[0]
                for el in elements:
                    tags = el.get('tags', {})
                    if 'name' in tags and tags.get('highway') in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']:
                        best_element = el
                        break
                tags = best_element.get('tags', {})
                info = {
                    'highway': tags.get('highway', 'residential'),
                    'name': tags.get('name', 'Unnamed Road'),
                    'lanes': tags.get('lanes', '2'),
                    'maxspeed': tags.get('maxspeed', '40')
                }
                osm_cache[cache_key] = info
                return info
    except Exception as e:
        print(f"OSM Road query failed for ({lat}, {lon}): {e}")
    
    return {'highway': 'residential', 'name': 'Unnamed Road', 'lanes': '2', 'maxspeed': '40'}

def get_poi_info(lat, lon):
    """
    Queries Overpass API for POIs (Hospitals, Metro Stations, Schools) within 200m.
    Caches the results locally.
    """
    cache_key = f"poi_{lat:.4f}_{lon:.4f}"
    if cache_key in osm_cache:
        return osm_cache[cache_key]

    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:15];
    (
      node(around:200, {lat}, {lon})[amenity~"hospital|school|university|college|bus_station|subway_station|mall"];
      way(around:200, {lat}, {lon})[amenity~"hospital|school|university|college|bus_station|subway_station|mall"];
    );
    out tags;
    """
    try:
        response = requests.post(url, data={'data': query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pois = []
            if 'elements' in data:
                for el in data['elements']:
                    tags = el.get('tags', {})
                    amenity = tags.get('amenity', 'poi')
                    name = tags.get('name', 'Unnamed POI')
                    pois.append({'type': amenity, 'name': name})
            osm_cache[cache_key] = pois
            return pois
    except Exception as e:
        print(f"OSM POI query failed for ({lat}, {lon}): {e}")
    
    return []

def preprocess_and_cluster():
    print("Loading data from local cache...")
    df = pd.read_csv(RAW_FILE)
    print(f"Total rows: {len(df)}")

    # 1. Clean and Classify violations
    df['violation_type_str'] = df['violation_type'].astype(str).str.upper()
    df['is_parking'] = df['violation_type_str'].str.contains('PARKING')
    df['is_helmet'] = df['violation_type_str'].str.contains('HELMET')
    df['is_one_way'] = df['violation_type_str'].str.contains('ONE WAY|NO ENTRY')
    df['is_plate'] = df['violation_type_str'].str.contains('NUMBER PLATE')

    # Vehicle type classification
    df['vehicle_type_str'] = df['vehicle_type'].astype(str).str.upper()
    two_wheeler_types = ['SCOOTER', 'MOTOR CYCLE', 'MOPED']
    df['is_two_wheeler'] = df['vehicle_type_str'].apply(lambda x: any(t in x for t in two_wheeler_types))

    # Bounding box filter for Bengaluru
    df = df[(df['latitude'] >= 12.8) & (df['latitude'] <= 13.1) & 
            (df['longitude'] >= 77.4) & (df['longitude'] <= 77.8)]
    print(f"Rows inside Bengaluru: {len(df)}")

    parking_df = df[df['is_parking']].copy()
    print(f"Total parking violations: {len(parking_df)}")

    # 2. Spatial Clustering using DBSCAN
    parking_df['lat_bin'] = parking_df['latitude'].round(4)
    parking_df['lon_bin'] = parking_df['longitude'].round(4)

    binned = parking_df.groupby(['lat_bin', 'lon_bin']).size().reset_index(name='count')
    coords = binned[['lat_bin', 'lon_bin']].values
    db = DBSCAN(eps=0.0005, min_samples=3, metric='euclidean').fit(coords)
    binned['cluster_id'] = db.labels_

    # Map back to parking dataset
    parking_df = parking_df.merge(binned[['lat_bin', 'lon_bin', 'cluster_id']], on=['lat_bin', 'lon_bin'], how='left')

    # Calculate summaries including vehicle ratios
    cluster_summary = parking_df[parking_df['cluster_id'] != -1].groupby('cluster_id').agg(
        center_lat=('latitude', 'mean'),
        center_lon=('longitude', 'mean'),
        violation_count=('id', 'count'),
        two_wheeler_count=('is_two_wheeler', 'sum'),
        helmet_count=('is_helmet', 'sum'),
        one_way_count=('is_one_way', 'sum'),
        plate_count=('is_plate', 'sum')
    ).reset_index()

    # Calculate two-wheeler percentage
    cluster_summary['two_wheeler_pct'] = (cluster_summary['two_wheeler_count'] / cluster_summary['violation_count']) * 100

    # Sort and keep top 60 hotspots
    top_hotspots = cluster_summary.sort_values(by='violation_count', ascending=False).head(60).copy()
    print("Querying OSM Overpass API for road features & POIs...")
    
    # 3. Retrieve Road classifications and POIs
    roads = []
    poi_counts = []
    poi_details = []

    for idx, row in top_hotspots.iterrows():
        lat, lon = row['center_lat'], row['center_lon']
        
        # Query road info
        road_info = get_osm_road_info(lat, lon)
        roads.append(road_info)
        
        # Query POIs
        pois = get_poi_info(lat, lon)
        poi_counts.append(len(pois))
        
        # Summarize POI detail string
        if len(pois) > 0:
            summary_str = ", ".join([f"{p['name']} ({p['type']})" for p in pois[:3]])
        else:
            summary_str = "None"
        poi_details.append(summary_str)
        
        # Sleep to be polite to Overpass (if not hit cache)
        # If cache hit, get_osm_road_info takes 0s, so we only sleep if querying
        # We can just do a tiny sleep
        time.sleep(0.1)

    save_cache()

    # Build details dataframe
    roads_df = pd.DataFrame(roads)
    top_hotspots = pd.concat([top_hotspots.reset_index(drop=True), roads_df], axis=1)
    top_hotspots['poi_count'] = poi_counts
    top_hotspots['poi_details'] = poi_details

    # 4. Boosted Traffic Disruption Index (TDI) Calculations
    highway_weights = {
        'motorway': 3.5, 'trunk': 3.5, 'primary': 3.0, 'secondary': 2.2, 
        'tertiary': 1.6, 'unclassified': 1.2, 'residential': 1.0, 
        'service': 0.8, 'living_street': 0.8
    }

    def compute_boosted_tdi(row):
        hw_type = str(row['highway']).split(';')[0].strip()
        road_weight = highway_weights.get(hw_type, 1.0)
        
        try:
            lanes_val = str(row['lanes']).split(';')[0]
            lanes = float(lanes_val)
            if lanes <= 0 or np.isnan(lanes):
                lanes = 2.0
        except ValueError:
            lanes = 2.0

        # Base score
        tdi_base = (row['violation_count'] * road_weight) / lanes
        
        # POI Multiplier calculation
        multiplier = 1.0
        details = str(row['poi_details']).lower()
        if 'hospital' in details:
            multiplier = 1.5
        elif 'subway_station' in details or 'bus_station' in details or 'transit' in details:
            multiplier = 1.3
        elif 'school' in details or 'college' in details or 'university' in details or 'mall' in details:
            multiplier = 1.1

        return tdi_base * multiplier

    top_hotspots['road_weight'] = top_hotspots['highway'].apply(lambda x: highway_weights.get(str(x).split(';')[0].strip(), 1.0))
    top_hotspots['tdi'] = top_hotspots.apply(compute_boosted_tdi, axis=1)
    
    # Sort by TDI
    top_hotspots = top_hotspots.sort_values(by='tdi', ascending=False)
    top_hotspots.to_csv(HOTSPOTS_FILE, index=False)
    print(f"Saved hotspots summary to {HOTSPOTS_FILE}")

    # 5. Extract hotspot-hourly aggregated trends
    print("Preparing hotspot-hourly trends dataset...")
    # Convert dates
    parking_df['created_datetime'] = pd.to_datetime(parking_df['created_datetime'], format='ISO8601')
    parking_df['hour'] = parking_df['created_datetime'].dt.hour
    parking_df['day_of_week'] = parking_df['created_datetime'].dt.dayofweek
    parking_df['month'] = parking_df['created_datetime'].dt.month
    parking_df['date'] = parking_df['created_datetime'].dt.date

    # Aggregating by cluster_id, date, month, day of week, hour
    hourly_trends = parking_df[parking_df['cluster_id'] != -1].groupby(
        ['cluster_id', 'date', 'month', 'day_of_week', 'hour']
    ).size().reset_index(name='violation_count')
    
    # Merge center coordinates into hourly trends for ML spatial features
    hourly_trends = hourly_trends.merge(
        top_hotspots[['cluster_id', 'center_lat', 'center_lon']], 
        on='cluster_id', 
        how='inner'
    )
    
    hourly_trends.to_csv(HOURLY_FILE, index=False)
    print(f"Saved hotspot-hourly trends to {HOURLY_FILE}")
    print("Preprocessing completed successfully!")

if __name__ == "__main__":
    download_data()
    preprocess_and_cluster()
