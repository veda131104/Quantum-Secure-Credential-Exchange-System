"""
Redis service for token management and caching
"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta

from app.core.config import settings


class RedisService:
    """Service for Redis operations"""

    def __init__(self):
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.password = settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
        self.client = None

    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            print(f"Connected to Redis at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Redis: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    def set(self, key: str, value: Any, expiry_seconds: Optional[int] = None) -> bool:
        """
        Set a key-value pair

        Args:
            key: Key
            value: Value (will be JSON encoded if dict/list)
            expiry_seconds: Optional expiry time in seconds

        Returns:
            True if successful
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            # Convert dict/list to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if expiry_seconds:
                self.client.setex(key, expiry_seconds, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            print(f"Failed to set key {key}: {str(e)}")
            return False

    def get(self, key: str, as_json: bool = False) -> Optional[Any]:
        """
        Get value for a key

        Args:
            key: Key
            as_json: If True, parse value as JSON

        Returns:
            Value or None if not found
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            value = self.client.get(key)
            if value is None:
                return None

            if as_json:
                return json.loads(value)
            return value
        except Exception as e:
            print(f"Failed to get key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Failed to delete key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Failed to check key {key}: {str(e)}")
            return False

    def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL (time to live) for a key in seconds"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            ttl = self.client.ttl(key)
            return ttl if ttl >= 0 else None
        except Exception as e:
            print(f"Failed to get TTL for key {key}: {str(e)}")
            return None

    # Token management methods

    def store_share_token(
        self, token: str, credential_data: Dict, expiry_hours: int
    ) -> bool:
        """Store a share token with credential data"""
        key = f"share_token:{token}"
        expiry_seconds = expiry_hours * 3600
        return self.set(key, credential_data, expiry_seconds)

    def get_share_token(self, token: str) -> Optional[Dict]:
        """Get share token data"""
        key = f"share_token:{token}"
        return self.get(key, as_json=True)

    def revoke_share_token(self, token: str) -> bool:
        """Revoke a share token"""
        key = f"share_token:{token}"
        return self.delete(key)

    def blacklist_token(self, token: str, expiry_seconds: int) -> bool:
        """Add token to blacklist (for logout)"""
        key = f"blacklist:{token}"
        return self.set(key, "1", expiry_seconds)

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        key = f"blacklist:{token}"
        return self.exists(key)

    def store_refresh_token(
        self, user_id: str, token: str, expiry_days: int
    ) -> bool:
        """Store refresh token"""
        key = f"refresh_token:{user_id}"
        expiry_seconds = expiry_days * 86400
        return self.set(key, token, expiry_seconds)

    def get_refresh_token(self, user_id: str) -> Optional[str]:
        """Get refresh token for user"""
        key = f"refresh_token:{user_id}"
        return self.get(key)

    def delete_refresh_token(self, user_id: str) -> bool:
        """Delete refresh token"""
        key = f"refresh_token:{user_id}"
        return self.delete(key)

    # User session methods

    def store_user_session(self, user_id: str, session_data: Dict, expiry_seconds: int) -> bool:
        """Store user session data"""
        key = f"session:{user_id}"
        return self.set(key, session_data, expiry_seconds)

    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get user session data"""
        key = f"session:{user_id}"
        return self.get(key, as_json=True)

    def delete_user_session(self, user_id: str) -> bool:
        """Delete user session"""
        key = f"session:{user_id}"
        return self.delete(key)

    # List operations

    def get_keys_by_pattern(self, pattern: str) -> list:
        """Get all keys matching pattern"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Redis")

        try:
            return list(self.client.scan_iter(match=pattern))
        except Exception as e:
            print(f"Failed to get keys by pattern {pattern}: {str(e)}")
            return []

    def get_user_share_tokens(self, user_id: str) -> list:
        """Get all active share tokens for a user"""
        pattern = f"share_token:*"
        keys = self.get_keys_by_pattern(pattern)

        tokens = []
        for key in keys:
            data = self.get(key, as_json=True)
            if data and data.get("user_id") == user_id:
                token = key.replace("share_token:", "")
                ttl = self.get_ttl(key)
                tokens.append(
                    {
                        "token": token,
                        "data": data,
                        "ttl_seconds": ttl,
                    }
                )
        return tokens

    def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            self.client.close()
            self.client = None


# Singleton instance
redis_service = RedisService()
