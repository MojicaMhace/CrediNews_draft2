import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional

class FacebookService:
    def __init__(self):
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.app_id = os.getenv('FACEBOOK_APP_ID')
        self.app_secret = os.getenv('FACEBOOK_APP_SECRET')
        self.base_url = 'https://graph.facebook.com/v18.0'
        
        if not self.access_token:
            raise ValueError("Facebook access token not found in environment variables")
    
    def get_page_posts(self, page_id: str, limit: int = 50) -> Dict:
        """Get posts from a Facebook page"""
        try:
            url = f"{self.base_url}/{page_id}/posts"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,story,created_time,updated_time,type,link,name,description,caption,picture,full_picture,shares,reactions.summary(true),comments.summary(true)',
                'limit': limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page posts: {e}")
            return {'data': [], 'error': str(e)}
    
    def get_post_details(self, post_id: str) -> Dict:
        """Get detailed information about a specific post"""
        try:
            url = f"{self.base_url}/{post_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,story,created_time,updated_time,type,link,name,description,caption,picture,full_picture,shares,reactions.summary(true),comments.summary(true),from'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching post details: {e}")
            return {'error': str(e)}
    
    def get_page_info(self, page_id: str) -> Dict:
        """Get information about a Facebook page"""
        try:
            url = f"{self.base_url}/{page_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'id,name,username,about,category,created_time,fan_count,followers_count,verification_status,is_verified,website,location'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page info: {e}")
            return {'error': str(e)}
    
    def search_posts(self, query: str, limit: int = 25) -> Dict:
        """Search for posts containing specific keywords"""
        try:
            url = f"{self.base_url}/search"
            params = {
                'access_token': self.access_token,
                'q': query,
                'type': 'post',
                'fields': 'id,message,story,created_time,type,link,from',
                'limit': limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching posts: {e}")
            return {'data': [], 'error': str(e)}
    
    def analyze_account_activity(self, page_id: str) -> Dict:
        """Analyze account activity for poser detection"""
        try:
            # Get page info
            page_info = self.get_page_info(page_id)
            if 'error' in page_info:
                return page_info
            
            # Get recent posts
            posts_data = self.get_page_posts(page_id, limit=100)
            if 'error' in posts_data:
                return posts_data
            
            posts = posts_data.get('data', [])
            
            # Calculate activity metrics
            now = datetime.now()
            recent_posts = []
            total_engagement = 0
            
            for post in posts:
                created_time = datetime.strptime(post['created_time'], '%Y-%m-%dT%H:%M:%S%z')
                days_ago = (now - created_time.replace(tzinfo=None)).days
                
                if days_ago <= 30:  # Posts from last 30 days
                    recent_posts.append(post)
                
                # Calculate engagement
                reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
                comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                shares = post.get('shares', {}).get('count', 0)
                
                total_engagement += reactions + comments + shares
            
            # Calculate metrics
            posting_frequency = len(recent_posts) / 30 if recent_posts else 0
            avg_engagement = total_engagement / len(posts) if posts else 0
            
            # Determine suspicion level
            suspicion_score = 0
            flags = []
            
            # Check verification status
            if not page_info.get('is_verified', False):
                suspicion_score += 1
                flags.append('Not verified')
            
            # Check account age
            if 'created_time' in page_info:
                created_time = datetime.strptime(page_info['created_time'], '%Y-%m-%dT%H:%M:%S%z')
                account_age_days = (now - created_time.replace(tzinfo=None)).days
                
                if account_age_days < 30:
                    suspicion_score += 2
                    flags.append('Very new account (< 30 days)')
                elif account_age_days < 90:
                    suspicion_score += 1
                    flags.append('New account (< 90 days)')
            
            # Check posting patterns
            if posting_frequency > 10:  # More than 10 posts per day
                suspicion_score += 2
                flags.append('Extremely high posting frequency')
            elif posting_frequency > 5:
                suspicion_score += 1
                flags.append('High posting frequency')
            
            # Check follower count vs engagement ratio
            follower_count = page_info.get('fan_count', 0)
            if follower_count > 0 and avg_engagement > 0:
                engagement_ratio = avg_engagement / follower_count
                if engagement_ratio > 0.1:  # Very high engagement ratio might indicate fake engagement
                    suspicion_score += 1
                    flags.append('Unusually high engagement ratio')
                elif engagement_ratio < 0.001:  # Very low engagement might indicate bought followers
                    suspicion_score += 1
                    flags.append('Unusually low engagement ratio')
            
            # Determine risk level
            if suspicion_score >= 4:
                risk_level = 'HIGH'
            elif suspicion_score >= 2:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'page_info': page_info,
                'activity_metrics': {
                    'total_posts': len(posts),
                    'recent_posts_30d': len(recent_posts),
                    'posting_frequency_per_day': round(posting_frequency, 2),
                    'average_engagement': round(avg_engagement, 2),
                    'follower_count': follower_count,
                    'account_age_days': account_age_days if 'created_time' in page_info else None
                },
                'poser_analysis': {
                    'suspicion_score': suspicion_score,
                    'risk_level': risk_level,
                    'flags': flags,
                    'is_verified': page_info.get('is_verified', False)
                }
            }
            
        except Exception as e:
            print(f"Error analyzing account activity: {e}")
            return {'error': str(e)}
    
    def extract_news_content(self, posts: List[Dict]) -> List[Dict]:
        """Extract and structure news content from posts"""
        news_items = []
        
        for post in posts:
            # Extract text content
            content = post.get('message', '') or post.get('story', '')
            
            # Skip posts without meaningful content
            if not content or len(content.strip()) < 10:
                continue
            
            # Check if post contains news-like content
            news_keywords = ['breaking', 'news', 'report', 'update', 'alert', 'announcement', 
                           'confirmed', 'official', 'statement', 'press release']
            
            content_lower = content.lower()
            has_news_keywords = any(keyword in content_lower for keyword in news_keywords)
            
            # Extract structured data
            news_item = {
                'post_id': post.get('id'),
                'content': content,
                'link': post.get('link'),
                'created_time': post.get('created_time'),
                'post_type': post.get('type'),
                'source_page': post.get('from', {}).get('name', 'Unknown'),
                'source_page_id': post.get('from', {}).get('id'),
                'engagement': {
                    'reactions': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
                    'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                    'shares': post.get('shares', {}).get('count', 0)
                },
                'has_news_keywords': has_news_keywords,
                'media': {
                    'picture': post.get('picture'),
                    'full_picture': post.get('full_picture')
                }
            }
            
            news_items.append(news_item)
        
        return news_items
    
    def validate_access_token(self) -> bool:
        """Validate if the access token is still valid"""
        try:
            url = f"{self.base_url}/me"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params)
            return response.status_code == 200
            
        except:
            return False