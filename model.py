import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
HOURLY_FILE = os.path.join("data", "hourly_trends.csv")
MODEL_FILE = os.path.join("data", "predictor.pkl")

def train_model():
    if not os.path.exists(HOURLY_FILE):
        print(f"Error: {HOURLY_FILE} not found. Run preprocess.py first.")
        return

    print("Loading hotspot-hourly trends...")
    df = pd.read_csv(HOURLY_FILE)
    print(f"Loaded {len(df)} hotspot-hourly records.")

    # 1. Feature Engineering
    # We predict the violation count based on Coordinates, Month, Day of Week, and Hour
    X = df[['center_lat', 'center_lon', 'month', 'day_of_week', 'hour']]
    y = df['violation_count']

    # 2. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Model Training
    print("Training Granular Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 4. Evaluation
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Granular Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} violations/hour")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} violations/hour")
    print(f"R² Score: {r2:.4f}")
    print("---------------------------------\n")

    # 5. Train final model on full dataset
    print("Training final granular model on full dataset...")
    final_model = RandomForestRegressor(n_estimators=100, max_depth=14, random_state=42, n_jobs=-1)
    final_model.fit(X, y)

    # 6. Save model
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(final_model, f)
    print(f"Granular Model saved successfully to {MODEL_FILE}")

if __name__ == "__main__":
    train_model()
