"""
Topic Extractor for Wiki Pipeline
Extracts specific topics from transcripts using GPT-4 mini.
"""
import os
import json
import openai
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential


class TopicExtractor:
    """Extract topics from transcript content using LLM."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        self.cache = {}  # Simple in-memory cache
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    def extract(self, title: str, transcript_preview: str) -> List[str]:
        """
        Extract topics from episode.
        
        Args:
            title: Video title
            transcript_preview: First ~1000 chars of transcript
        
        Returns:
            List of topic strings
        """
        # Check cache
        cache_key = f"{title}:{hash(transcript_preview[:200])}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        prompt = f"""Analyze this video title and transcript preview. Extract 5-10 specific, concrete topics discussed.

Guidelines:
- Be specific: "testosterone optimization" not just "health"
- Include concrete methods, techniques, or concepts
- Avoid generic terms like "video", "episode", "discussion"
- Topics should be searchable and meaningful
- Each topic should be 1-4 words maximum

Title: {title}

Transcript Preview (first 800 chars):
{transcript_preview[:800]}

Return ONLY a JSON array of topic strings:
{{"topics": ["topic1", "topic2", "topic3", "topic4", "topic5"]}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract specific, concrete topics from video content. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            topics = result.get('topics', [])
            
            # Clean topics
            topics = [t.strip().lower() for t in topics if t.strip()]
            
            # Cache result
            self.cache[cache_key] = topics
            
            return topics
            
        except Exception as e:
            print(f"Topic extraction error: {e}")
            return []
    
    def extract_batch(self, episodes: List[dict]) -> List[List[str]]:
        """Extract topics for multiple episodes."""
        results = []
        for ep in episodes:
            topics = self.extract(ep['title'], ep.get('transcript_preview', ''))
            results.append(topics)
        return results


if __name__ == '__main__':
    # Test topic extraction
    test_title = "How to 2x Your Natural Testosterone"
    test_preview = """What is going on guys? Today we're going to talk about 
    how to naturally increase your testosterone levels. The first thing you 
    need to understand is that sleep is absolutely crucial. Most of your 
    testosterone is produced during deep sleep. Next, let's talk about diet. 
    You need to eat enough cholesterol from eggs and animal fats. Finally, 
    resistance training stimulates testosterone production."""
    
    extractor = TopicExtractor()
    topics = extractor.extract(test_title, test_preview)
    
    print(f"Title: {test_title}")
    print(f"Extracted topics: {topics}")
