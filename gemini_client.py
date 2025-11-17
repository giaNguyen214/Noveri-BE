import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

# Tạo 1 instance duy nhất của model
model = GenerativeModel("gemini-2.5-pro")
