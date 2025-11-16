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


def get_book_recommendation_chat(user_message, user_genres=None, chat_history=None):
    """
    Get book recommendations and answer questions based on user preferences.

    Args:
        user_message: The user's question or statement
        user_genres: List of user's favorite genres from database
        chat_history: Previous conversation (optional)

    Returns:
        tuple: (success, response_text)
    """

    # Build system instruction with user's preferences
    genre_context = ""
    if user_genres and len(user_genres) > 0:
        genre_context = f"\nThe user's favorite genres are: {', '.join(user_genres)}. Use this to personalize recommendations."

    system_instruction = f"""
You are a knowledgeable book recommendation assistant helping readers discover their next great book.

Your capabilities:
1. Recommend books based on user preferences and favorite genres
2. Answer questions about books, authors, and literary topics
3. Help users explore new genres and authors
4. Provide spoiler-free summaries

Guidelines:
- Recommend ONLY ONE book per response
- Start directly with the recommendation - no need for "Okay!" or "Based on your interest"
- Format: **"Title" by Author** - Provide 2-3 descriptive sentences about the book without spoilers
- On a new line, ask if they'd like another recommendation or need more help
- All book and author names must be real
- Be conversational and enthusiastic about reading
- If asked about specific books, provide accurate information
{genre_context}
"""

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=system_instruction
        )

        response = model.generate_content(user_message)
        response_text = response.text

        return True, response_text

    except Exception as e:
        print(f"Error: {e}")
        return False, f"Error: {e}"


def select_books_from_list(book_titles, user_genres, limit=10):
    """
    Select books from a provided list that match user's favorite genres.
    Returns only book titles, one per line.

    Args:
        book_titles: List of book titles to choose from
        user_genres: List of user's favorite genres
        limit: Maximum number of books to return

    Returns:
        tuple: (success, titles_text) where titles_text is newline-separated titles
    """
    
    if not book_titles or not user_genres:
        return False, ""
    
    # Build a simple list of titles for the AI
    titles_list = "\n".join(book_titles)
    
    system_instruction = f"""
You are a book selection assistant. Your ONLY job is to select books from the provided list that best match the user's favorite genres.

User's favorite genres: {', '.join(user_genres)}

Rules:
1. Select EXACTLY {limit} books from the list
2. Choose books that best match the user's genres
3. Output ONLY the exact book titles, one per line
4. Do NOT add any commentary, explanations, or formatting
5. Do NOT add numbers, bullets, or any prefixes
6. Use the EXACT title as provided in the list
"""

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=system_instruction
        )

        prompt = f"From this list of books, select {limit} titles that best match these genres: {', '.join(user_genres)}\n\nBooks:\n{titles_list}"
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        return True, response_text

    except Exception as e:
        print(f"Error in select_books_from_list: {e}")
        return False, ""
