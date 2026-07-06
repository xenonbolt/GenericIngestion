import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_models(csv_file="server_telemetry.csv"):
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run 'generate_data.py' first.")
        return

    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    features = ["cpu_usage", "memory_usage", "disk_io_wait", "network_latency"]
    X = df[features]

    # 1. Train Isolation Forest
    print("\n--- Training Isolation Forest ---")
    iso_model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_model.fit(X)
    
    joblib.dump(iso_model, os.path.join(MODEL_DIR, "isolation_forest.joblib"))
    print("Saved Isolation Forest model.")

    # Generate scores and normalize
    raw_scores = -iso_model.score_samples(X)
    scaler = MinMaxScaler(feature_range=(0, 1))
    normalized_scores = scaler.fit_transform(raw_scores.reshape(-1, 1)).flatten()
    
    joblib.dump(scaler, os.path.join(MODEL_DIR, "anomaly_scaler.joblib"))
    df["anomaly_score"] = normalized_scores

    # Map to risk levels
    def determine_risk(score):
        if score < 0.4: return "LOW"
        elif score < 0.7: return "Medium"
        else: return "HIGH"
            
    df["risk_level"] = df["anomaly_score"].apply(determine_risk)
    print("\nRisk Level Distribution:")
    print(df["risk_level"].value_counts())

    # 2. Train Risk Classifier
    print("\n--- Training Risk Classifier (XGBoost) ---")
    y = df["risk_level"]
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "label_encoder.joblib"))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    xgb_model = xgb.XGBClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42, 
        objective='multi:softprob',
        num_class=len(label_encoder.classes_)
    )
    xgb_model.fit(X_train, y_train)
    
    # Evaluation
    print("Evaluating Model on Test Data...")
    y_pred = xgb_model.predict(X_test)
    y_test_labels = label_encoder.inverse_transform(y_test)
    y_pred_labels = label_encoder.inverse_transform(y_pred)
    
    print(f"Accuracy: {accuracy_score(y_test_labels, y_pred_labels):.4f}")
    print("Classification Report:\n", classification_report(y_test_labels, y_pred_labels))
    
    joblib.dump(xgb_model, os.path.join(MODEL_DIR, "xgboost_risk_classifier.joblib"))
    print("Saved XGBoost Risk Classifier model.")
    print("Training complete!")

if __name__ == "__main__":
    train_models()
