"""
Facebook Graph API service for posting to Facebook Page.

Requires environment variables:
- FACEBOOK_PAGE_ID: Your Facebook Page ID (e.g., 61584437267769)
- FACEBOOK_PAGE_TOKEN: Long-lived Page Access Token with pages_manage_posts permission

Setup instructions:
1. Go to developers.facebook.com and create an app
2. Add "Facebook Login" and "Pages" products
3. Get Page Access Token from Graph API Explorer
4. Convert to long-lived token (60+ days)
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# Facebook API configuration
FACEBOOK_PAGE_ID = os.environ.get('FACEBOOK_PAGE_ID', '61584437267769')
FACEBOOK_PAGE_TOKEN = os.environ.get('FACEBOOK_PAGE_TOKEN')
FACEBOOK_API_VERSION = 'v18.0'
FACEBOOK_ENABLED = bool(FACEBOOK_PAGE_TOKEN)


class FacebookService:
    """Service for posting to Facebook Page"""

    def __init__(self):
        self.page_id = FACEBOOK_PAGE_ID
        self.access_token = FACEBOOK_PAGE_TOKEN
        self.api_version = FACEBOOK_API_VERSION
        self.enabled = FACEBOOK_ENABLED
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def post_text(self, message: str) -> dict:
        """
        Post a text message to Facebook Page.

        Args:
            message: The text content to post

        Returns:
            dict with 'status' ('success' or 'failed') and 'post_id' or 'error'
        """
        if not self.enabled:
            logger.info(f"[DEV MODE] Would post to Facebook: {message[:100]}...")
            return {'status': 'dev_mode', 'post_id': None, 'message': 'Facebook posting disabled - no token configured'}

        url = f"{self.base_url}/{self.page_id}/feed"
        data = {
            'message': message,
            'access_token': self.access_token
        }

        try:
            response = requests.post(url, data=data, timeout=30)
            response_data = response.json()

            if response.status_code == 200 and 'id' in response_data:
                post_id = response_data['id']
                logger.info(f"Successfully posted to Facebook: {post_id}")
                return {'status': 'success', 'post_id': post_id}
            else:
                error_msg = response_data.get('error', {}).get('message', response.text)
                logger.error(f"Facebook API error: {error_msg}")
                return {'status': 'failed', 'error': error_msg}

        except requests.exceptions.Timeout:
            logger.error("Facebook API timeout")
            return {'status': 'failed', 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Facebook posting error: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    def post_with_image(self, message: str, image_url: str) -> dict:
        """
        Post a message with an image to Facebook Page.

        Args:
            message: The text content to post
            image_url: URL of the image to attach (must be publicly accessible)

        Returns:
            dict with 'status' ('success' or 'failed') and 'post_id' or 'error'
        """
        if not self.enabled:
            logger.info(f"[DEV MODE] Would post to Facebook with image: {message[:100]}... | Image: {image_url}")
            return {'status': 'dev_mode', 'post_id': None, 'message': 'Facebook posting disabled - no token configured'}

        url = f"{self.base_url}/{self.page_id}/photos"
        data = {
            'caption': message,
            'url': image_url,
            'access_token': self.access_token
        }

        try:
            response = requests.post(url, data=data, timeout=60)
            response_data = response.json()

            if response.status_code == 200 and 'id' in response_data:
                post_id = response_data['id']
                logger.info(f"Successfully posted photo to Facebook: {post_id}")
                return {'status': 'success', 'post_id': post_id}
            else:
                error_msg = response_data.get('error', {}).get('message', response.text)
                logger.error(f"Facebook API error: {error_msg}")
                return {'status': 'failed', 'error': error_msg}

        except requests.exceptions.Timeout:
            logger.error("Facebook API timeout")
            return {'status': 'failed', 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Facebook photo posting error: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    def post_link(self, message: str, link_url: str) -> dict:
        """
        Post a message with a link to Facebook Page.

        Args:
            message: The text content to post
            link_url: URL to share

        Returns:
            dict with 'status' ('success' or 'failed') and 'post_id' or 'error'
        """
        if not self.enabled:
            logger.info(f"[DEV MODE] Would post to Facebook with link: {message[:100]}... | Link: {link_url}")
            return {'status': 'dev_mode', 'post_id': None, 'message': 'Facebook posting disabled - no token configured'}

        url = f"{self.base_url}/{self.page_id}/feed"
        data = {
            'message': message,
            'link': link_url,
            'access_token': self.access_token
        }

        try:
            response = requests.post(url, data=data, timeout=30)
            response_data = response.json()

            if response.status_code == 200 and 'id' in response_data:
                post_id = response_data['id']
                logger.info(f"Successfully posted link to Facebook: {post_id}")
                return {'status': 'success', 'post_id': post_id}
            else:
                error_msg = response_data.get('error', {}).get('message', response.text)
                logger.error(f"Facebook API error: {error_msg}")
                return {'status': 'failed', 'error': error_msg}

        except requests.exceptions.Timeout:
            logger.error("Facebook API timeout")
            return {'status': 'failed', 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Facebook link posting error: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    def get_page_info(self) -> Optional[dict]:
        """
        Get information about the Facebook Page.
        Useful for verifying token and page access.

        Returns:
            dict with page info or None if failed
        """
        if not self.enabled:
            return {'name': 'DEV MODE', 'id': self.page_id, 'enabled': False}

        url = f"{self.base_url}/{self.page_id}"
        params = {
            'fields': 'id,name,fan_count,link',
            'access_token': self.access_token
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                data['enabled'] = True
                return data
            else:
                logger.error(f"Failed to get page info: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return None


# Singleton instance
_facebook_service = None


def get_facebook_service() -> FacebookService:
    """Get or create the Facebook service singleton"""
    global _facebook_service
    if _facebook_service is None:
        _facebook_service = FacebookService()
    return _facebook_service
