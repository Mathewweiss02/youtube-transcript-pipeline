"""
Guest Extractor for Wiki Pipeline
Detects guests in interview episodes.
"""
import re
import os
import openai
import json
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class GuestExtractor:
    """Extract guest names from episode titles and content."""
    
    # Common patterns for guest mentions in titles
    PATTERNS = [
        r'with\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',      # "with John Smith"
        r'featuring\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)', # "featuring John Smith"  
        r'guest\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',     # "guest John Smith"
        r'joined\s+by\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)', # "joined by John Smith"
        r'ft\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',      # "ft. John Smith"
        r'featuring:\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)', # "featuring: John Smith"
        r'w/\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',         # "w/ John Smith"
        r'interview\s+with\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',  # "interview with John Smith"
    ]
    
    # Solo indicators (no guest)
    SOLO_INDICATORS = [
        'solo episode', 'me talking', 'i discuss', 'my thoughts',
        'monologue', 'solo show', 'just me'
    ]
    
    def __init__(self, api_key: str = None, use_llm: bool = True):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_llm = use_llm and self.api_key is not None
        
        if self.use_llm:
            self.client = openai.OpenAI(api_key=self.api_key)
        
        self.cache = {}
    
    def extract_pattern(self, title: str) -> Optional[str]:
        """Extract guest using regex patterns."""
        title_lower = title.lower()
        
        # Check if explicitly solo
        for indicator in self.SOLO_INDICATORS:
            if indicator in title_lower:
                return None
        
        # Try patterns
        for pattern in self.PATTERNS:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                guest = match.group(1).strip()
                # Filter out false positives (common words)
                if len(guest) > 3 and ' ' in guest:
                    return guest
        
        return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    def extract_llm(self, title: str, transcript_preview: str) -> Optional[str]:
        """LLM fallback for ambiguous cases."""
        if not self.use_llm:
            return None
        
        prompt = f"""Does this episode have a guest being interviewed?

Look at the title and transcript preview. If there's someone being interviewed (not the host), return their full name. If it's solo content or unclear, return null.

Title: {title}

Transcript Preview:
{transcript_preview[:600]}

Return JSON: {{"guest": "Full Name" or null}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            guest = result.get('guest')
            
            if guest and len(guest) > 3:
                return guest.strip()
            return None
            
        except Exception as e:
            print(f"LLM guest extraction error: {e}")
            return None
    
    def extract(self, title: str, transcript_preview: str = "") -> Optional[str]:
        """
        Extract guest name from episode.
        
        Strategy:
        1. Try regex patterns on title (fast, cheap)
        2. If ambiguous, use LLM (slower, costs money)
        """
        # Check cache
        cache_key = f"{title}:{hash(transcript_preview[:100])}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try pattern matching first
        guest = self.extract_pattern(title)
        
        # If no match and we have transcript, try LLM
        if not guest and transcript_preview and self.use_llm:
            guest = self.extract_llm(title, transcript_preview)
        
        # Cache result
        self.cache[cache_key] = guest
        
        return guest


if __name__ == '__main__':
    # Test cases
    test_cases = [
        "How to Build Muscle with Dr. Mike Israetel",
        "Testosterone Optimization featuring Andrew Huberman",
        "My Solo Thoughts on Current Events",
        "Interview with David Goggins on Mental Toughness",
        "Nutrition Deep Dive ft. Layne Norton",
        "Why I'm Taking a Break (Solo Episode)",
    ]
    
    extractor = GuestExtractor()
    
    for title in test_cases:
        guest = extractor.extract(title, "")
        print(f"{title[:50]}... -> {guest or 'No guest'}")
