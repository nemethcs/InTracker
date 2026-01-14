#!/usr/bin/env python3
"""Script to check if team leader invitations were sent in production."""
import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database.models import InvitationCode
from datetime import datetime

def get_database_url():
    """Get database URL from environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to connect to the production database")
        sys.exit(1)
    return database_url

def check_team_leader_invites():
    """Check team leader invitations in the database."""
    database_url = get_database_url()
    
    print(f"🔍 Connecting to database...")
    print(f"   Database URL: {database_url.split('@')[1] if '@' in database_url else 'hidden'}")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Query admin invitations (team leader invitations)
        admin_invites = db.query(InvitationCode).filter(
            InvitationCode.type == "admin"
        ).order_by(InvitationCode.created_at.desc()).all()
        
        print(f"\n📊 Found {len(admin_invites)} admin/team leader invitation(s)\n")
        
        if not admin_invites:
            print("⚠️  No team leader invitations found in the database")
            return
        
        # Check each invitation
        sent_count = 0
        not_sent_count = 0
        
        for invite in admin_invites:
            print(f"📧 Invitation Code: {invite.code}")
            print(f"   Created: {invite.created_at}")
            print(f"   Created by: {invite.created_by}")
            print(f"   Expires: {invite.expires_at or 'Never'}")
            print(f"   Used: {'Yes' if invite.used_at else 'No'}")
            if invite.used_by:
                print(f"   Used by: {invite.used_by}")
            
            if invite.email_sent_to:
                sent_count += 1
                print(f"   ✅ Email sent to: {invite.email_sent_to}")
                print(f"   📅 Sent at: {invite.email_sent_at}")
            else:
                not_sent_count += 1
                print(f"   ❌ Email NOT sent (no email_sent_to field)")
            
            print()
        
        # Summary
        print("=" * 60)
        print(f"📈 Summary:")
        print(f"   Total invitations: {len(admin_invites)}")
        print(f"   ✅ Emails sent: {sent_count}")
        print(f"   ❌ Emails not sent: {not_sent_count}")
        print("=" * 60)
        
        db.close()
        
    except Exception as e:
        print(f"❌ ERROR: Failed to check invitations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_team_leader_invites()
