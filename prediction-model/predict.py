import os
import pandas as pd
import joblib

MODEL_DIR = "models"

class RiskPredictor:
    def __init__(self):
        """Loads all the trained models and scalers into memory."""
        self.iso_model = joblib.load(os.path.join(MODEL_DIR, "isolation_forest.joblib"))
        self.scaler = joblib.load(os.path.join(MODEL_DIR, "anomaly_scaler.joblib"))
        self.xgb_model = joblib.load(os.path.join(MODEL_DIR, "xgboost_risk_classifier.joblib"))
        self.label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))

    def predict(self, cpu_usage: float, memory_usage: float, disk_io_wait: float, network_latency: float) -> dict:
        """
        Takes server telemetry inputs and returns the predicted risk level and anomaly score.
        """
        # Create a DataFrame for the single input row
        input_data = pd.DataFrame({
            "cpu_usage": [cpu_usage],
            "memory_usage": [memory_usage],
            "disk_io_wait": [disk_io_wait],
            "network_latency": [network_latency]
        })
        
        # 1. Generate Anomaly Score
        raw_score = -self.iso_model.score_samples(input_data)
        normalized_score = self.scaler.transform(raw_score.reshape(-1, 1)).flatten()[0]
        
        # Add score to input data so the XGBoost model can use it if we trained on it
        # Wait, in the training script we trained the XGBoost classifier on the features, NOT the score!
        # Let's double check what we trained XGBoost on in train.py:
        # X = df[features] (where features = ["cpu_usage", "memory_usage", "disk_io_wait", "network_latency"])
        # So XGBoost only needs the 4 base features.
        
        # 2. Predict Risk Class
        predicted_class_encoded = self.xgb_model.predict(input_data)
        predicted_risk = self.label_encoder.inverse_transform(predicted_class_encoded)[0]
        
        # 3. Get prediction probabilities
        probabilities = self.xgb_model.predict_proba(input_data)[0]
        prob_dict = {
            self.label_encoder.inverse_transform([i])[0]: float(prob) 
            for i, prob in enumerate(probabilities)
        }
        
        return {
            "predicted_risk": predicted_risk,
            "anomaly_score": float(normalized_score),
            "probabilities": prob_dict
        }

if __name__ == "__main__":
    # Example Usage
    print("Testing Risk Predictor with sample telemetry...\n")
    try:
        predictor = RiskPredictor()
        
        # Normal server example
        normal_server = predictor.predict(cpu_usage=25.0, memory_usage=30.0, disk_io_wait=2.5, network_latency=15.0)
        print("Normal Server Prediction:")
        print(normal_server)
        
        print("-" * 40)
        
        # Struggling server example
        struggling_server = predictor.predict(cpu_usage=85.0, memory_usage=90.0, disk_io_wait=55.0, network_latency=120.0)
        print("Struggling Server Prediction:")
        print(struggling_server)
        
    except Exception as e:
        print(f"Error loading models: {e}\nPlease run 'python train.py' first to generate the models.")
