# Asset Risk Forecasting & Outage Prevention

This module contains the machine learning pipeline used to predict IT Server outage risks based on server telemetry. It implements a two-phase ML approach:
1. **Anomaly Detection** (Isolation Forest) to identify irregular server behavior.
2. **Risk Classification** (XGBoost) to classify the server's current state into `LOW`, `Medium`, or `HIGH` risk of outage.

## 📂 Project Structure
- `generate_data.py`: A utility script that generates synthetic server telemetry data (`cpu_usage`, `memory_usage`, `disk_io_wait`, `network_latency`) and injects realistic anomalies.
- `train.py`: The training pipeline. It reads the CSV data, trains both the Isolation Forest and the XGBoost classifier, and saves the trained models to the local `models/` directory.
- `predict.py`: The inference engine. It loads the pre-trained models from the `models/` directory and exposes a `RiskPredictor` class to make real-time predictions on live telemetry.
- `requirements.txt`: Python dependencies required for this module.

---

## 🧠 Models Used

### 1. Isolation Forest (Anomaly Detection)
- **Type**: Unsupervised Learning
- **Library**: `scikit-learn`
- **Purpose**: Detects statistical outliers across multi-dimensional telemetry data (CPU, memory, etc.) without requiring pre-labeled outage data. 
- **How it works**: It isolates anomalous observations by randomly selecting a feature and splitting the data. Anomalies require fewer random partitions to be isolated compared to normal data points, allowing the model to flag irregular server behavior early.

### 2. XGBoost (Risk Classifier)
- **Type**: Supervised Multi-class Classification
- **Library**: `xgboost`
- **Purpose**: Maps the server's telemetry features to a specific categorical risk tier (`LOW`, `Medium`, `HIGH`).
- **How it works**: Uses a robust gradient-boosted decision tree framework (optimized with `multi:softprob` objective). It evaluates the complex, non-linear relationships between server metrics to calculate the exact probability of an impending outage.

---

## 🔄 Data & Execution Flow

### 1. Data Ingestion (Training)
The pipeline begins by loading historical IT server telemetry (e.g., `cpu_usage`, `memory_usage`, `disk_io_wait`, `network_latency`) from `server_telemetry.csv`.

### 2. Phase 1: Anomaly Scoring
The raw telemetry is fed into the **Isolation Forest** model. The model identifies statistical outliers and returns an anomaly score. 
- A `MinMaxScaler` is then used to normalize these scores strictly between `0.0` (Normal) and `1.0` (Highly Anomalous).
- Based on these scores, the data is automatically labeled into categorical Risk Levels:
  - `LOW` (score < 0.4)
  - `Medium` (0.4 <= score < 0.7)
  - `HIGH` (score >= 0.7)

### 3. Phase 2: Risk Classifier Training
With the data now properly labeled with Risk Levels, the **XGBoost Classifier** is trained. It learns to predict the categorical Risk Level (`LOW`, `Medium`, `HIGH`) directly from the raw telemetry inputs, effectively learning the patterns of server failure.

### 4. Phase 3: Real-Time Inference
In a production setting, `predict.py` takes live incoming telemetry data for a single server. It bypasses the labeling rules and directly feeds the raw metrics into the trained XGBoost model, returning instantaneous risk predictions and exact probabilities.

---

## 🚀 Setup Instructions

1. **Create a Virtual Environment:**
   It is highly recommended to run this within an isolated virtual environment.
   ```bash
   python -m venv venv
   ```
2. **Activate the Environment:**
   - **Windows:** `.\venv\Scripts\activate`
   - **Mac/Linux:** `source venv/bin/activate`
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠️ Usage

### 1. Generate Synthetic Data
Run the data generator to create your `server_telemetry.csv` file. 
*(Note: You can skip this step if you have your own real `server_telemetry.csv` with the required columns).*
```bash
python generate_data.py
```

### 2. Train the Models
Run the training script to build the ML models. This will generate a `models/` folder containing the saved `.joblib` model artifacts.
```bash
python train.py
```

### 3. Run Predictions (Inference)
You can test the prediction engine directly by running the script.
```bash
python predict.py
```
To use the prediction engine in your own application (e.g., inside a FastAPI route or a background worker):

```python
from predict import RiskPredictor

# Initialize the predictor (loads models into memory)
predictor = RiskPredictor()

# Pass telemetry variables to get a prediction
result = predictor.predict(
    cpu_usage=85.0, 
    memory_usage=90.0, 
    disk_io_wait=55.0, 
    network_latency=120.0
)

print(result)
```

**Example Output:**
```json
{
    "predicted_risk": "Medium",
    "anomaly_score": 0.656,
    "probabilities": {
        "HIGH": 0.278,
        "LOW": 0.005,
        "Medium": 0.716
    }
}
```
