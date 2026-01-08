#!/bin/bash
# Run migrations and create user in Azure Cloud Shell
# This script should be run in Azure Cloud Shell

set -e

echo "🚀 Starting Azure database setup..."

# Get database connection string from Key Vault
RESOURCE_GROUP="intracker-rg-poland"
KEY_VAULT="intracker-kv"

echo "📊 Getting database connection string..."
DATABASE_URL=$(az keyvault secret show \
  --vault-name "$KEY_VAULT" \
  --name "database-url" \
  --query "value" \
  --output tsv)

if [ -z "$DATABASE_URL" ]; then
  echo "❌ Failed to get database URL from Key Vault"
  exit 1
fi

echo "✅ Database URL retrieved"
echo ""

# Clone or update repository
if [ ! -d "InTracker" ]; then
  echo "📥 Cloning repository..."
  git clone https://github.com/yourusername/InTracker.git || echo "Repository not found, using current directory"
  cd InTracker
else
  echo "📂 Using existing repository..."
  cd InTracker
  git pull || echo "Git pull failed, continuing..."
fi

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Run migrations
echo "🔄 Running database migrations..."
export DATABASE_URL
alembic upgrade head

echo "✅ Migrations completed successfully!"
echo ""

# Create user
echo "👤 Creating user..."
export USER_EMAIL="nemethcs@example.com"
export USER_PASSWORD="Hello1kaa"
export USER_NAME="nemethcs"

python3 << 'EOF'
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import User
from src.services.auth_service import AuthService

database_url = os.getenv("DATABASE_URL")
email = os.getenv("USER_EMAIL", "nemethcs@example.com")
password = os.getenv("USER_PASSWORD", "Hello1kaa")
name = os.getenv("USER_NAME", "nemethcs")

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"⚠️  User {email} already exists. Skipping creation.")
    else:
        # Create user
        user = AuthService.register(db, email, password, name)
        print(f"✅ User created successfully: {user.email} (ID: {user.id})")
finally:
    db.close()
    engine.dispose()
EOF

echo ""
echo "✅ Azure database setup completed successfully!"
