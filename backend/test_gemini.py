from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv("GEMINI_API_KEY")

# Check if key was loaded
if api_key:
    print(f"API Key loaded successfully!")
    print(f"Key preview: {api_key[:20]}...")
else:
    print("API Key not found in .env file!")
    exit()

# Configure Gemini with your API key
genai.configure(api_key=api_key)

# Create the model
print("\n📚 Testing Gemini API...\n")

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Recommend me one sci-fi book in one sentence.")
    
    print("SUCCESS! Gemini is working!\n")
    print("Bot Response:")
    print(response.text)
    
except Exception as e:
    print(f"Error: {e}")