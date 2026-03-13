#!/usr/bin/env python3
"""
Deep analysis of uncategorized Mark Bell videos with systematic classification.
"""
import os
import json
import re
from collections import Counter
from typing import Dict, List, Tuple, Set
from datetime import datetime

def load_categorized_data():
    """Load the categorized video data."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, "mark_bell_categorized.json"), 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    match = re.search(r'v=([^&]+)', url)
    return match.group(1) if match else None

def analyze_title_patterns(title):
    """Extract various patterns and features from title."""
    features = {
        'has_guest': False,
        'has_number': False,
        'has_question': False,
        'has_episode': False,
        'word_count': len(title.split()),
        'has_expert_terms': False,
        'has_action_words': False,
        'caps_ratio': sum(1 for c in title if c.isupper()) / len(title) if title else 0
    }
    
    # Check for guest indicators
    guest_patterns = [
        r'\bfeat\.?\b', r'\bfeaturing\b', r'\bwith\b', r'\bft\.?\b',
        r'\bdr\.?\b', r'\bexpert\b', r'\bspecialist\b', r'\bcoach\b'
    ]
    features['has_guest'] = any(re.search(pattern, title, re.IGNORECASE) for pattern in guest_patterns)
    
    # Check for numbers
    features['has_number'] = bool(re.search(r'\d+', title))
    
    # Check for questions
    features['has_question'] = '?' in title or any(word in title.lower() for word in ['why', 'what', 'how', 'when', 'where', 'who'])
    
    # Check for episode indicators
    episode_patterns = [r'\bep\.?\s*\d+', r'\bepisode\s*\d+', r'\b#\d+']
    features['has_episode'] = any(re.search(pattern, title, re.IGNORECASE) for pattern in episode_patterns)
    
    # Check for expert/technical terms
    expert_terms = [
        'science', 'research', 'study', 'data', 'analysis', 'protocol',
        'mechanism', 'systematic', 'clinical', 'evidence', 'mechanism'
    ]
    features['has_expert_terms'] = any(term in title.lower() for term in expert_terms)
    
    # Check for action words
    action_words = [
        'build', 'boost', 'increase', 'decrease', 'optimize', 'maximize',
        'improve', 'enhance', 'transform', 'elevate', 'master'
    ]
    features['has_action_words'] = any(word in title.lower() for word in action_words)
    
    return features

def similarity_score(title, category_keywords):
    """Calculate similarity score between title and category keywords."""
    title_lower = title.lower()
    score = 0
    matched = []
    
    for keyword in category_keywords:
        if keyword.lower() in title_lower:
            score += 1
            matched.append(keyword)
    
    return score, matched

def classify_uncategorized_videos():
    """Perform deep analysis on uncategorized videos."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Load data
    videos = load_categorized_data()
    uncategorized = [v for v in videos if not v['primary_category']]
    
    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS OF {len(uncategorized)} UNCATEGORIZED VIDEOS")
    print(f"{'='*80}\n")
    
    # Analyze each uncategorized video
    results = []
    
    for i, video in enumerate(uncategorized, 1):
        title = video['title']
        video_id = extract_video_id(video['url'])
        
        # Extract features
        features = analyze_title_patterns(title)
        
        # Calculate similarity scores for all categories
        category_scores = {}
        for category, data in CATEGORIES.items():
            score, matched = similarity_score(title, data['keywords'] + data['secondary_keywords'])
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'matched_keywords': matched
                }
        
        # Determine best classification
        best_category = None
        best_score = 0
        confidence = 'LOW'
        best_data = {}
        
        if category_scores:
            sorted_scores = sorted(category_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            best_category, best_data = sorted_scores[0]
            best_score = best_data['score']
            
            # Calculate confidence
            if best_score >= 3:
                confidence = 'HIGH'
            elif best_score >= 2:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
        
        # Special rule checks
        special_rules = []
        
        # Check for Saturday School pattern
        if 'saturday' in title.lower() or 'school' in title.lower():
            best_category = 'SATURDAY_SCHOOL'
            confidence = 'HIGH'
            special_rules.append('Saturday School pattern detected')
        
        # Check for interview patterns
        if features['has_guest'] and best_category != 'INTERVIEWS_GUESTS':
            special_rules.append('Guest detected - consider INTERVIEWS_GUESTS')
        
        # Check for question format (often mindset/education)
        if features['has_question'] and not best_category:
            best_category = 'MINDSET_MOTIVATION'
            confidence = 'MEDIUM'
            special_rules.append('Question format suggests educational content')
        
        # Compile result
        result = {
            'index': i,
            'video_id': video_id,
            'title': title,
            'url': video['url'],
            'features': features,
            'category_scores': category_scores,
            'proposed_category': best_category,
            'confidence': confidence,
            'evidence': best_data.get('matched_keywords', []) if best_category else [],
            'special_rules': special_rules,
            'needs_review': confidence == 'LOW' or not best_category
        }
        
        results.append(result)
        
        # Print progress
        if i <= 20 or i % 50 == 0:
            print(f"[{i}/{len(uncategorized)}] {title[:60]}...")
            if best_category:
                print(f"    → {best_category} ({confidence} confidence)")
                if result['evidence']:
                    print(f"    Evidence: {', '.join(result['evidence'][:3])}")
            if special_rules:
                print(f"    Notes: {', '.join(special_rules)}")
            print()
    
    # Prioritize by confidence and impact
    high_priority = [r for r in results if r['confidence'] == 'HIGH' and r['proposed_category']]
    medium_priority = [r for r in results if r['confidence'] == 'MEDIUM' and r['proposed_category']]
    low_priority = [r for r in results if r['confidence'] == 'LOW' or not r['proposed_category']]
    
    # Generate comprehensive report
    report_file = os.path.join(BASE_DIR, "uncategorized_analysis_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Deep Analysis Report: Uncategorized Mark Bell Videos\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Uncategorized: {len(uncategorized)}\n\n")
        
        # Summary
        f.write("## Classification Summary\n\n")
        f.write(f"- High Confidence (ready to auto-classify): {len(high_priority)}\n")
        f.write(f"- Medium Confidence (needs quick review): {len(medium_priority)}\n")
        f.write(f"- Low Confidence/Unresolved: {len(low_priority)}\n\n")
        
        # High priority items
        f.write("## High Priority - Ready for Auto-Classification\n\n")
        for r in high_priority[:20]:  # Show first 20
            f.write(f"### {r['index']}. {r['title']}\n")
            f.write(f"- **Proposed Category:** {r['proposed_category']}\n")
            f.write(f"- **Confidence:** {r['confidence']}\n")
            f.write(f"- **Evidence:** {', '.join(r['evidence'])}\n")
            f.write(f"- **Video ID:** {r['video_id']}\n\n")
        
        # Medium priority items
        f.write(f"\n## Medium Priority - Needs Quick Review ({len(medium_priority)} items)\n\n")
        category_counts = Counter(r['proposed_category'] for r in medium_priority if r['proposed_category'])
        for cat, count in category_counts.most_common():
            f.write(f"- {cat}: {count} videos\n")
        
        # Low priority items
        f.write(f"\n## Low Priority - Requires Manual Review ({len(low_priority)} items)\n\n")
        
        # Pattern analysis
        f.write("\n## Pattern Analysis\n\n")
        f.write("### Common Features in Uncategorized Videos:\n\n")
        
        feature_counts = {
            'has_guest': sum(1 for r in results if r['features']['has_guest']),
            'has_question': sum(1 for r in results if r['features']['has_question']),
            'has_number': sum(1 for r in results if r['features']['has_number']),
            'has_episode': sum(1 for r in results if r['features']['has_episode'])
        }
        
        for feature, count in feature_counts.items():
            percentage = (count / len(results)) * 100
            f.write(f"- {feature}: {count} videos ({percentage:.1f}%)\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        f.write("1. **Immediate Action:** Auto-classify all HIGH confidence items\n")
        f.write("2. **Quick Review:** Review MEDIUM confidence items (focus on top categories)\n")
        f.write("3. **Deep Dive:** Analyze LOW confidence items for new category patterns\n")
        f.write("4. **Keyword Enhancement:** Add new keywords based on patterns found\n")
        f.write("5. **Quality Check:** Spot check 10% of auto-classified items\n\n")
        
        # Sample low confidence items for manual review
        f.write("## Sample Items Needing Manual Review\n\n")
        for r in low_priority[:10]:
            f.write(f"### {r['index']}. {r['title']}\n")
            f.write(f"- **Features:** Guest={r['features']['has_guest']}, Question={r['features']['has_question']}\n")
            f.write(f"- **Top Score:** {max(r['category_scores'].items(), key=lambda x: x[1]['score']) if r['category_scores'] else 'None'}\n\n")
    
    # Save detailed results
    detailed_file = os.path.join(BASE_DIR, "uncategorized_detailed.json")
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"\nPriority Breakdown:")
    print(f"  High Confidence: {len(high_priority)} videos (ready to auto-classify)")
    print(f"  Medium Confidence: {len(medium_priority)} videos (quick review needed)")
    print(f"  Low Priority: {len(low_priority)} videos (manual review required)")
    print(f"\nFiles Created:")
    print(f"  - {report_file}")
    print(f"  - {detailed_file}")
    
    return results

# Import categories from previous script
CATEGORIES = {
    'STRENGTH_TRAINING': {
        'keywords': [
            'squat', 'bench', 'deadlift', 'powerlifting', 'strongman', 'bodybuilding',
            'hypertrophy', 'weightlifting', 'olympic', 'strength', 'training', 'programming',
            'periodization', 'volume', 'intensity', 'rpe', 'pr', 'competition', 'peaking',
            'deload', 'workout', 'lift', 'lifting', 'gym', 'gainz'
        ],
        'secondary_keywords': ['power', 'force', 'muscle', 'athlete', 'performance']
    },
    'TECHNIQUE_BIOMECHANICS': {
        'keywords': [
            'technique', 'form', 'biomechanics', 'cue', 'depth', 'range of motion',
            'bracing', 'breathing', 'tempo', 'eccentric', 'concentric', 'movement',
            'mobility', 'flexibility', 'stability', 'posture', 'alignment'
        ],
        'secondary_keywords': ['how to', 'proper', 'correct', 'fix', 'improve']
    },
    'NUTRITION': {
        'keywords': [
            'nutrition', 'diet', 'food', 'meal', 'protein', 'carb', 'fat', 'calorie',
            'macro', 'micro', 'vitamin', 'mineral', 'supplement', 'carnivore', 'keto',
            'vegan', 'vegetarian', 'fasting', 'bulking', 'cutting', 'hydration'
        ],
        'secondary_keywords': ['eat', 'cooking', 'recipe', 'meal prep', 'nutritionist']
    },
    'PEPTIDES_HORMONES': {
        'keywords': [
            'peptide', 'bpc-157', 'tb-500', 'cjc-1295', 'ipamorelin', 'hormone',
            'testosterone', 'hgh', 'estrogen', 'trt', 'hrt', 'bloodwork', 'therapy',
            'optimization', 'age management', 'fertility', 'recovery'
        ],
        'secondary_keywords': ['regenerative', 'healing', 'anti-aging', 'longevity']
    },
    'PEDS_PERFORMANCE_ENHANCEMENT': {
        'keywords': [
            'steroid', 'aas', 'sarm', 'prohormone', 'cycle', 'ped', 'enhancement',
            'anabolic', 'androgenic', 'pct', 'side effect', 'gyno', 'hair loss',
            'liver', 'blood pressure', 'cardarine', 'lgd', 'ostarine', 'rad'
        ],
        'secondary_keywords': ['gear', 'juice', 'enhanced', 'chemical']
    },
    'LONGEVITY_HEALTHSPAN': {
        'keywords': [
            'longevity', 'healthspan', 'aging', 'anti-aging', 'lifespan', 'biomarker',
            'sleep', 'stress', 'cortisol', 'meditation', 'cold therapy', 'heat therapy',
            'cellular', 'mitochondria', 'telomere', 'biological age'
        ],
        'secondary_keywords': ['health', 'wellness', 'optimization', 'biohacking']
    },
    'RECOVERY_REHABILITATION': {
        'keywords': [
            'recovery', 'rehab', 'injury', 'pain', 'inflammation', 'massage',
            'foam roller', 'stretching', 'physical therapy', 'prehab', 'soreness',
            'rest', 'heal', 'treatment', 'therapy'
        ],
        'secondary_keywords': ['restore', 'repair', 'recover', 'healing']
    },
    'EQUIPMENT_GEAR': {
        'keywords': [
            'equipment', 'gear', 'bar', 'bell', 'kettlebell', 'dumbbell', 'machine',
            'rack', 'bench', 'sling shot', 'review', 'home gym', 'commercial gym',
            'apparel', 'wearable', 'tracking', 'technology', 'device'
        ],
        'secondary_keywords': ['product', 'tool', 'device', 'app', 'tech']
    },
    'INTERVIEWS_GUESTS': {
        'keywords': [
            'interview', 'guest', 'expert', 'doctor', 'scientist', 'champion',
            'coach', 'podcast', 'feat.', 'featuring', 'special guest'
        ],
        'secondary_keywords': ['talk', 'discussion', 'conversation', 'qa', 'q&a']
    },
    'BUSINESS_ENTREPRENEURSHIP': {
        'keywords': [
            'business', 'entrepreneur', 'money', 'marketing', 'brand', 'revenue',
            'social media', 'youtube', 'content', 'career', 'industry', 'supplement business'
        ],
        'secondary_keywords': ['company', 'income', 'success', 'growth']
    },
    'MINDSET_MOTIVATION': {
        'keywords': [
            'motivation', 'mindset', 'discipline', 'consistency', 'goal', 'habit',
            'mental toughness', 'confidence', 'focus', 'drive', 'inspiration',
            'willpower', 'grit', 'determination'
        ],
        'secondary_keywords': ['psychology', 'mental', 'brain', 'think']
    },
    'COMMUNITY_EVENTS': {
        'keywords': [
            'competition', 'meet', 'event', 'live', 'fan mail', 'reaction',
            'challenge', 'contest', 'recap', 'coverage', 'gathering'
        ],
        'secondary_keywords': ['audience', 'community', 'fan', 'viewer']
    },
    'SATURDAY_SCHOOL': {
        'keywords': ['saturday school', 'school', 'lesson', 'advice', 'rant'],
        'secondary_keywords': ['teaching', 'education', 'guidance']
    }
}

if __name__ == "__main__":
    results = classify_uncategorized_videos()
