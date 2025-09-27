import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class FirebaseService:
    def __init__(self):
        self.db = None
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to get credentials from environment variable (JSON string)
                firebase_service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
                
                if firebase_service_account_key:
                    # Parse JSON string from environment variable
                    try:
                        config_dict = json.loads(firebase_service_account_key)
                        cred = credentials.Certificate(config_dict)
                        print("Using Firebase service account key from environment variable")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing Firebase service account key: {e}")
                        raise
                else:
                    # Fallback to service account file
                    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
                    if os.path.exists(service_account_path):
                        cred = credentials.Certificate(service_account_path)
                        print("Using Firebase service account key from file")
                    else:
                        print("Warning: Firebase credentials not found. Using default credentials.")
                        cred = credentials.ApplicationDefault()
                
                # Initialize the app with project configuration
                firebase_config = {
                    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                }
                
                self.app = firebase_admin.initialize_app(cred, firebase_config)
            else:
                self.app = firebase_admin.get_app()
            
            # Initialize Firestore
            self.db = firestore.client()
            print("Firebase initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.db = None
    
    def create_user_profile(self, uid: str, email: str, display_name: str = None) -> bool:
        """Create a user profile in Firestore"""
        if not self.db:
            return False
        
        try:
            user_data = {
                'uid': uid,
                'email': email,
                'display_name': display_name or email.split('@')[0],
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'news_analyses_count': 0,
                'preferences': {
                    'theme': 'light',
                    'language': 'en',
                    'notifications': True
                }
            }
            
            self.db.collection('users').document(uid).set(user_data)
            return True
            
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def get_user_profile(self, uid: str) -> Optional[Dict]:
        """Get user profile from Firestore"""
        if not self.db:
            return None
        
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, uid: str, updates: Dict) -> bool:
        """Update user profile in Firestore"""
        if not self.db:
            return False
        
        try:
            updates['updated_at'] = datetime.now()
            self.db.collection('users').document(uid).update(updates)
            return True
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def save_analysis_result(self, uid: str, analysis_data: Dict) -> str:
        """Save news analysis result to Firestore"""
        if not self.db:
            return None
        
        try:
            # Prepare analysis document
            analysis_doc = {
                'user_id': uid,
                'timestamp': datetime.now(),
                'input_text': analysis_data.get('input_text', ''),
                'input_url': analysis_data.get('input_url', ''),
                'input_type': analysis_data.get('input_type', 'text'),
                'ml_prediction': analysis_data.get('ml_prediction', {}),
                'factcheck_results': analysis_data.get('factcheck_results', {}),
                'poser_analysis': analysis_data.get('poser_analysis', {}),
                'preprocessing_results': analysis_data.get('preprocessing_results', {}),
                'final_credibility_score': analysis_data.get('final_credibility_score', 0.5),
                'verdict': analysis_data.get('verdict', 'Unknown'),
                'confidence': analysis_data.get('confidence', 0.0)
            }
            
            # Add to news_verifications collection
            doc_ref = self.db.collection('news_verifications').add(analysis_doc)
            analysis_id = doc_ref[1].id
            
            # Update user's analysis count
            user_ref = self.db.collection('users').document(uid)
            user_ref.update({
                'news_analyses_count': firestore.Increment(1),
                'last_news_analysis_date': datetime.now()
            })
            
            return analysis_id
            
        except Exception as e:
            print(f"Error saving analysis result: {e}")
            return None
    
    def get_user_news_verifications(self, uid: str, limit: int = 50) -> List[Dict]:
        """Get user's news verification history"""
        if not self.db:
            return []
        
        try:
            news_verifications = []
            docs = (self.db.collection('news_verifications')
                   .where('user_id', '==', uid)
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
            
            for doc in docs:
                verification = doc.to_dict()
                verification['id'] = doc.id
                news_verifications.append(verification)
            
            return news_verifications
            
        except Exception as e:
            print(f"Error getting user news verifications: {e}")
            return []
    
    def get_news_verification_by_id(self, verification_id: str) -> Optional[Dict]:
        """Get specific news verification by ID"""
        if not self.db:
            return None
        
        try:
            doc = self.db.collection('news_verifications').document(verification_id).get()
            if doc.exists:
                verification = doc.to_dict()
                verification['id'] = doc.id
                return verification
            return None
            
        except Exception as e:
            print(f"Error getting news verification: {e}")
            return None
    
    def save_misinformation_trend(self, trend_data: Dict) -> bool:
        """Save misinformation trend data"""
        if not self.db:
            return False
        
        try:
            trend_doc = {
                'date': datetime.now().date(),
                'total_news_verifications': trend_data.get('total_news_verifications', 0),
                'fake_news_count': trend_data.get('fake_news_count', 0),
                'real_news_count': trend_data.get('real_news_count', 0),
                'fake_percentage': trend_data.get('fake_percentage', 0.0),
                'top_keywords': trend_data.get('top_keywords', []),
                'source_breakdown': trend_data.get('source_breakdown', {}),
                'timestamp': datetime.now()
            }
            
            # Use date as document ID to avoid duplicates
            date_str = datetime.now().strftime('%Y-%m-%d')
            self.db.collection('trends').document(date_str).set(trend_doc, merge=True)
            
            return True
            
        except Exception as e:
            print(f"Error saving trend data: {e}")
            return False
    
    def get_misinformation_trends(self, days: int = 30) -> List[Dict]:
        """Get misinformation trends for the last N days"""
        if not self.db:
            return []
        
        try:
            trends = []
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            docs = (self.db.collection('trends')
                   .where('date', '>=', start_date)
                   .where('date', '<=', end_date)
                   .order_by('date')
                   .stream())
            
            for doc in docs:
                trend = doc.to_dict()
                trend['id'] = doc.id
                trends.append(trend)
            
            return trends
            
        except Exception as e:
            print(f"Error getting trends: {e}")
            return []
    
    def verify_user_token(self, id_token: str) -> Optional[Dict]:
        """Verify Firebase ID token"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled
            }
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def update_user_login(self, uid: str) -> bool:
        """Update user's last login timestamp"""
        if not self.db:
            return False
        
        try:
            self.db.collection('users').document(uid).update({
                'last_login': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error updating user login: {e}")
            return False
    
    def get_system_stats(self) -> Dict:
        """Get system-wide statistics"""
        if not self.db:
            return {}
        
        try:
            stats = {
                'total_users': 0,
                'total_news_verifications': 0,
                'news_verifications_today': 0,
                'fake_news_detected': 0
            }
            
            # Count total users
            users_count = len(list(self.db.collection('users').stream()))
            stats['total_users'] = users_count
            
            # Count total news verifications
            verifications_count = len(list(self.db.collection('news_verifications').stream()))
            stats['total_news_verifications'] = verifications_count
            
            # Count news verifications today
            today = datetime.now().date()
            today_verifications = self.db.collection('news_verifications').where(
                'timestamp', '>=', datetime.combine(today, datetime.min.time())
            ).stream()
            stats['news_verifications_today'] = len(list(today_verifications))
            
            # Count fake news detected
            fake_verifications = self.db.collection('news_verifications').where(
                'final_credibility_score', '<', 0.5
            ).stream()
            stats['fake_news_detected'] = len(list(fake_verifications))
            
            return stats
            
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {}