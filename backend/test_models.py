import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {api_key is not None}")
if api_key:
    print(f"Key starts with: {api_key[:5]}... (length: {len(api_key)})")

genai.configure(api_key=api_key)

try:
    print("\nListing available models:")
    for model in genai.list_models():
        print(f"  - {model.name} (supports: {model.supported_generation_methods})")
except Exception as e:
    print(f"Error listing models: {e}")
