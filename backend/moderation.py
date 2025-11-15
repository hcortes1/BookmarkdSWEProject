import re
from backend.gemini_helper import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Layer 1: Banned words list
BANNED_WORDS = [
    # Profanity
    'fuck', 'shit', 'bitch', 'ass', 'damn', 'hell', 'crap', 'piss',
    'bastard', 'cock', 'dick', 'pussy', 'cunt', 'whore', 'slut',
    
    # Racial slurs (partial list - add more as needed)
    'nigger', 'nigga', 'chink', 'spic', 'kike', 'wetback', 'gook',
    'towelhead', 'raghead', 'beaner',
    
    # Homophobic slurs
    'faggot', 'fag', 'dyke', 'tranny',"troon","travesti"
    
    # Other offensive terms
    'retard', 'retarded', 'rape', 'nazi'
]

# Allowlist - legitimate words that might get caught
ALLOWLIST = [
    'scunthorpe',  # Town name
    'arsenal',     # Football team
    'sussex',      # Place name
    'assassin',    # Legitimate word
    'classic',     # Contains 'ass'
    'dick',        # Name (Dick Francis, Philip K. Dick)
    'moby dick',   # Book title
    'passionate',  # Contains 'ass'
    'compass',     # Contains 'ass'
    'bass',        # Musical instrument
    'grass',       # Plant
    'bookmarkd',   # YOUR APP NAME! ← ADD THIS
    'bookmark',    # Related
    'pass'
]

# Common obfuscation patterns
OBFUSCATION_PATTERNS = {
    r'f+u+c+k+': 'fuck',
    r's+h+i+t+': 'shit',
    r'b+i+t+c+h+': 'bitch',
    r'a+s+s+': 'ass',
    r'n+i+g+g+e*r+': 'n-word',
    r'f\s*u\s*c\s*k': 'fuck',  # Spaces between letters
    r's\s*h\s*i\s*t': 'shit',
    r'f[@*!]ck': 'fuck',  # Symbol substitutions
    r'sh[@*!]t': 'shit',
    r'b[@*!]tch': 'bitch',
}


def normalize_text(text):
    """Normalize text for checking - lowercase, remove extra spaces"""
    return re.sub(r'\s+', ' ', text.lower().strip())


def check_allowList(text):
    """Check if text contains allowlisted phrases"""
    normalized = normalize_text(text)
    for allowed_phrase in ALLOWLIST:
        if allowed_phrase.lower() in normalized:
            return True
    return False


def detect_obfuscation(text):
    """Detect common obfuscation patterns"""
    normalized = normalize_text(text)
    
    for pattern, word in OBFUSCATION_PATTERNS.items():
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, word
    
    return False, None


def simple_text_filter(text):
    """
    Layer 1: Fast, hard-coded filter for obvious violations.
    
    Returns:
        tuple: (is_clean: bool, flagged_words: list)
    """
    if not text or not text.strip():
        return True, []
    
    normalized = normalize_text(text)
    flagged_words = []
    
    # Check allowlist first
    if check_allowList(text):
        return True, []
    
    # Check for obfuscation patterns
    has_obfuscation, obfuscated_word = detect_obfuscation(text)
    if has_obfuscation:
        flagged_words.append(obfuscated_word)
    
    # Check banned words
    for banned_word in BANNED_WORDS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(banned_word) + r'\b'
        if re.search(pattern, normalized, re.IGNORECASE):
            flagged_words.append(banned_word)
    
    is_clean = len(flagged_words) == 0
    return is_clean, flagged_words


def ai_content_moderation(text, context="general"):
    """
    Layer 2: AI moderation with context awareness.
    
    Args:
        text: Text to moderate
        context: "review", "profile", "username", "recommendation", "general"
    
    Returns:
        tuple: (is_approved: bool, reason: str)
    """
    
    # Context-specific instructions
    if context == "review":
        content_description = "a book review"
        reject_criteria = """
- Hate speech or discriminatory content
- Spam patterns (repeated characters, promotional links)
- Threats or harassment
- Content completely unrelated to books
"""
    elif context == "profile":
        content_description = "a user profile bio"
        reject_criteria = """
- Hate speech or discriminatory content
- Spam patterns (repeated characters, promotional links)
- Threats or harassment
- Explicit sexual content
"""
    elif context == "username":
        content_description = "a username"
        reject_criteria = """
- Hate speech or discriminatory content
- Impersonation attempts
- Explicit sexual content
"""
    elif context == "recommendation":
        content_description = "a book recommendation message"
        reject_criteria = """
- Hate speech or discriminatory content
- Spam patterns (repeated characters, promotional links)
- Threats or harassment
"""
    else:
        content_description = "user-generated content"
        reject_criteria = """
- Hate speech or discriminatory content
- Spam patterns
- Threats or harassment
"""
    
    system_instruction = f"""
You are a content moderator for a book social platform.

Review the user's text which is {content_description}.

REJECT if the text contains:
{reject_criteria}

APPROVE if:
- It's genuine user-generated content
- It doesn't violate the above criteria
- For profiles: any reasonable bio is acceptable
- For usernames: any reasonable name is acceptable

Respond ONLY in valid JSON format:
{{
  "approved": true,
  "reason": ""
}}
OR
{{
  "approved": false,
  "reason": "Brief specific explanation"
}}
"""

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=system_instruction
        )
        
        response = model.generate_content(f"Moderate this {content_description}: {text}")
        response_text = response.text.strip()
        
        # Try to parse JSON response
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        is_approved = result.get('approved', False)
        reason = result.get('reason', 'Content flagged by AI moderation')
        
        return is_approved, reason
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response was: {response_text}")
        return True, ""
    except Exception as e:
        print(f"AI moderation error: {e}")
        return True, ""


def moderate_review(text, context="general"):
    """
    Two-layer moderation system with context awareness.
    
    Args:
        text: The text to moderate
        context: "review", "profile", "username", "recommendation"
    
    Returns:
        tuple: (is_approved: bool, reason: str, layer: str)
    """
    if not text or not text.strip():
        return True, "", "none"
    
    print(f"DEBUG MODERATION: Checking text: '{text}' (context: {context})")
    
    # Layer 1: Simple text filter (fast) - same for all contexts
    is_clean, flagged_words = simple_text_filter(text)
    
    print(f"DEBUG MODERATION: Layer 1 result - is_clean: {is_clean}, flagged_words: {flagged_words}")
    
    if not is_clean:
        reason = "Your content contains inappropriate language. Please revise and try again."
        return False, reason, "simple"
    
    # Layer 2: AI moderation - context-specific
    is_approved, ai_reason = ai_content_moderation(text, context)
    
    print(f"DEBUG MODERATION: Layer 2 result - is_approved: {is_approved}, reason: '{ai_reason}'")
    
    if not is_approved:
        return False, ai_reason, "ai"
    
    print(f"DEBUG MODERATION: PASSED both layers")
    return True, "", "none"