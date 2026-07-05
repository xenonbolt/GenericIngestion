# Headroom AI Proxy Environment

This folder contains a completely isolated environment for running the Headroom AI proxy. 
By keeping this isolated, we prevent any dependency conflicts with the main backend's `langchain` and `httpx` versions.

## Setup Instructions

1. **Open a new terminal** and navigate to this folder:
   ```bash
   cd d:\Workspace\Hackathon\GenericIngestion\headroom
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows (PowerShell):
     ```bash
     .\venv\Scripts\activate.ps1
     ```
   - Windows (Command Prompt):
     ```bash
     .\venv\Scripts\activate.bat
     ```

4. **Install Headroom**:
   ```bash
   python -m pip install -r requirements.txt
   ```

## Running the Proxy

Whenever you want to start the chatbot backend, you must also start this proxy in a separate terminal tab.

Make sure your virtual environment is activated (`(venv)` appears in your terminal prompt), then run:

```bash
headroom proxy --port 8787
```

Your backend `chatbot.py` is already configured to automatically route requests to `http://127.0.0.1:8787` when `LLM_PROVIDER="openai"`.
