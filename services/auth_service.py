"""Authentication service for user management and JWT token handling."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.database import User, UserSession
from utils.logger import logger
from utils.config import config
import os


class AuthService:
    """Service for handling user authentication, registration, and session management."""
    
    def __init__(self, db_service):
        """
        Initialize authentication service.
        
        Args:
            db_service: DatabaseService instance for database operations
        """
        self.db_service = db_service
        
        # Password hashing context using bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT Configuration - Get from environment or config
        self.secret_key = os.getenv('JWT_SECRET_KEY') or config.get('jwt', {}).get('secret_key', 'your-secret-key-change-this')
        self.algorithm = config.get('jwt', {}).get('algorithm', 'HS256')
        self.expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', config.get('jwt', {}).get('expiration_hours', 24)))
        
        logger.info(
            "Authentication service initialized",
            jwt_expiration_hours=self.expiration_hours
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_jwt_token(self, user_id: UUID, username: str, email: str) -> str:
        """
        Create a JWT token for a user.
        
        Args:
            user_id: User's database ID (UUID)
            username: User's username
            email: User's email
            
        Returns:
            JWT token string
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        
        payload = {
            'user_id': str(user_id),  # Convert UUID to string for JSON serialization
            'username': username,
            'email': email,
            'exp': expires_at,
            'iat': datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user.
        
        Args:
            username: Desired username (must be unique)
            email: User's email address (must be unique)
            password: Plain text password (will be hashed)
            full_name: Optional full name
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Validate input
            if not username or not email or not password:
                return False, "Username, email, and password are required", None
            
            if len(password) < 8:
                return False, "Password must be at least 8 characters long", None
            
            if '@' not in email:
                return False, "Invalid email address", None
            
            # Hash the password
            password_hash = self.hash_password(password)
            
            # Create user in database
            with self.db_service.get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()
                
                if existing_user:
                    if existing_user.username == username:
                        return False, "Username already exists", None
                    else:
                        return False, "Email already registered", None
                
                # Create new user
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    is_active=True,
                    is_admin=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                session.add(new_user)
                session.flush()  # Get the user ID
                
                user_data = {
                    'user_id': str(new_user.id),  # Convert UUID to string
                    'username': new_user.username,
                    'email': new_user.email,
                    'full_name': new_user.full_name,
                    'created_at': new_user.created_at.isoformat()
                }
                
                logger.info(
                    "User registered successfully",
                    user_id=str(new_user.id),
                    username=username,
                    email=email
                )
                
                return True, "User registered successfully", user_data
                
        except IntegrityError as e:
            logger.error("Database integrity error during registration", error=str(e))
            return False, "User already exists", None
        except Exception as e:
            logger.error("Error during user registration", error=str(e))
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate a user and create a session.
        
        Args:
            email: User's email address
            password: Plain text password
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string
            
        Returns:
            Tuple of (success, message, session_data with token)
        """
        try:
            with self.db_service.get_session() as session:
                # Find user by email
                user = session.query(User).filter(
                    User.email == email,
                    User.is_active == True
                ).first()
                
                if not user:
                    logger.warning("Login attempt with non-existent email", email=email)
                    return False, "Invalid email or password", None
                
                # Verify password
                if not self.verify_password(password, user.password_hash):
                    logger.warning("Login attempt with incorrect password", email=email)
                    return False, "Invalid email or password", None
                
                # Create JWT token
                jwt_token = self.create_jwt_token(user.id, user.username, user.email)
                
                # Create user session
                expires_at = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
                
                user_session = UserSession(
                    user_id=user.id,
                    session_token=jwt_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    expires_at=expires_at,
                    last_activity=datetime.now(timezone.utc)
                )
                
                session.add(user_session)
                session.flush()  # Flush to get the session ID
                
                # Update user's last login
                user.last_login = datetime.now(timezone.utc)
                
                session_data = {
                    'token': jwt_token,
                    'user_id': str(user.id),  # Convert UUID to string
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'expires_at': expires_at.isoformat(),
                    'session_id': user_session.id
                }
                
                logger.info(
                    "User logged in successfully",
                    user_id=str(user.id),
                    username=user.username,
                    email=email
                )
                
                return True, "Login successful", session_data
                
        except Exception as e:
            logger.error("Error during user login", error=str(e), email=email)
            return False, f"Login failed: {str(e)}", None
    
    def logout_user(self, token: str) -> Tuple[bool, str]:
        """
        Logout a user by invalidating their session.
        
        Args:
            token: JWT token to invalidate
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Decode token to get user info
            payload = self.decode_jwt_token(token)
            if not payload:
                return False, "Invalid or expired token"
            
            with self.db_service.get_session() as session:
                # Find and deactivate the session
                user_session = session.query(UserSession).filter(
                    UserSession.session_token == token,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    user_session.is_active = False
                    user_session.logged_out_at = datetime.now(timezone.utc)
                    
                    logger.info(
                        "User logged out successfully",
                        user_id=payload.get('user_id'),
                        session_id=user_session.id
                    )
                    
                    return True, "Logout successful"
                else:
                    return False, "Session not found or already logged out"
                    
        except Exception as e:
            logger.error("Error during user logout", error=str(e))
            return False, f"Logout failed: {str(e)}"
    
    def validate_session(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JWT token and check if the session is still active.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Tuple of (is_valid, user_data)
        """
        try:
            # Decode token
            payload = self.decode_jwt_token(token)
            if not payload:
                return False, None
            
            with self.db_service.get_session() as session:
                # Check if session is still active
                user_session = session.query(UserSession).filter(
                    UserSession.session_token == token,
                    UserSession.is_active == True
                ).first()
                
                if not user_session:
                    return False, None
                
                # Check if session has expired
                # Make sure both datetimes are timezone-aware for comparison
                expires_at = user_session.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                if expires_at < datetime.now(timezone.utc):
                    user_session.is_active = False
                    logger.info("Session expired", session_id=user_session.id)
                    return False, None
                
                # Update last activity
                user_session.last_activity = datetime.now(timezone.utc)
                
                # Get user data
                user = session.query(User).filter(User.id == user_session.user_id).first()
                
                if not user or not user.is_active:
                    return False, None
                
                user_data = {
                    'user_id': str(user.id),  # Convert UUID to string
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_admin': user.is_admin
                }
                
                return True, user_data
                
        except Exception as e:
            logger.error("Error validating session", error=str(e))
            return False, None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            with self.db_service.get_session() as session:
                expired_sessions = session.query(UserSession).filter(
                    UserSession.expires_at < datetime.now(timezone.utc),
                    UserSession.is_active == True
                ).all()
                
                count = 0
                for user_session in expired_sessions:
                    user_session.is_active = False
                    count += 1
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired sessions")
                
                return count
                
        except Exception as e:
            logger.error("Error cleaning up expired sessions", error=str(e))
            return 0
    
    def get_user_active_sessions(self, user_id: UUID) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User's database ID (UUID)
            
        Returns:
            List of active session data
        """
        try:
            with self.db_service.get_session() as session:
                sessions = session.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).all()
                
                return [
                    {
                        'session_id': s.id,
                        'created_at': s.created_at.isoformat(),
                        'expires_at': s.expires_at.isoformat(),
                        'last_activity': s.last_activity.isoformat() if s.last_activity else None,
                        'ip_address': s.ip_address,
                        'user_agent': s.user_agent
                    }
                    for s in sessions
                ]
                
        except Exception as e:
            logger.error("Error getting user active sessions", error=str(e))
            return []
