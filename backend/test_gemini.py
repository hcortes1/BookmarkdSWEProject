from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv("GEMINI_API_KEY")

# Check if key was loaded
# if api_key:
#     print(f"API Key loaded successfully!")
#     print(f"Key preview: {api_key[:20]}...")
# else:
#     print("API Key not found in .env file!")
#     exit()

# Configure Gemini with your API key
genai.configure(api_key=api_key)

# # Create the model
# print("\n📚 Testing Gemini API...\n")

try:
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction="Always respond straight to the point. You are a robot no need to be friendly just give the answer without additional jargon or descriptions. Do not use descriptive words about the books that are up to personal opinions. Be neutral. All recommendations must be existing books and the authors must be real people. After the book name and author, give a short spoiler free summary of the book in 1-2 descriptive sentences."
    )
    response = model.generate_content(
        "Recommend me one sci-fi book. I like the red rising series, project hail mary by andy weir, and the bobiverse series by dennis e. taylor.")

    # print("SUCCESS! Gemini is working!\n")
    print("Bot Response:")
    print(response.text)

except Exception as e:
    print(f"Error: {e}")
