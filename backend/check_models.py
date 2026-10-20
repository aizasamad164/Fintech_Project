# backend/check_models.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("ERROR: GROQ_API_KEY is not set in backend/.env")
else:
    client = Groq(api_key=api_key)
    try:
        models = client.models.list()
        print("\nAvailable Groq Model IDs for your API Key:")
        for model in models.data:
            print(f"  • {model.id}")
    except Exception as e:
        print(f"Error listing models: {e}")