"""GitHub OAuth 2.0 service for authorization code flow with PKCE."""
import secrets
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import httpx
from src.config import settings
from src.services.encryption_service import encryption_service


class GitHubOAuthService:
    """Service for GitHub OAuth 2.0 authorization code flow with PKCE."""
    
    # GitHub OAuth endpoints
    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_API_URL = "https://api.github.com/user"
    
    @staticmethod
    def generate_pkce_pair() -> Tuple[str, str]:
        """Generate PKCE code verifier and code challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random code verifier (43-128 characters, URL-safe)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    @staticmethod
    def generate_authorization_url(
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
    ) -> Tuple[str, str]:
        """Generate GitHub OAuth authorization URL with PKCE.
        
        Args:
            state: Optional state parameter for CSRF protection
            code_challenge: PKCE code challenge (if None, generates new pair)
            code_challenge_method: PKCE method (default: S256)
            
        Returns:
            Tuple of (authorization_url, code_verifier)
            If code_challenge is provided, code_verifier will be empty string
        """
        if not settings.GITHUB_OAUTH_CLIENT_ID:
            raise ValueError("GITHUB_OAUTH_CLIENT_ID is not configured")
        
        # Generate PKCE pair if not provided
        if code_challenge is None:
            code_verifier, code_challenge = GitHubOAuthService.generate_pkce_pair()
        else:
            code_verifier = ""  # Not needed if challenge is provided
        
        # Generate state if not provided
        if state is None:
            state = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode('utf-8').rstrip('=')
        
        # Build authorization URL
        params = {
            "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
            "redirect_uri": f"{settings.FRONTEND_URL}/api/auth/github/callback",
            "scope": "repo read:org read:user user:email",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{GitHubOAuthService.AUTHORIZATION_URL}?{query_string}"
        
        return authorization_url, code_verifier
    
    @staticmethod
    async def exchange_code_for_tokens(
        code: str,
        code_verifier: str,
        state: Optional[str] = None,
    ) -> Dict[str, any]:
        """Exchange authorization code for access token using PKCE.
        
        Args:
            code: Authorization code from GitHub callback
            code_verifier: PKCE code verifier (must match code_challenge used in authorization)
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dictionary with:
                - access_token: GitHub access token
                - refresh_token: GitHub refresh token (if available)
                - expires_in: Token expiration time in seconds
                - scope: Granted scopes
                - token_type: Token type (usually "bearer")
                - user_info: GitHub user information
        """
        if not settings.GITHUB_OAUTH_CLIENT_ID or not settings.GITHUB_OAUTH_CLIENT_SECRET:
            raise ValueError("GitHub OAuth credentials are not configured")
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GitHubOAuthService.TOKEN_URL,
                data={
                    "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                    "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": f"{settings.FRONTEND_URL}/api/auth/github/callback",
                    "code_verifier": code_verifier,
                },
                headers={
                    "Accept": "application/json",
                },
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise ValueError(f"Failed to exchange code for token: {error_detail}")
            
            token_data = response.json()
            
            # Check for errors in response
            if "error" in token_data:
                raise ValueError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
            
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")
            
            # Get user information
            user_response = await client.get(
                GitHubOAuthService.USER_API_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if user_response.status_code != 200:
                raise ValueError(f"Failed to get user information: {user_response.text}")
            
            user_info = user_response.json()
            
            # Calculate expiration times
            expires_in = token_data.get("expires_in", 28800)  # Default: 8 hours
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # GitHub OAuth Apps don't provide refresh tokens by default
            # Refresh tokens are only available for GitHub Apps
            refresh_token = token_data.get("refresh_token")
            refresh_expires_at = None
            if refresh_token:
                # Refresh tokens typically expire in 6 months
                refresh_expires_at = datetime.utcnow() + timedelta(days=180)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "expires_at": expires_at,
                "refresh_expires_at": refresh_expires_at,
                "scope": token_data.get("scope", ""),
                "token_type": token_data.get("token_type", "bearer"),
                "user_info": user_info,
            }
    
    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, any]:
        """Refresh an expired access token using refresh token.
        
        Note: GitHub OAuth Apps don't provide refresh tokens by default.
        This method is for future compatibility with GitHub Apps.
        
        Args:
            refresh_token: Refresh token from previous OAuth flow
            
        Returns:
            Dictionary with new access token and expiration info
        """
        if not settings.GITHUB_OAUTH_CLIENT_ID or not settings.GITHUB_OAUTH_CLIENT_SECRET:
            raise ValueError("GitHub OAuth credentials are not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GitHubOAuthService.TOKEN_URL,
                data={
                    "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                    "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={
                    "Accept": "application/json",
                },
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise ValueError(f"Failed to refresh token: {error_detail}")
            
            token_data = response.json()
            
            if "error" in token_data:
                raise ValueError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
            
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")
            
            expires_in = token_data.get("expires_in", 28800)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                "access_token": access_token,
                "refresh_token": token_data.get("refresh_token", refresh_token),
                "expires_in": expires_in,
                "expires_at": expires_at,
                "scope": token_data.get("scope", ""),
                "token_type": token_data.get("token_type", "bearer"),
            }
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt a GitHub token for storage.
        
        Args:
            token: Plaintext token
            
        Returns:
            Encrypted token (base64-encoded)
        """
        return encryption_service.encrypt(token)
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> Optional[str]:
        """Decrypt a stored GitHub token.
        
        Args:
            encrypted_token: Encrypted token (base64-encoded)
            
        Returns:
            Decrypted plaintext token, or None if decryption fails
        """
        return encryption_service.decrypt(encrypted_token)


# Global service instance
github_oauth_service = GitHubOAuthService()
