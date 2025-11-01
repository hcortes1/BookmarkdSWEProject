from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_genre_recommendation(user_message, chat_history=None):
    """
    Get genre recommendations from Gemini based on user input.
    
    Args:
        user_message: The user's question or statement
        chat_history: Previous conversation (optional)
    
    Returns:
        tuple: (success, response_text, suggested_genres)
    """
    
    # TODO: Create the model with system instructions
    # TODO: Send the message
    # TODO: Parse response for genre names
    # TODO: Return response and suggested genres
    
    pass