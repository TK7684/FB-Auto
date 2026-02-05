"""
Shared filtering utilities for D Plus Skin Facebook Bot.
"""
from typing import List

# Negative keywords for filtering out irrelevant posts (e.g. real estate)
NEGATIVE_KEYWORDS = [
    "#คุณก้งขายบ้าน", 
    "ขายบ้าน", 
    "#ขายบ้าน",
    "ทาวน์โฮม", 
    "บ้านเดี่ยว",
    "อาคารพาณิชย์"
]

# Users to ignore (e.g., specific admins or spammers)
IGNORED_USERS = [
    "Treepehch Kwangkhwang"
]

def is_ignored_user(name: str) -> bool:
    """
    Check if the user is in the ignored list.
    
    Args:
        name (str): The user's name.
        
    Returns:
        bool: True if user should be ignored.
    """
    if not name:
        return False
        
    return name in IGNORED_USERS

def is_relevant_post(text: str) -> bool:
    """
    Check if the post is relevant to the product line.
    Returns False if it matches negative keywords (e.g. real estate).
    
    Args:
        text (str): The post content or message.
        
    Returns:
        bool: True if relevant, False if it contains negative keywords.
    """
    if not text:
        return True
    
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in NEGATIVE_KEYWORDS):
        return False
        
    return True
