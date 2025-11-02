from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Define the genre list - THIS WAS MISSING!
GENRES = [
    "Mystery",
    "Thriller/Suspense",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Horror",
    "Historical Fiction",
    "Biography/Memoir",
    "Self-Help",
    "History"
]

def get_genre_recommendation(user_message, chat_history=None):
    """
    Get genre recommendations from Gemini based on user input.
    
    Args:
        user_message: The user's question or statement
        chat_history: Previous conversation (optional)
    
    Returns:
        tuple: (success, response_text, suggested_genres)
    """
    
    try:
        # Create the model with system instructions
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction="""
You are a friendly reading assistant helping users discover their favorite book genres.

Available genres to suggest:
Mystery, Thriller/Suspense, Romance, Science Fiction, Fantasy, Horror, Historical Fiction, Biography/Memoir, Self-Help, History

Your goals:
1. Help users identify which genres match their interests
2. When you recommend a genre, use its EXACT name from the list above
3. Ask follow-up questions to narrow down preferences
4. Be conversational and encouraging

Guidelines:
- Keep responses to 2-3 sentences
- When mentioning a genre from the list, put it in **bold** like **Mystery** or **Science Fiction**
- If a user mentions books they like, suggest matching genres
- If they're unsure, ask about preferences (real vs imaginary, past vs future, scary vs romantic, etc.)
"""
        )
        
        # Generate response and extract text - THIS WAS MISSING!
        response = model.generate_content(user_message)
        response_text = response.text
        
        # Parse response for genre names
        suggested_genres = []
        for genre in GENRES:
            # Check if the genre name appears in the response
            if genre in response_text:
                # Add it to our list (but avoid duplicates)
                if genre not in suggested_genres:
                    suggested_genres.append(genre)
        
        # Return success, the AI's response, and list of suggested genres
        return True, response_text, suggested_genres
        
    except Exception as e:
        print(f"Error: {e}")
        return False, f"Error: {e}", []