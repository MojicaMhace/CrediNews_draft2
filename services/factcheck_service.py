import requests
import os
from typing import Dict, List, Optional
from urllib.parse import quote
from datetime import datetime

class FactCheckService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_FACTCHECK_API_KEY')
        self.base_url = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'
        
        if not self.api_key:
            print("Warning: Google Fact Check API key not found. Fact checking will be limited.")
    
    def search_fact_checks(self, query: str, language_code: str = 'en') -> Dict:
        """Search for fact checks related to a query"""
        if not self.api_key:
            return {
                'claims': [],
                'error': 'API key not configured',
                'source': 'google_factcheck'
            }
        
        try:
            params = {
                'key': self.api_key,
                'query': query,
                'languageCode': language_code,
                'pageSize': 10
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and structure the response
            claims = data.get('claims', [])
            processed_claims = []
            
            for claim in claims:
                processed_claim = self._process_claim(claim)
                processed_claims.append(processed_claim)
            
            return {
                'claims': processed_claims,
                'total_results': len(processed_claims),
                'source': 'google_factcheck',
                'query': query
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching fact checks: {e}")
            return {
                'claims': [],
                'error': str(e),
                'source': 'google_factcheck'
            }
    
    def _process_claim(self, claim: Dict) -> Dict:
        """Process and structure a single claim from the API response"""
        claim_text = claim.get('text', '')
        claimant = claim.get('claimant', 'Unknown')
        claim_date = claim.get('claimDate', '')
        
        # Process claim reviews
        reviews = []
        for review in claim.get('claimReview', []):
            publisher = review.get('publisher', {})
            
            processed_review = {
                'publisher_name': publisher.get('name', 'Unknown'),
                'publisher_site': publisher.get('site', ''),
                'url': review.get('url', ''),
                'title': review.get('title', ''),
                'review_date': review.get('reviewDate', ''),
                'textual_rating': review.get('textualRating', ''),
                'language_code': review.get('languageCode', 'en')
            }
            
            # Normalize the rating
            rating = self._normalize_rating(processed_review['textual_rating'])
            processed_review['normalized_rating'] = rating
            
            reviews.append(processed_review)
        
        return {
            'claim_text': claim_text,
            'claimant': claimant,
            'claim_date': claim_date,
            'reviews': reviews,
            'review_count': len(reviews)
        }
    
    def _normalize_rating(self, textual_rating: str) -> Dict:
        """Normalize textual ratings to a standard format"""
        if not textual_rating:
            return {'score': 0.5, 'label': 'Unknown', 'confidence': 0.0}
        
        rating_lower = textual_rating.lower()
        
        # Define rating mappings (score from 0.0 to 1.0, where 1.0 is completely true)
        rating_mappings = {
            # True ratings
            'true': {'score': 1.0, 'label': 'True', 'confidence': 0.9},
            'correct': {'score': 1.0, 'label': 'True', 'confidence': 0.9},
            'accurate': {'score': 1.0, 'label': 'True', 'confidence': 0.9},
            'verified': {'score': 1.0, 'label': 'True', 'confidence': 0.9},
            
            # Mostly true
            'mostly true': {'score': 0.8, 'label': 'Mostly True', 'confidence': 0.8},
            'mostly correct': {'score': 0.8, 'label': 'Mostly True', 'confidence': 0.8},
            'largely accurate': {'score': 0.8, 'label': 'Mostly True', 'confidence': 0.8},
            
            # Mixed/Partially true
            'mixture': {'score': 0.5, 'label': 'Mixed', 'confidence': 0.7},
            'half true': {'score': 0.5, 'label': 'Mixed', 'confidence': 0.7},
            'partially true': {'score': 0.5, 'label': 'Mixed', 'confidence': 0.7},
            'some truth': {'score': 0.5, 'label': 'Mixed', 'confidence': 0.7},
            
            # Mostly false
            'mostly false': {'score': 0.2, 'label': 'Mostly False', 'confidence': 0.8},
            'mostly incorrect': {'score': 0.2, 'label': 'Mostly False', 'confidence': 0.8},
            'largely inaccurate': {'score': 0.2, 'label': 'Mostly False', 'confidence': 0.8},
            
            # False ratings
            'false': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            'incorrect': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            'inaccurate': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            'debunked': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            'fake': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            'hoax': {'score': 0.0, 'label': 'False', 'confidence': 0.9},
            
            # Unverifiable
            'unverifiable': {'score': 0.3, 'label': 'Unverifiable', 'confidence': 0.6},
            'unproven': {'score': 0.3, 'label': 'Unverifiable', 'confidence': 0.6},
            'no evidence': {'score': 0.3, 'label': 'Unverifiable', 'confidence': 0.6},
            
            # Satire/Opinion
            'satire': {'score': 0.1, 'label': 'Satire', 'confidence': 0.8},
            'opinion': {'score': 0.4, 'label': 'Opinion', 'confidence': 0.7},
            'commentary': {'score': 0.4, 'label': 'Opinion', 'confidence': 0.7}
        }
        
        # Try exact match first
        if rating_lower in rating_mappings:
            return rating_mappings[rating_lower]
        
        # Try partial matches
        for key, value in rating_mappings.items():
            if key in rating_lower or rating_lower in key:
                return value
        
        # Default for unknown ratings
        return {
            'score': 0.5, 
            'label': f'Unknown ({textual_rating})', 
            'confidence': 0.3
        }
    
    def analyze_claim_credibility(self, claims_data: Dict) -> Dict:
        """Analyze the overall credibility based on fact check results"""
        claims = claims_data.get('claims', [])
        
        if not claims:
            return {
                'overall_score': 0.5,
                'confidence': 0.0,
                'verdict': 'No fact checks found',
                'evidence_count': 0,
                'source_diversity': 0
            }
        
        # Collect all ratings
        all_ratings = []
        publishers = set()
        
        for claim in claims:
            for review in claim.get('reviews', []):
                rating = review.get('normalized_rating', {})
                if rating.get('score') is not None:
                    all_ratings.append(rating)
                    publishers.add(review.get('publisher_name', ''))
        
        if not all_ratings:
            return {
                'overall_score': 0.5,
                'confidence': 0.0,
                'verdict': 'No valid ratings found',
                'evidence_count': 0,
                'source_diversity': 0
            }
        
        # Calculate weighted average score
        total_weighted_score = 0
        total_weight = 0
        
        for rating in all_ratings:
            weight = rating.get('confidence', 0.5)
            score = rating.get('score', 0.5)
            total_weighted_score += score * weight
            total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.5
        
        # Calculate confidence based on number of sources and agreement
        source_diversity = len(publishers)
        evidence_count = len(all_ratings)
        
        # Calculate agreement (how much ratings agree with each other)
        scores = [r.get('score', 0.5) for r in all_ratings]
        if len(scores) > 1:
            score_variance = sum((s - overall_score) ** 2 for s in scores) / len(scores)
            agreement = max(0, 1 - score_variance * 4)  # Scale variance to 0-1
        else:
            agreement = 1.0
        
        # Overall confidence
        confidence = min(1.0, (
            (evidence_count / 10) * 0.4 +  # More evidence = higher confidence
            (source_diversity / 5) * 0.3 +  # More diverse sources = higher confidence
            agreement * 0.3  # Higher agreement = higher confidence
        ))
        
        # Determine verdict
        if overall_score >= 0.8:
            verdict = 'Likely True'
        elif overall_score >= 0.6:
            verdict = 'Leaning True'
        elif overall_score >= 0.4:
            verdict = 'Mixed/Uncertain'
        elif overall_score >= 0.2:
            verdict = 'Leaning False'
        else:
            verdict = 'Likely False'
        
        return {
            'overall_score': round(overall_score, 3),
            'confidence': round(confidence, 3),
            'verdict': verdict,
            'evidence_count': evidence_count,
            'source_diversity': source_diversity,
            'agreement_level': round(agreement, 3),
            'detailed_ratings': all_ratings
        }
    
    def get_fact_check_summary(self, query: str, language_code: str = 'en') -> Dict:
        """Get a comprehensive fact check summary for a query"""
        # Search for fact checks
        claims_data = self.search_fact_checks(query, language_code)
        
        # Analyze credibility
        credibility_analysis = self.analyze_claim_credibility(claims_data)
        
        # Combine results
        return {
            'query': query,
            'fact_check_results': claims_data,
            'credibility_analysis': credibility_analysis,
            'timestamp': datetime.utcnow().isoformat(),
            'api_status': 'success' if not claims_data.get('error') else 'error'
        }