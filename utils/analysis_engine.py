import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ml_models import FakeNewsDetector
from services.facebook_service import FacebookService
from services.factcheck_service import FactCheckService
from services.firebase_service import FirebaseService
from utils.preprocessor import TextPreprocessor
from utils.credibility_scorer import CredibilityScorer
from typing import Dict, Optional
import re
from urllib.parse import urlparse
from datetime import datetime

class NewsAnalysisEngine:
    def __init__(self):
        # Initialize all components
        self.ml_detector = FakeNewsDetector()
        self.facebook_service = FacebookService()
        self.factcheck_service = FactCheckService()
        self.firebase_service = FirebaseService()
        self.preprocessor = TextPreprocessor()
        self.credibility_scorer = CredibilityScorer()
        
        # Load ML model if available
        try:
            if not self.ml_detector.is_trained:
                print("Warning: ML model not found. Training with sample data...")
                texts, labels = self.ml_detector.create_sample_training_data()
                self.ml_detector.train(texts, labels)
            else:
                print("ML model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not initialize ML model: {e}")
    
    def analyze_news(self, input_data: str, input_type: str = 'auto', user_id: str = None) -> Dict:
        """Main analysis function that coordinates all detection methods"""
        
        # Determine input type if auto
        if input_type == 'auto':
            input_type = self._detect_input_type(input_data)
        
        # Initialize analysis results
        analysis_results = {
            'input_text': input_data,
            'input_type': input_type,
            'preprocessing_results': {},
            'ml_prediction': {},
            'factcheck_results': {},
            'poser_analysis': {},
            'source_info': {},
            'final_credibility_score': 0.5,
            'verdict': 'Unknown',
            'confidence': 0.0,
            'explanation': '',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Extract and preprocess text
            text_content = self._extract_text_content(input_data, input_type)
            analysis_results['extracted_text'] = text_content
            
            if not text_content or len(text_content.strip()) < 10:
                return self._create_error_result("Insufficient text content for analysis", analysis_results)
            
            # Step 2: Preprocess text
            preprocessing_results = self.preprocessor.preprocess(
                text_content, 
                detect_slang=True, 
                detect_sarcasm_flag=True
            )
            analysis_results['preprocessing_results'] = preprocessing_results
            
            # Step 3: ML prediction
            ml_prediction = self._get_ml_prediction(preprocessing_results['processed_text'])
            analysis_results['ml_prediction'] = ml_prediction
            
            # Step 4: Fact checking
            factcheck_results = self._get_factcheck_results(text_content)
            analysis_results['factcheck_results'] = factcheck_results
            
            # Step 5: Poser detection (if Facebook content)
            if input_type == 'facebook_url' or 'facebook.com' in input_data:
                poser_analysis = self._get_poser_analysis(input_data)
                analysis_results['poser_analysis'] = poser_analysis
            
            # Step 6: Source credibility assessment
            source_info = self._assess_source_credibility(input_data, input_type)
            analysis_results['source_info'] = source_info
            
            # Step 7: Calculate final credibility score
            credibility_assessment = self.credibility_scorer.calculate_credibility_score(analysis_results)
            
            # Update results with final assessment
            analysis_results.update({
                'final_credibility_score': credibility_assessment['final_score'],
                'verdict': credibility_assessment['verdict'],
                'confidence': credibility_assessment['confidence'],
                'explanation': credibility_assessment['explanation'],
                'component_scores': credibility_assessment['component_scores'],
                'credibility_level_info': self.credibility_scorer.get_credibility_level_info(
                    credibility_assessment['final_score']
                ),
                'timestamp': credibility_assessment['timestamp']
            })
            
            # Step 8: Save results to database (if user provided)
            if user_id and self.firebase_service.db:
                analysis_id = self.firebase_service.save_analysis_result(user_id, analysis_results)
                analysis_results['analysis_id'] = analysis_id
            
            return analysis_results
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            return self._create_error_result(f"Analysis failed: {str(e)}", analysis_results)
    
    def _detect_input_type(self, input_data: str) -> str:
        """Automatically detect the type of input"""
        input_data = input_data.strip()
        
        # Check if it's a URL
        if self._is_url(input_data):
            if 'facebook.com' in input_data:
                return 'facebook_url'
            else:
                return 'url'
        
        # Check if it's a Facebook post ID
        if re.match(r'^\d+_\d+$', input_data):
            return 'facebook_post_id'
        
        # Default to text
        return 'text'
    
    def _is_url(self, text: str) -> bool:
        """Check if text is a valid URL"""
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_text_content(self, input_data: str, input_type: str) -> str:
        """Extract text content based on input type"""
        if input_type == 'text':
            return input_data
        
        elif input_type == 'url':
            return self.preprocessor.extract_text_from_url(input_data)
        
        elif input_type == 'facebook_url':
            # Extract post ID from Facebook URL and get post content
            post_id = self._extract_facebook_post_id(input_data)
            if post_id:
                post_details = self.facebook_service.get_post_details(post_id)
                if 'error' not in post_details:
                    return post_details.get('message', '') or post_details.get('story', '')
            return "Could not extract Facebook post content"
        
        elif input_type == 'facebook_post_id':
            post_details = self.facebook_service.get_post_details(input_data)
            if 'error' not in post_details:
                return post_details.get('message', '') or post_details.get('story', '')
            return "Could not fetch Facebook post"
        
        return input_data
    
    def _extract_facebook_post_id(self, url: str) -> Optional[str]:
        """Extract Facebook post ID from URL"""
        # Simple regex to extract post ID from Facebook URLs
        patterns = [
            r'facebook\.com/.*?/posts/(\d+)',
            r'facebook\.com/.*?/photos/.*?(\d+)',
            r'facebook\.com/permalink\.php\?story_fbid=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_ml_prediction(self, processed_text: str) -> Dict:
        """Get machine learning prediction"""
        try:
            prediction_result = self.ml_detector.predict(processed_text)
            return {
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'model_used': prediction_result.get('model_used', 'ensemble'),
                'probabilities': prediction_result.get('probabilities', {})
            }
        except Exception as e:
            print(f"ML prediction error: {e}")
            return {
                'prediction': 0.5,
                'confidence': 0.0,
                'model_used': 'fallback',
                'error': str(e)
            }
    
    def _get_factcheck_results(self, text_content: str) -> Dict:
        """Get fact checking results from Google Fact Check API"""
        try:
            # Extract key phrases for fact checking
            key_phrases = self._extract_key_phrases(text_content)
            
            all_results = []
            for phrase in key_phrases[:3]:  # Limit to top 3 phrases
                result = self.factcheck_service.get_fact_check_summary(phrase)
                if result and not result.get('fact_check_results', {}).get('error'):
                    all_results.append(result)
            
            if all_results:
                # Combine results from multiple queries
                return self._combine_factcheck_results(all_results)
            else:
                return {
                    'claims': [],
                    'credibility_analysis': {
                        'overall_score': 0.5,
                        'confidence': 0.0,
                        'verdict': 'No fact checks found'
                    }
                }
                
        except Exception as e:
            print(f"Fact check error: {e}")
            return {
                'error': str(e),
                'claims': [],
                'credibility_analysis': {
                    'overall_score': 0.5,
                    'confidence': 0.0,
                    'verdict': 'Fact check failed'
                }
            }
    
    def _extract_key_phrases(self, text: str) -> list:
        """Extract key phrases for fact checking"""
        # Simple keyword extraction (can be improved with NLP libraries)
        words = text.lower().split()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        # Extract potential key phrases
        key_phrases = []
        
        # Look for quoted text
        quoted_text = re.findall(r'"([^"]+)"', text)
        key_phrases.extend(quoted_text)
        
        # Look for capitalized phrases (potential proper nouns)
        capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(\s+[A-Z][a-z]+)*\b', text)
        key_phrases.extend(capitalized_phrases)
        
        # Extract important keywords
        important_words = [word for word in words if len(word) > 4 and word not in stop_words]
        key_phrases.extend(important_words[:5])
        
        # Return unique phrases, limited to reasonable length
        unique_phrases = list(set(phrase for phrase in key_phrases if len(phrase) > 3 and len(phrase) < 100))
        return unique_phrases[:5]
    
    def _combine_factcheck_results(self, results_list: list) -> Dict:
        """Combine multiple fact check results"""
        all_claims = []
        all_scores = []
        all_confidences = []
        
        for result in results_list:
            fact_check_results = result.get('fact_check_results', {})
            claims = fact_check_results.get('claims', [])
            all_claims.extend(claims)
            
            credibility = result.get('credibility_analysis', {})
            if credibility.get('overall_score') is not None:
                all_scores.append(credibility['overall_score'])
                all_confidences.append(credibility.get('confidence', 0.0))
        
        if all_scores:
            # Calculate weighted average
            weighted_score = sum(score * conf for score, conf in zip(all_scores, all_confidences))
            total_weight = sum(all_confidences)
            
            if total_weight > 0:
                overall_score = weighted_score / total_weight
                overall_confidence = total_weight / len(all_scores)
            else:
                overall_score = sum(all_scores) / len(all_scores)
                overall_confidence = 0.3
        else:
            overall_score = 0.5
            overall_confidence = 0.0
        
        return {
            'claims': all_claims,
            'credibility_analysis': {
                'overall_score': overall_score,
                'confidence': min(1.0, overall_confidence),
                'verdict': self._score_to_verdict(overall_score),
                'evidence_count': len(all_claims),
                'source_diversity': len(set(claim.get('claimant', '') for claim in all_claims))
            }
        }
    
    def _score_to_verdict(self, score: float) -> str:
        """Convert score to verdict"""
        if score >= 0.8:
            return 'Likely True'
        elif score >= 0.6:
            return 'Leaning True'
        elif score >= 0.4:
            return 'Mixed Evidence'
        elif score >= 0.2:
            return 'Leaning False'
        else:
            return 'Likely False'
    
    def _get_poser_analysis(self, input_data: str) -> Dict:
        """Get poser detection analysis for Facebook content"""
        try:
            # Extract page ID or post ID
            if 'facebook.com' in input_data:
                # Try to extract page ID from URL
                page_match = re.search(r'facebook\.com/([^/]+)', input_data)
                if page_match:
                    page_identifier = page_match.group(1)
                    return self.facebook_service.analyze_account_activity(page_identifier)
            
            return {'error': 'Could not extract Facebook page information'}
            
        except Exception as e:
            print(f"Poser analysis error: {e}")
            return {'error': str(e)}
    
    def _assess_source_credibility(self, input_data: str, input_type: str) -> Dict:
        """Assess source credibility"""
        source_info = {
            'type': input_type,
            'domain': '',
            'credibility_indicators': []
        }
        
        if input_type in ['url', 'facebook_url']:
            try:
                parsed_url = urlparse(input_data)
                domain = parsed_url.netloc.lower()
                source_info['domain'] = domain
                
                # Add domain-specific credibility indicators
                if domain.endswith('.gov'):
                    source_info['credibility_indicators'].append('Government domain')
                elif domain.endswith('.edu'):
                    source_info['credibility_indicators'].append('Educational domain')
                elif 'facebook.com' in domain:
                    source_info['credibility_indicators'].append('Social media platform')
                
            except:
                pass
        
        return source_info
    
    def _create_error_result(self, error_message: str, partial_results: Dict) -> Dict:
        """Create error result with partial analysis"""
        partial_results.update({
            'error': error_message,
            'final_credibility_score': 0.5,
            'verdict': 'Analysis Failed',
            'confidence': 0.0,
            'explanation': f'Analysis could not be completed: {error_message}'
        })
        return partial_results
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve a previous analysis by ID"""
        if self.firebase_service.db:
            return self.firebase_service.get_analysis_by_id(analysis_id)
        return None
    
    def get_user_analysis_history(self, user_id: str, limit: int = 20) -> list:
        """Get user's analysis history"""
        if self.firebase_service.db:
            return self.firebase_service.get_user_news_verifications(user_id, limit)
        return []