import pandas as pd
import numpy as np

def generate_csv_data(filepath="server_telemetry.csv"):
    print("Generating synthetic IT Server telemetry data...")
    np.random.seed(42)
    n_samples = 1500
    
    # Normal operating server data
    df = pd.DataFrame({
        "cpu_usage": np.random.normal(30, 10, n_samples),         # CPU usage %
        "memory_usage": np.random.normal(40, 15, n_samples),      # Memory usage %
        "disk_io_wait": np.random.normal(5, 2, n_samples),        # Disk I/O wait time ms
        "network_latency": np.random.normal(20, 5, n_samples)     # Network latency ms
    })
    
    # Inject anomalies representing struggling servers (High resource usage)
    df.loc[1300:1400] = df.loc[1300:1400] + [50, 40, 50, 100]
    # Inject anomalies representing failing servers (Spikes and freezes)
    df.loc[1400:] = df.loc[1400:] + [65, 55, 200, 500]
    
    # Clip values to realistic max (100% for cpu/memory)
    df["cpu_usage"] = df["cpu_usage"].clip(0, 100)
    df["memory_usage"] = df["memory_usage"].clip(0, 100)
    
    # Round all values to 2 decimal points
    df = df.round(2)
    
    df.to_csv(filepath, index=False)
    print(f"Successfully generated {n_samples} rows of data and saved to '{filepath}'.")

if __name__ == "__main__":
    generate_csv_data()
