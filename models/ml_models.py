import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os
import joblib

class FakeNewsDetector:
    def __init__(self, model_path='./data/models/'):
        self.model_path = model_path
        self.vectorizer = None
        self.ensemble_model = None
        self.models = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'naive_bayes': MultinomialNB(),
            'svm': SVC(probability=True, random_state=42)
        }
        self.is_trained = False
        
        # Try to load pre-trained models
        self.load_models()
    
    def preprocess_data(self, texts, labels=None):
        """Preprocess text data for training or prediction"""
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95
            )
            
        if labels is not None:  # Training mode
            X = self.vectorizer.fit_transform(texts)
            return X, labels
        else:  # Prediction mode
            X = self.vectorizer.transform(texts)
            return X
    
    def train(self, texts, labels):
        """Train the ensemble model with multiple algorithms"""
        print("Training fake news detection models...")
        
        # Preprocess data
        X, y = self.preprocess_data(texts, labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train individual models
        trained_models = []
        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            
            # Evaluate individual model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"{name} accuracy: {accuracy:.4f}")
            
            trained_models.append((name, model))
        
        # Create ensemble model
        self.ensemble_model = VotingClassifier(
            estimators=trained_models,
            voting='soft'  # Use probability-based voting
        )
        
        # Train ensemble
        print("Training ensemble model...")
        self.ensemble_model.fit(X_train, y_train)
        
        # Evaluate ensemble
        y_pred_ensemble = self.ensemble_model.predict(X_test)
        ensemble_accuracy = accuracy_score(y_test, y_pred_ensemble)
        print(f"Ensemble accuracy: {ensemble_accuracy:.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred_ensemble))
        
        self.is_trained = True
        
        # Save models
        self.save_models()
        
        return ensemble_accuracy
    
    def predict(self, texts):
        """Predict if news is fake or real"""
        if not self.is_trained or self.ensemble_model is None:
            # Use a simple rule-based approach if models aren't trained
            return self._fallback_prediction(texts)
        
        # Handle single text input
        if isinstance(texts, str):
            texts = [texts]
        
        # Preprocess
        X = self.preprocess_data(texts)
        
        # Get predictions and probabilities
        predictions = self.ensemble_model.predict(X)
        probabilities = self.ensemble_model.predict_proba(X)
        
        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            confidence = max(prob)
            label = 'fake' if pred == 1 else 'real'
            
            # Get individual model predictions for transparency
            individual_preds = {}
            for name, model in self.models.items():
                try:
                    ind_pred = model.predict(X[i:i+1])[0]
                    ind_prob = model.predict_proba(X[i:i+1])[0]
                    individual_preds[name] = {
                        'prediction': 'fake' if ind_pred == 1 else 'real',
                        'confidence': max(ind_prob)
                    }
                except:
                    individual_preds[name] = {
                        'prediction': 'unknown',
                        'confidence': 0.5
                    }
            
            results.append({
                'prediction': label,
                'confidence': float(confidence),
                'probability_fake': float(prob[1]) if len(prob) > 1 else 0.0,
                'probability_real': float(prob[0]),
                'individual_models': individual_preds
            })
        
        return results[0] if len(results) == 1 else results
    
    def _fallback_prediction(self, texts):
        """Simple rule-based fallback when ML models aren't available"""
        if isinstance(texts, str):
            texts = [texts]
        
        results = []
        for text in texts:
            # Simple heuristics for fake news detection
            fake_indicators = [
                'breaking:', 'urgent:', 'shocking:', 'unbelievable:',
                'you won\'t believe', 'doctors hate', 'this one trick',
                'click here', 'share if you agree'
            ]
            
            text_lower = text.lower()
            fake_score = sum(1 for indicator in fake_indicators if indicator in text_lower)
            
            # Simple scoring
            if fake_score >= 2:
                prediction = 'fake'
                confidence = min(0.7 + fake_score * 0.1, 0.95)
            else:
                prediction = 'real'
                confidence = max(0.6 - fake_score * 0.1, 0.55)
            
            results.append({
                'prediction': prediction,
                'confidence': confidence,
                'probability_fake': 1 - confidence if prediction == 'real' else confidence,
                'probability_real': confidence if prediction == 'real' else 1 - confidence,
                'individual_models': {
                    'rule_based': {
                        'prediction': prediction,
                        'confidence': confidence
                    }
                },
                'note': 'Using rule-based fallback - ML models not trained'
            })
        
        return results[0] if len(results) == 1 else results
    
    def save_models(self):
        """Save trained models and vectorizer"""
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
        
        # Save vectorizer
        joblib.dump(self.vectorizer, os.path.join(self.model_path, 'vectorizer.pkl'))
        
        # Save ensemble model
        joblib.dump(self.ensemble_model, os.path.join(self.model_path, 'ensemble_model.pkl'))
        
        # Save individual models
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(self.model_path, f'{name}.pkl'))
        
        print(f"Models saved to {self.model_path}")
    
    def load_models(self):
        """Load pre-trained models and vectorizer"""
        try:
            vectorizer_path = os.path.join(self.model_path, 'vectorizer.pkl')
            ensemble_path = os.path.join(self.model_path, 'ensemble_model.pkl')
            
            if os.path.exists(vectorizer_path) and os.path.exists(ensemble_path):
                self.vectorizer = joblib.load(vectorizer_path)
                self.ensemble_model = joblib.load(ensemble_path)
                
                # Load individual models
                for name in self.models.keys():
                    model_path = os.path.join(self.model_path, f'{name}.pkl')
                    if os.path.exists(model_path):
                        self.models[name] = joblib.load(model_path)
                
                self.is_trained = True
                print("Pre-trained models loaded successfully")
            else:
                print("No pre-trained models found. Will use fallback prediction.")
        except Exception as e:
            print(f"Error loading models: {e}")
            self.is_trained = False
    
    def create_sample_training_data(self):
        """Create sample training data for demonstration"""
        fake_news_samples = [
            "BREAKING: Scientists discover this one weird trick that doctors don't want you to know!",
            "URGENT: Government hiding the truth about vaccines! Share before they delete this!",
            "You won't believe what happened next! This shocking discovery will change everything!",
            "EXPOSED: The real reason why they don't want you to know this secret!",
            "This miracle cure that Big Pharma doesn't want you to see!",
            "SHOCKING: Celebrity dies in mysterious circumstances! Click to see photos!",
            "WARNING: This everyday item is slowly killing you! Doctors hate this!",
            "UNBELIEVABLE: Local mom discovers amazing weight loss secret!"
        ]
        
        real_news_samples = [
            "The Philippine Stock Exchange closed higher today following positive economic indicators.",
            "Local government announces new infrastructure projects to improve transportation.",
            "University researchers publish findings on climate change adaptation strategies.",
            "Health department reports successful vaccination campaign in rural areas.",
            "Technology company launches new educational program for students.",
            "Agricultural department introduces sustainable farming practices.",
            "Central bank maintains interest rates amid stable economic conditions.",
            "Environmental agency implements new conservation measures for marine life."
        ]
        
        texts = fake_news_samples + real_news_samples
        labels = [1] * len(fake_news_samples) + [0] * len(real_news_samples)  # 1 = fake, 0 = real
        
        return texts, labels

# Initialize the detector
fake_news_detector = FakeNewsDetector()

# Train with sample data if no models exist
if not fake_news_detector.is_trained:
    print("Training with sample data...")
    texts, labels = fake_news_detector.create_sample_training_data()
    fake_news_detector.train(texts, labels)