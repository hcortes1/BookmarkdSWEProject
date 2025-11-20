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
        tuple: (is_approved: bool, reason: str, violation_type: str)
    """
    
    # Context-specific instructions
    if context == "review":
        content_description = "a book review"
        reject_criteria = """
REJECT ONLY if the text contains:
1. SEVERE hate speech or explicit discriminatory content
2. OBVIOUS spam (e.g., "click here", repeated URLs, "buy now", external links)
3. Direct threats or targeted harassment
4. Content completely unrelated to books

PROMOTIONAL CONTENT - Flag as "promotional" if:
- Contains promotional language like "check out my book", "buy my book", "visit my site"
- Includes multiple external links or website URLs
- Self-promotion of the reviewer's own work

BE LENIENT with:
- Strong opinions (even negative ones) about books are allowed
- Casual language and slang
- Criticism of books, authors, or genres
- Personal reading experiences and preferences
"""
    elif context == "profile":
        content_description = "a user profile bio"
        reject_criteria = """
REJECT ONLY if the text contains:
1. SEVERE hate speech or explicit discriminatory content
2. OBVIOUS spam or promotional links
3. Direct threats or harassment

PROMOTIONAL CONTENT - Flag as "promotional" if:
- Contains business promotion or advertising
- User is telling someone to buy their book or buy their service
- Multiple external links or website URLs
- Selling products or services

BE LENIENT with:
- Any reasonable personal bio
- Mentioning favorite books or authors
- Links to social media or personal blogs (1-2 links is fine)
- Creative or quirky bios
"""
    elif context == "username":
        content_description = "a username"
        reject_criteria = """
REJECT ONLY if the username:
1. Contains hate speech or slurs
2. Is clearly impersonating someone else (e.g., "officialCEO", "realAuthorName")
3. Contains explicit sexual content

BE LENIENT with:
- Creative or unusual names
- References to books, characters, or authors
- Numbers, underscores, or special characters
"""
    elif context == "recommendation":
        content_description = "a book recommendation message"
        reject_criteria = """
REJECT ONLY if the text contains:
1. SEVERE hate speech or explicit discriminatory content
2. OBVIOUS spam patterns
3. Direct threats or harassment

BE LENIENT with:
- Enthusiastic book recommendations
- Strong opinions about books
- Personal anecdotes related to reading
"""
    else:
        content_description = "user-generated content"
        reject_criteria = """
REJECT ONLY if the text contains:
1. SEVERE hate speech or explicit discriminatory content
2. OBVIOUS spam patterns
3. Direct threats or harassment

BE LENIENT with:
- Casual language and opinions
- Criticism and debate
- Personal experiences
"""
    
    system_instruction = f"""
You are a content moderator for a book social platform. Your goal is to create a welcoming community while being LENIENT with genuine users.

Review this {content_description}.

{reject_criteria}

IMPORTANT: Be lenient and assume good intent. Most content should be APPROVED.

Respond ONLY in valid JSON format:

If APPROVED:
{{
  "approved": true,
  "violation_type": "none",
  "reason": ""
}}

If REJECTED for promotional content:
{{
  "approved": false,
  "violation_type": "promotional",
  "reason": "Brief explanation"
}}

If REJECTED for other reasons:
{{
  "approved": false,
  "violation_type": "inappropriate",
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
        violation_type = result.get('violation_type', 'inappropriate')
        reason = result.get('reason', 'Content flagged by moderation')
        
        return is_approved, reason, violation_type
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response was: {response_text}")
        return True, "", "none"
    except Exception as e:
        print(f"AI moderation error: {e}")
        return True, "", "none"


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
    is_approved, ai_reason, violation_type = ai_content_moderation(text, context)
    
    print(f"DEBUG MODERATION: Layer 2 result - is_approved: {is_approved}, violation_type: '{violation_type}', reason: '{ai_reason}'")
    
    if not is_approved:
        # Customize the message based on violation type
        if violation_type == "promotional":
            final_reason = "This content appears to be promotional. Please keep your posts focused on genuine book discussions and recommendations."
        else:
            final_reason = ai_reason if ai_reason else "Your content violates our community guidelines. Please revise and try again."
        
        return False, final_reason, "ai"
    
    print(f"DEBUG MODERATION: PASSED both layers")
    return True, "", "none"