#!/usr/bin/env python3
"""Script to check team leader invitations via production API."""
import requests
import sys
import os

def check_invites_via_api(api_url: str, admin_token: str = None):
    """Check team leader invitations via API."""
    headers = {}
    if admin_token:
        headers["Authorization"] = f"Bearer {admin_token}"
    
    try:
        # Get invitations list
        response = requests.get(
            f"{api_url}/admin/invitations",
            params={"type": "admin", "limit": 100},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            print("❌ ERROR: Authentication required")
            print("   Please provide an admin access token:")
            print("   export ADMIN_TOKEN='your_token_here'")
            print("   python3 scripts/check_prod_invites_api.py")
            return
        
        if response.status_code != 200:
            print(f"❌ ERROR: API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        data = response.json()
        invitations = data.get("invitations", [])
        
        print(f"\n📊 Found {len(invitations)} admin/team leader invitation(s)\n")
        
        if not invitations:
            print("⚠️  No team leader invitations found")
            return
        
        sent_count = 0
        not_sent_count = 0
        
        for invite in invitations:
            print(f"📧 Invitation Code: {invite.get('code', 'N/A')}")
            print(f"   Created: {invite.get('created_at', 'N/A')}")
            print(f"   Expires: {invite.get('expires_at', 'Never')}")
            print(f"   Used: {'Yes' if invite.get('used_at') else 'No'}")
            
            email_sent_to = invite.get('email_sent_to')
            email_sent_at = invite.get('email_sent_at')
            
            if email_sent_to:
                sent_count += 1
                print(f"   ✅ Email sent to: {email_sent_to}")
                print(f"   📅 Sent at: {email_sent_at}")
            else:
                not_sent_count += 1
                print(f"   ❌ Email NOT sent (no email_sent_to field)")
            
            print()
        
        # Summary
        print("=" * 60)
        print(f"📈 Summary:")
        print(f"   Total invitations: {len(invitations)}")
        print(f"   ✅ Emails sent: {sent_count}")
        print(f"   ❌ Emails not sent: {not_sent_count}")
        print("=" * 60)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to connect to API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    api_url = os.getenv("API_URL", "https://intracker-api.polandcentral.azurecontainerapps.io")
    admin_token = os.getenv("ADMIN_TOKEN")
    
    print(f"🔍 Checking team leader invitations via API...")
    print(f"   API URL: {api_url}")
    print()
    
    check_invites_via_api(api_url, admin_token)
