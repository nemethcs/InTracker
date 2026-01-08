#!/usr/bin/env python3
"""Run database migrations and create initial user on Azure."""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import User
from src.services.auth_service import AuthService


def run_migrations(database_url: str):
    """Run Alembic migrations."""
    print("🔄 Running database migrations...")
    
    # Set up Alembic
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    # Run migrations
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def create_user(database_url: str, email: str, password: str, name: str = None):
    """Create a user in the database."""
    print(f"👤 Creating user: {email}...")
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"⚠️  User {email} already exists. Skipping creation.")
            return True
        
        # Create user using auth service
        user = AuthService.register(db, email, password, name)
        print(f"✅ User created successfully: {user.email} (ID: {user.id})")
        return True
    except ValueError as e:
        if "already exists" in str(e):
            print(f"⚠️  User {email} already exists. Skipping creation.")
            return True
        print(f"❌ Failed to create user: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        engine.dispose()


def main():
    """Main function."""
    # Get database URL from environment or argument
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!")
        print("Usage: DATABASE_URL=postgresql://... python run_azure_migrations.py")
        sys.exit(1)
    
    print("🚀 Starting Azure database setup...")
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else 'N/A'}")
    print()
    
    # Run migrations
    if not run_migrations(database_url):
        print("❌ Migration failed. Aborting.")
        sys.exit(1)
    
    print()
    
    # Create user
    user_email = os.getenv("USER_EMAIL", "nemethcs@example.com")
    user_password = os.getenv("USER_PASSWORD", "Hello1kaa")
    user_name = os.getenv("USER_NAME", "nemethcs")
    
    # Extract email from username if needed
    if "@" not in user_email:
        user_email = f"{user_email}@example.com"
    
    if not create_user(database_url, user_email, user_password, user_name):
        print("⚠️  User creation failed, but migrations completed.")
        sys.exit(1)
    
    print()
    print("✅ Azure database setup completed successfully!")
    print(f"   User: {user_email}")
    print(f"   Password: {'*' * len(user_password)}")


if __name__ == "__main__":
    main()
