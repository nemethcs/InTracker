"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from src.config import settings
from src.database.models import User, TeamMember, Team
from src.services.invitation_service import InvitationService


class AuthService:
    """Authentication service for user management and JWT tokens."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        # Bcrypt has a 72 byte limit, truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        # Bcrypt has a 72 byte limit, truncate if necessary
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, is_refresh: bool = False) -> dict:
        """Verify JWT token."""
        secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return payload
        except JWTError:
            raise ValueError("Invalid or expired token")

    @staticmethod
    def register(
        db: Session,
        email: str,
        password: str,
        invitation_code: str,
        name: Optional[str] = None,
    ) -> User:
        """Register new user with invitation code."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists")

        # Validate invitation code
        is_valid, invitation, error_message = InvitationService.validate_code(db, invitation_code)
        if not is_valid:
            raise ValueError(error_message or "Invalid invitation code")

        # Determine user role and team based on invitation type
        user_role = "member"  # Default role
        team_id = None
        should_create_team = False
        team_member_role = "member"  # Default team member role

        if invitation.type == "admin":
            # Admin invitation creates a team_leader who gets their own team
            user_role = "team_leader"
            should_create_team = True
            team_member_role = "team_leader"
        elif invitation.type == "team":
            user_role = "member"  # User role is always member for team invitations
            team_id = invitation.team_id
            # Use member_role from invitation (member or team_leader)
            team_member_role = getattr(invitation, 'member_role', 'member')

        # Hash password
        password_hash = AuthService.hash_password(password)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=user_role,
            is_active=True,
        )
        db.add(user)
        db.flush()  # Flush to get user.id

        # Mark invitation as used
        InvitationService.mark_as_used(db, invitation_code, user.id)

        # Create team for admin invitation (team_leader)
        if should_create_team:
            from src.services.team_service import TeamService
            # Generate team name from user name or email
            team_name = f"{name}'s Team" if name else f"{email.split('@')[0]}'s Team"
            # Ensure unique team name
            base_name = team_name
            counter = 1
            while db.query(Team).filter(Team.name == team_name).first():
                team_name = f"{base_name} {counter}"
                counter += 1
            
            team = TeamService.create_team(
                db=db,
                name=team_name,
                created_by=user.id,
                description=None,
            )
            team_id = team.id

        # Add user to team if team invitation or newly created team
        if team_id:
            team_member = TeamMember(
                team_id=team_id,
                user_id=user.id,
                role=team_member_role,
            )
            db.add(team_member)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> tuple[User, dict]:
        """Login user and return user with tokens."""
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        # Verify password
        if not AuthService.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Generate tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)

        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

        return user, tokens

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        # Verify refresh token
        payload = AuthService.verify_token(refresh_token, is_refresh=True)

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Generate new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = AuthService.create_access_token(token_data)
        new_refresh_token = AuthService.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }


# Global instance
auth_service = AuthService()
