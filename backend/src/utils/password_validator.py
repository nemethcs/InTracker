"""Password validation utilities."""
import re
from typing import Tuple, Optional


class PasswordValidator:
    """Validates password strength according to security policy."""
    
    # Password requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128  # Bcrypt limit is 72 bytes, but we allow longer for UTF-8 encoding
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBER = True
    REQUIRE_SPECIAL = True
    
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, Optional[str]]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if password meets requirements
            - error_message: None if valid, error description if invalid
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if len(password) > cls.MAX_LENGTH:
            return False, f"Password must be at most {cls.MAX_LENGTH} characters long"
        
        # Check for UTF-8 encoding size (bcrypt limit is 72 bytes)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            return False, "Password is too long (exceeds 72 bytes when encoded)"
        
        errors = []
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter")
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter")
        
        if cls.REQUIRE_NUMBER and not re.search(r'\d', password):
            errors.append("at least one number")
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("at least one special character")
        
        if errors:
            return False, f"Password must contain {', '.join(errors)}"
        
        return True, None
    
    @classmethod
    def get_password_requirements(cls) -> dict:
        """Get password requirements as a dictionary."""
        return {
            "min_length": cls.MIN_LENGTH,
            "max_length": cls.MAX_LENGTH,
            "require_uppercase": cls.REQUIRE_UPPERCASE,
            "require_lowercase": cls.REQUIRE_LOWERCASE,
            "require_number": cls.REQUIRE_NUMBER,
            "require_special": cls.REQUIRE_SPECIAL,
        }
