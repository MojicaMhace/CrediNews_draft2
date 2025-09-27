from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
import os
from datetime import datetime, timedelta
import json
import logging
from werkzeug.exceptions import RequestEntityTooLarge

# Import our custom modules
from models.ml_models import FakeNewsDetector
from services.facebook_service import FacebookService
from services.factcheck_service import FactCheckService
from services.firebase_service import FirebaseService
from utils.preprocessor import TextPreprocessor
from utils.credibility_scorer import CredibilityScorer
from utils.analysis_engine import NewsAnalysisEngine

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
try:
    firebase_service = FirebaseService()
    facebook_service = FacebookService()
    factcheck_service = FactCheckService()
    text_preprocessor = TextPreprocessor()
    fake_news_detector = FakeNewsDetector()
    credibility_scorer = CredibilityScorer()
    
    # Initialize analysis engine (it creates its own components internally)
    analysis_engine = NewsAnalysisEngine()
    
    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    # Initialize with None for graceful degradation
    analysis_engine = None

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        try:
            return firebase_service.get_user_profile(session['user_id'])
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            session.clear()
    return None

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

@app.errorhandler(RequestEntityTooLarge)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 16MB.'
    }), 413

# Context processor to make current_user available to all templates
@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# Routes
@app.route('/')
def index():
    """Home page with dashboard overview"""
    try:
        # Get system statistics
        system_stats = {
            'total_news_verifications': 0,
            'fake_detected': 0,
            'accuracy_rate': 0,
            'posers_detected': 0
        }
        
        # Get recent activity for authenticated users
        recent_activity = []
        current_user = get_current_user()
        
        if current_user and analysis_engine:
            try:
                recent_activity = analysis_engine.get_user_analysis_history(
                    current_user['uid'], limit=5
                )
                # Get system stats from Firebase
                system_stats = firebase_service.get_system_stats()
            except Exception as e:
                logger.error(f"Error getting user data: {str(e)}")
        
        # Get misinformation trends
        trends_data = []
        trending_stats = {
            'avg_daily': 23,
            'peak_day': 45,
            'political': 156,
            'health': 89,
            'technology': 67,
            'social': 34,
            'economic': 21
        }
        
        if analysis_engine:
            try:
                trends_data = firebase_service.get_misinformation_trends(days=7)
                # Try to get real trending stats from Firebase
                real_trending_stats = firebase_service.get_trending_stats()
                if real_trending_stats:
                    trending_stats.update(real_trending_stats)
            except Exception as e:
                logger.error(f"Error getting trends: {str(e)}")
        
        return render_template('dashboard.html',
                             current_user=current_user,
                             system_stats=system_stats,
                             recent_activity=recent_activity,
                             trends_data=trends_data,
                             trending_stats=trending_stats)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('dashboard.html',
                             current_user=None,
                             system_stats={'total_news_verifications': 0, 'fake_detected': 0, 'accuracy_rate': 0, 'posers_detected': 0},
                             recent_activity=[],
                             trends_data=[],
                             trending_stats={'avg_daily': 23, 'peak_day': 45, 'political': 156, 'health': 89, 'technology': 67, 'social': 34, 'economic': 21})

@app.route('/analyze')
def analyze():
    """Analysis page"""
    current_user = get_current_user()
    return render_template('analyze.html', current_user=current_user)

@app.route('/login')
def login():
    """Login page"""
    # Redirect if already logged in
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    """User dashboard page"""
    try:
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('login'))
        
        # Get user statistics
        user_stats = {
            'total_news_verifications': 0,
            'accuracy_rate': 0,
            'days_active': 0,
            'news_verifications_this_week': 0,
            'fake_detected': 0,
            'fake_percentage': 0,
            'verified_news': 0,
            'verified_percentage': 0,
            'avg_score': 0.0
        }
        
        # Get user analysis history
        user_news_verifications = []
        recent_news_verifications = []
        content_stats = {'text': 0, 'url': 0, 'facebook': 0}
        user_topics = []
        
        if analysis_engine:
            try:
                user_news_verifications = analysis_engine.get_user_analysis_history(current_user['uid'])
                recent_news_verifications = user_news_verifications[:5] if user_news_verifications else []
                
                # Calculate user statistics
                if user_news_verifications:
                    user_stats['total_news_verifications'] = len(user_news_verifications)
                    
                    # Count by type
                    for verification in user_news_verifications:
                        content_stats[verification.get('input_type', 'text')] += 1
                    
                    # Calculate other stats
                    fake_count = sum(1 for v in user_news_verifications if v.get('verdict') == 'FAKE')
                    user_stats['fake_detected'] = fake_count
                    user_stats['fake_percentage'] = round((fake_count / len(user_news_verifications)) * 100, 1)
                    
                    verified_count = sum(1 for v in user_news_verifications if v.get('verdict') == 'REAL')
                    user_stats['verified_news'] = verified_count
                    user_stats['verified_percentage'] = round((verified_count / len(user_news_verifications)) * 100, 1)
                    
                    # Average credibility score
                    scores = [v.get('credibility_score', 0) for v in user_news_verifications]
                    user_stats['avg_score'] = round(sum(scores) / len(scores), 1) if scores else 0
                    
                    # News verifications this week
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    user_stats['news_verifications_this_week'] = sum(
                        1 for v in user_news_verifications 
                        if datetime.fromisoformat(v.get('created_at', '').replace('Z', '+00:00')) > week_ago
                    )
                    
            except Exception as e:
                logger.error(f"Error getting user statistics: {str(e)}")
        
        return render_template('user_dashboard.html',
                             current_user=current_user,
                             user_stats=user_stats,
                             user_news_verifications=user_news_verifications,
                             recent_news_verifications=recent_news_verifications,
                             content_stats=content_stats,
                             user_topics=user_topics)
                             
    except Exception as e:
        logger.error(f"Error in user dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for news analysis"""
    try:
        if not analysis_engine:
            return jsonify({
                'success': False,
                'error': 'Analysis engine not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        input_type = data.get('type')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content cannot be empty'
            }), 400
        
        if not input_type or input_type not in ['text', 'url', 'facebook']:
            return jsonify({
                'success': False,
                'error': 'Invalid input type'
            }), 400
        
        # Get current user for saving results
        current_user = get_current_user()
        user_id = current_user['uid'] if current_user else None
        
        # Perform analysis
        result = analysis_engine.analyze_news(
            content=content,
            input_type=input_type,
            user_id=user_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'analysis_id': result.get('analysis_id'),
                'verdict': result['verdict'],
                'credibility_score': result['credibility_score'],
                'confidence': result['confidence'],
                'explanation': result['explanation'],
                'ml_prediction': result.get('ml_prediction', {}),
                'fact_check_results': result.get('fact_check_results', []),
                'poser_detection': result.get('poser_detection', {}),
                'source_credibility': result.get('source_credibility', {}),
                'processing_time': result.get('processing_time', 0)
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Analysis failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in analyze API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during analysis'
        }), 500

@app.route('/trends')
def trends():
    """Misinformation trends page"""
    current_user = get_current_user()
    
    # Get trends data
    trends_data = {
        'detection_rate': [],
        'category_distribution': [],
        'source_credibility': [],
        'trending_keywords': [],
        'fake_news_patterns': [],
        'high_risk_sources': []
    }
    
    if analysis_engine:
        try:
            # Get various trend metrics
            trends_data['detection_rate'] = firebase_service.get_detection_rate_trends(days=30)
            trends_data['category_distribution'] = firebase_service.get_category_distribution()
            trends_data['trending_keywords'] = firebase_service.get_trending_keywords(limit=10)
            trends_data['fake_news_patterns'] = firebase_service.get_fake_news_patterns(limit=5)
            trends_data['high_risk_sources'] = firebase_service.get_high_risk_sources(limit=10)
        except Exception as e:
            logger.error(f"Error getting trends data: {str(e)}")
    
    return render_template('trends.html',
                         current_user=current_user,
                         trends_data=trends_data)

@app.route('/api/trends')
def api_trends():
    """API endpoint for trends data"""
    try:
        time_range = request.args.get('range', '7')  # days
        
        if not analysis_engine:
            return jsonify({
                'success': False,
                'error': 'Service not available'
            }), 503
        
        trends_data = {
            'total_news_verifications': firebase_service.get_total_news_verifications(days=int(time_range)),
            'fake_detected': firebase_service.get_fake_detected(days=int(time_range)),
            'accuracy_rate': firebase_service.get_accuracy_rate(days=int(time_range)),
            'posers_detected': firebase_service.get_posers_detected(days=int(time_range)),
            'detection_rate_chart': firebase_service.get_detection_rate_trends(days=int(time_range)),
            'category_chart': firebase_service.get_category_distribution(days=int(time_range)),
            'source_credibility_chart': firebase_service.get_source_credibility_trends(days=int(time_range))
        }
        
        return jsonify({
            'success': True,
            'data': trends_data
        })
        
    except Exception as e:
        logger.error(f"Error in trends API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch trends data'
        }), 500

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Handle Google authentication"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({
                'success': False,
                'error': 'No ID token provided'
            }), 400
        
        # Verify token with Firebase
        user_info = firebase_service.verify_user_token(id_token)
        
        if user_info:
            # Create or update user profile
            user_profile = {
                'uid': user_info['uid'],
                'email': user_info['email'],
                'display_name': user_info.get('name', ''),
                'photo_url': user_info.get('picture', ''),
                'last_login': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            firebase_service.create_or_update_user_profile(user_info['uid'], user_profile)
            
            # Set session
            session['user_id'] = user_info['uid']
            session['user_email'] = user_info['email']
            
            return jsonify({
                'success': True,
                'user': {
                    'uid': user_info['uid'],
                    'email': user_info['email'],
                    'displayName': user_info.get('name', ''),
                    'photoURL': user_info.get('picture', '')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 401
            
    except Exception as e:
        logger.error(f"Error in Google auth: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Authentication failed'
        }), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/api/analysis/<analysis_id>')
@login_required
def get_analysis(analysis_id):
    """Get specific analysis details"""
    try:
        current_user = get_current_user()
        if not current_user or not analysis_engine:
            return jsonify({
                'success': False,
                'error': 'Unauthorized or service unavailable'
            }), 401
        
        analysis = analysis_engine.get_analysis_result(analysis_id)
        
        if analysis and analysis.get('user_id') == current_user['uid']:
            return jsonify({
                'success': True,
                'analysis': analysis
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Analysis not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analysis'
        }), 500

@app.route('/api/user/export')
@login_required
def export_user_data():
    """Export user data"""
    try:
        current_user = get_current_user()
        if not current_user or not analysis_engine:
            return jsonify({
                'success': False,
                'error': 'Unauthorized or service unavailable'
            }), 401
        
        # Get all user data
        user_data = {
            'profile': current_user,
            'news_verifications': analysis_engine.get_user_analysis_history(current_user['uid']),
            'exported_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': user_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export data'
        }), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'analysis_engine': analysis_engine is not None,
            'firebase': firebase_service is not None,
            'facebook': facebook_service is not None,
            'factcheck': factcheck_service is not None
        }
    }
    
    return jsonify(status)

if __name__ == '__main__':
    # Set up logging for production
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/credinews.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('CrediNews startup')
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)