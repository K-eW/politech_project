from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")

OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")
AI_MODEL = 'gpt-oss:120b-cloud'