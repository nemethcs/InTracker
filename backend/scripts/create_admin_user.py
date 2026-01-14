#!/usr/bin/env python3
"""Script to create admin user directly in the database."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.database.base import get_db, engine
from src.database.models import User
from src.services.auth_service import AuthService

def create_admin_user(email: str, password: str, name: str = "Admin User"):
    """Create admin user in the database."""
    db: Session = next(get_db())
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists!")
            if existing_user.role == "admin":
                print(f"User is already an admin.")
            else:
                print(f"Updating user role to admin...")
                existing_user.role = "admin"
                db.commit()
                print(f"✅ User role updated to admin!")
            return existing_user
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   Role: {user.role}")
        print(f"   ID: {user.id}")
        
        return user
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create admin user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create admin user in database")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default="Admin User", help="Admin name")
    
    args = parser.parse_args()
    
    create_admin_user(args.email, args.password, args.name)
