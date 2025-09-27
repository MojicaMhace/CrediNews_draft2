from typing import Dict, List, Optional
import numpy as np
from datetime import datetime

class CredibilityScorer:
    def __init__(self):
        # Weights for different components (should sum to 1.0)
        self.weights = {
            'ml_prediction': 0.35,      # Machine learning model prediction
            'factcheck_results': 0.30,   # Google Fact Check API results
            'poser_detection': 0.15,     # Facebook account analysis
            'preprocessing_flags': 0.10, # Text preprocessing red flags
            'source_credibility': 0.10   # Source credibility assessment
        }
        
        # Confidence modifiers
        self.confidence_factors = {
            'ml_confidence': 0.25,
            'factcheck_evidence': 0.25,
            'source_diversity': 0.20,
            'content_quality': 0.15,
            'temporal_consistency': 0.15
        }
    
    def calculate_credibility_score(self, analysis_data: Dict) -> Dict:
        """Calculate overall credibility score from all analysis components"""
        
        # Extract component scores
        ml_score = self._process_ml_prediction(analysis_data.get('ml_prediction', {}))
        factcheck_score = self._process_factcheck_results(analysis_data.get('factcheck_results', {}))
        poser_score = self._process_poser_detection(analysis_data.get('poser_analysis', {}))
        preprocessing_score = self._process_preprocessing_flags(analysis_data.get('preprocessing_results', {}))
        source_score = self._process_source_credibility(analysis_data.get('source_info', {}))
        
        # Calculate weighted average
        weighted_score = (
            ml_score['score'] * self.weights['ml_prediction'] +
            factcheck_score['score'] * self.weights['factcheck_results'] +
            poser_score['score'] * self.weights['poser_detection'] +
            preprocessing_score['score'] * self.weights['preprocessing_flags'] +
            source_score['score'] * self.weights['source_credibility']
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence({
            'ml': ml_score,
            'factcheck': factcheck_score,
            'poser': poser_score,
            'preprocessing': preprocessing_score,
            'source': source_score
        })
        
        # Determine verdict
        verdict = self._determine_verdict(weighted_score, confidence)
        
        # Generate explanation
        explanation = self._generate_explanation({
            'ml': ml_score,
            'factcheck': factcheck_score,
            'poser': poser_score,
            'preprocessing': preprocessing_score,
            'source': source_score
        }, weighted_score, confidence)
        
        return {
            'final_score': round(weighted_score, 3),
            'confidence': round(confidence, 3),
            'verdict': verdict,
            'explanation': explanation,
            'component_scores': {
                'ml_prediction': ml_score,
                'factcheck_results': factcheck_score,
                'poser_detection': poser_score,
                'preprocessing_flags': preprocessing_score,
                'source_credibility': source_score
            },
            'weights_used': self.weights,
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_ml_prediction(self, ml_data: Dict) -> Dict:
        """Process machine learning prediction results"""
        if not ml_data:
            return {'score': 0.5, 'confidence': 0.0, 'details': 'No ML prediction available'}
        
        # Extract prediction and confidence
        prediction = ml_data.get('prediction', 0.5)
        ml_confidence = ml_data.get('confidence', 0.0)
        model_used = ml_data.get('model_used', 'unknown')
        
        # Convert prediction to credibility score (1.0 = credible, 0.0 = not credible)
        if isinstance(prediction, str):
            score = 1.0 if prediction.lower() in ['real', 'true', 'credible'] else 0.0
        else:
            score = float(prediction)
        
        return {
            'score': score,
            'confidence': ml_confidence,
            'details': f'ML model ({model_used}) prediction: {prediction}',
            'model_used': model_used
        }
    
    def _process_factcheck_results(self, factcheck_data: Dict) -> Dict:
        """Process Google Fact Check API results"""
        if not factcheck_data or factcheck_data.get('error'):
            return {'score': 0.5, 'confidence': 0.0, 'details': 'No fact check data available'}
        
        credibility_analysis = factcheck_data.get('credibility_analysis', {})
        
        if not credibility_analysis:
            return {'score': 0.5, 'confidence': 0.0, 'details': 'No credibility analysis available'}
        
        score = credibility_analysis.get('overall_score', 0.5)
        confidence = credibility_analysis.get('confidence', 0.0)
        evidence_count = credibility_analysis.get('evidence_count', 0)
        verdict = credibility_analysis.get('verdict', 'Unknown')
        
        details = f"Fact check verdict: {verdict} (based on {evidence_count} sources)"
        
        return {
            'score': score,
            'confidence': confidence,
            'details': details,
            'evidence_count': evidence_count,
            'verdict': verdict
        }
    
    def _process_poser_detection(self, poser_data: Dict) -> Dict:
        """Process Facebook poser detection results"""
        if not poser_data:
            return {'score': 0.7, 'confidence': 0.0, 'details': 'No poser analysis available'}
        
        poser_analysis = poser_data.get('poser_analysis', {})
        
        if not poser_analysis:
            return {'score': 0.7, 'confidence': 0.0, 'details': 'No poser analysis data'}
        
        risk_level = poser_analysis.get('risk_level', 'UNKNOWN')
        suspicion_score = poser_analysis.get('suspicion_score', 0)
        is_verified = poser_analysis.get('is_verified', False)
        flags = poser_analysis.get('flags', [])
        
        # Convert risk level to credibility score
        if risk_level == 'LOW':
            score = 0.8
            confidence = 0.7
        elif risk_level == 'MEDIUM':
            score = 0.5
            confidence = 0.6
        elif risk_level == 'HIGH':
            score = 0.2
            confidence = 0.8
        else:
            score = 0.5
            confidence = 0.3
        
        # Boost score if account is verified
        if is_verified:
            score = min(1.0, score + 0.2)
            confidence = min(1.0, confidence + 0.1)
        
        details = f"Account risk: {risk_level} (suspicion score: {suspicion_score})"
        if flags:
            details += f". Flags: {', '.join(flags[:3])}"
        
        return {
            'score': score,
            'confidence': confidence,
            'details': details,
            'risk_level': risk_level,
            'is_verified': is_verified,
            'flags': flags
        }
    
    def _process_preprocessing_flags(self, preprocessing_data: Dict) -> Dict:
        """Process text preprocessing red flags"""
        if not preprocessing_data:
            return {'score': 0.6, 'confidence': 0.0, 'details': 'No preprocessing analysis available'}
        
        score = 0.6  # Neutral starting point
        confidence = 0.5
        flags = []
        
        # Check for fake news indicators
        fake_indicators = preprocessing_data.get('fake_indicators', [])
        if fake_indicators:
            score -= len(fake_indicators) * 0.1
            flags.extend([f"Fake news indicator: {indicator}" for indicator in fake_indicators[:3]])
        
        # Check for sarcasm
        sarcasm_analysis = preprocessing_data.get('sarcasm_analysis', {})
        if sarcasm_analysis.get('is_sarcastic', False):
            sarcasm_confidence = sarcasm_analysis.get('confidence', 0)
            score -= sarcasm_confidence * 0.2
            flags.append(f"Potential sarcasm detected (confidence: {sarcasm_confidence:.2f})")
        
        # Check for Filipino slang (might indicate informal/unreliable source)
        slang_detected = preprocessing_data.get('slang_detected', [])
        if len(slang_detected) > 3:  # Many slang terms might indicate informal content
            score -= 0.1
            flags.append(f"High informal language usage ({len(slang_detected)} slang terms)")
        
        # Check content quality indicators
        token_count = preprocessing_data.get('token_count', 0)
        if token_count < 10:  # Very short content
            score -= 0.1
            flags.append("Very short content")
        elif token_count > 1000:  # Very long content might be more detailed/reliable
            score += 0.05
        
        # Ensure score stays within bounds
        score = max(0.0, min(1.0, score))
        
        details = "Text analysis: " + (', '.join(flags) if flags else "No significant red flags")
        
        return {
            'score': score,
            'confidence': confidence,
            'details': details,
            'flags': flags
        }
    
    def _process_source_credibility(self, source_data: Dict) -> Dict:
        """Process source credibility assessment"""
        if not source_data:
            return {'score': 0.5, 'confidence': 0.0, 'details': 'No source information available'}
        
        score = 0.5  # Neutral starting point
        confidence = 0.4
        
        source_type = source_data.get('type', 'unknown')
        domain = source_data.get('domain', '')
        
        # Known reliable domains (simplified list)
        reliable_domains = {
            'bbc.com': 0.9,
            'reuters.com': 0.9,
            'ap.org': 0.9,
            'cnn.com': 0.8,
            'nytimes.com': 0.8,
            'washingtonpost.com': 0.8,
            'theguardian.com': 0.8,
            'npr.org': 0.8,
            'abscbn.com': 0.7,
            'gmanetwork.com': 0.7,
            'inquirer.net': 0.7,
            'rappler.com': 0.7
        }
        
        # Known unreliable domains (simplified list)
        unreliable_domains = {
            'fake-news-site.com': 0.1,
            'clickbait-news.com': 0.2,
            'conspiracy-theories.com': 0.1
        }
        
        if domain in reliable_domains:
            score = reliable_domains[domain]
            confidence = 0.8
        elif domain in unreliable_domains:
            score = unreliable_domains[domain]
            confidence = 0.8
        elif domain.endswith('.gov') or domain.endswith('.edu'):
            score = 0.85
            confidence = 0.7
        elif source_type == 'facebook':
            score = 0.4  # Social media generally less reliable
            confidence = 0.5
        elif source_type == 'user_input':
            score = 0.5  # Neutral for user-provided text
            confidence = 0.3
        
        details = f"Source: {source_type}" + (f" ({domain})" if domain else "")
        
        return {
            'score': score,
            'confidence': confidence,
            'details': details,
            'domain': domain,
            'source_type': source_type
        }
    
    def _calculate_confidence(self, component_scores: Dict) -> float:
        """Calculate overall confidence based on component confidences"""
        confidences = []
        
        for component, data in component_scores.items():
            component_confidence = data.get('confidence', 0.0)
            confidences.append(component_confidence)
        
        if not confidences:
            return 0.0
        
        # Use weighted average of confidences
        weights = list(self.weights.values())
        weighted_confidence = sum(c * w for c, w in zip(confidences, weights))
        
        # Apply confidence modifiers
        # Higher confidence if multiple sources agree
        agreement_bonus = 0.0
        scores = [data.get('score', 0.5) for data in component_scores.values()]
        if len(scores) > 1:
            score_variance = np.var(scores)
            if score_variance < 0.1:  # Low variance = high agreement
                agreement_bonus = 0.1
        
        final_confidence = min(1.0, weighted_confidence + agreement_bonus)
        return final_confidence
    
    def _determine_verdict(self, score: float, confidence: float) -> str:
        """Determine final verdict based on score and confidence"""
        if confidence < 0.3:
            return "Insufficient Evidence"
        
        if score >= 0.8:
            return "Highly Credible" if confidence >= 0.7 else "Likely Credible"
        elif score >= 0.6:
            return "Mostly Credible" if confidence >= 0.6 else "Leaning Credible"
        elif score >= 0.4:
            return "Mixed Evidence" if confidence >= 0.5 else "Uncertain"
        elif score >= 0.2:
            return "Mostly Unreliable" if confidence >= 0.6 else "Leaning Unreliable"
        else:
            return "Highly Unreliable" if confidence >= 0.7 else "Likely Unreliable"
    
    def _generate_explanation(self, component_scores: Dict, final_score: float, confidence: float) -> str:
        """Generate human-readable explanation of the credibility assessment"""
        explanation_parts = []
        
        # Overall assessment
        explanation_parts.append(f"Overall credibility score: {final_score:.2f} (confidence: {confidence:.2f})")
        
        # Key contributing factors
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: abs(x[1].get('score', 0.5) - 0.5),
            reverse=True
        )
        
        explanation_parts.append("\nKey factors:")
        
        for component, data in sorted_components[:3]:  # Top 3 most significant factors
            score = data.get('score', 0.5)
            details = data.get('details', 'No details available')
            
            if score >= 0.7:
                impact = "supports credibility"
            elif score <= 0.3:
                impact = "raises concerns"
            else:
                impact = "neutral impact"
            
            explanation_parts.append(f"• {component.replace('_', ' ').title()}: {details} ({impact})")
        
        # Confidence factors
        if confidence < 0.5:
            explanation_parts.append("\nNote: Low confidence due to limited or conflicting evidence.")
        elif confidence >= 0.8:
            explanation_parts.append("\nNote: High confidence based on multiple consistent sources.")
        
        return "\n".join(explanation_parts)
    
    def get_credibility_level_info(self, score: float) -> Dict:
        """Get detailed information about a credibility level"""
        if score >= 0.8:
            return {
                'level': 'High',
                'color': '#22C55E',  # Green
                'description': 'This content appears to be highly credible based on multiple verification methods.',
                'recommendation': 'Safe to share and trust this information.'
            }
        elif score >= 0.6:
            return {
                'level': 'Medium-High',
                'color': '#84CC16',  # Light green
                'description': 'This content appears to be mostly credible with minor concerns.',
                'recommendation': 'Generally trustworthy, but verify important details.'
            }
        elif score >= 0.4:
            return {
                'level': 'Medium',
                'color': '#F59E0B',  # Yellow
                'description': 'This content has mixed credibility indicators.',
                'recommendation': 'Exercise caution and seek additional verification.'
            }
        elif score >= 0.2:
            return {
                'level': 'Low',
                'color': '#F97316',  # Orange
                'description': 'This content shows several indicators of unreliability.',
                'recommendation': 'Be very cautious and verify through reliable sources.'
            }
        else:
            return {
                'level': 'Very Low',
                'color': '#DC2626',  # Red
                'description': 'This content appears to be highly unreliable or potentially false.',
                'recommendation': 'Do not share. Likely misinformation.'
            }