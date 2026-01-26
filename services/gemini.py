import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_gemini_llm():
    """Initialize and return Gemini LLM with proper model"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
