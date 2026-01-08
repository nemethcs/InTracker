#!/usr/bin/env python3
"""Test script for admin endpoints."""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:3000"

# Test user credentials (adjust if needed)
TEST_EMAIL = "admin@test.com"
TEST_PASSWORD = "test123"

def get_auth_token():
    """Get authentication token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["tokens"]["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_admin_endpoints(token):
    """Test admin endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("TESTING ADMIN ENDPOINTS")
    print("="*60)
    
    # Test 1: List users
    print("\n1. Testing GET /admin/users")
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List users: {data['total']} users found")
        if data['users']:
            print(f"   First user: {data['users'][0]['email']} ({data['users'][0]['role']})")
    else:
        print(f"❌ List users failed: {response.status_code} - {response.text}")
    
    # Test 2: Get user by ID (use first user from list)
    if response.status_code == 200 and response.json()['users']:
        user_id = response.json()['users'][0]['id']
        print(f"\n2. Testing GET /admin/users/{user_id}")
        response = requests.get(f"{BASE_URL}/admin/users/{user_id}", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Get user: {user['email']} ({user['role']})")
        else:
            print(f"❌ Get user failed: {response.status_code} - {response.text}")
    
    # Test 3: List invitations
    print("\n3. Testing GET /admin/invitations")
    response = requests.get(f"{BASE_URL}/admin/invitations", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List invitations: {data['total']} invitations found")
    else:
        print(f"❌ List invitations failed: {response.status_code} - {response.text}")
    
    # Test 4: Create admin invitation
    print("\n4. Testing POST /admin/invitations/admin")
    response = requests.post(
        f"{BASE_URL}/admin/invitations/admin?expires_in_days=30",
        headers=headers
    )
    if response.status_code == 201:
        data = response.json()
        invitation_code = data['invitation']['code']
        print(f"✅ Create admin invitation: {invitation_code[:20]}...")
        
        # Test 5: Get invitation by code
        print(f"\n5. Testing GET /admin/invitations/{invitation_code}")
        response = requests.get(f"{BASE_URL}/admin/invitations/{invitation_code}", headers=headers)
        if response.status_code == 200:
            inv = response.json()
            print(f"✅ Get invitation: type={inv['type']}, expires_at={inv['expires_at']}")
        else:
            print(f"❌ Get invitation failed: {response.status_code} - {response.text}")
        
        # Test 6: Delete invitation
        print(f"\n6. Testing DELETE /admin/invitations/{invitation_code}")
        response = requests.delete(f"{BASE_URL}/admin/invitations/{invitation_code}", headers=headers)
        if response.status_code == 200:
            print(f"✅ Delete invitation: success")
        else:
            print(f"❌ Delete invitation failed: {response.status_code} - {response.text}")
    else:
        print(f"❌ Create admin invitation failed: {response.status_code} - {response.text}")

def test_team_endpoints(token):
    """Test team endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("TESTING TEAM ENDPOINTS")
    print("="*60)
    
    # Test 1: List teams
    print("\n1. Testing GET /teams")
    response = requests.get(f"{BASE_URL}/teams", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List teams: {data['total']} teams found")
        if data['teams']:
            print(f"   First team: {data['teams'][0]['name']}")
    else:
        print(f"❌ List teams failed: {response.status_code} - {response.text}")
    
    # Test 2: Create team (if admin)
    print("\n2. Testing POST /teams")
    test_team_name = f"Test Team {uuid4().hex[:8]}"
    response = requests.post(
        f"{BASE_URL}/teams",
        headers=headers,
        json={"name": test_team_name, "description": "Test team"}
    )
    if response.status_code == 201:
        team = response.json()
        team_id = team['id']
        print(f"✅ Create team: {team['name']} (ID: {team_id})")
        
        # Test 3: Get team
        print(f"\n3. Testing GET /teams/{team_id}")
        response = requests.get(f"{BASE_URL}/teams/{team_id}", headers=headers)
        if response.status_code == 200:
            team = response.json()
            print(f"✅ Get team: {team['name']}")
        else:
            print(f"❌ Get team failed: {response.status_code} - {response.text}")
        
        # Test 4: Update team
        print(f"\n4. Testing PUT /teams/{team_id}")
        response = requests.put(
            f"{BASE_URL}/teams/{team_id}",
            headers=headers,
            json={"description": "Updated test team description"}
        )
        if response.status_code == 200:
            team = response.json()
            print(f"✅ Update team: {team['description']}")
        else:
            print(f"❌ Update team failed: {response.status_code} - {response.text}")
        
        # Test 5: Create team invitation
        print(f"\n5. Testing POST /teams/{team_id}/invitations")
        response = requests.post(
            f"{BASE_URL}/teams/{team_id}/invitations?expires_in_days=7",
            headers=headers
        )
        if response.status_code == 201:
            inv = response.json()
            print(f"✅ Create team invitation: {inv['code'][:20]}...")
        else:
            print(f"❌ Create team invitation failed: {response.status_code} - {response.text}")
        
        # Test 6: Delete team
        print(f"\n6. Testing DELETE /teams/{team_id}")
        response = requests.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
        if response.status_code == 204:
            print(f"✅ Delete team: success")
        else:
            print(f"❌ Delete team failed: {response.status_code} - {response.text}")
    else:
        print(f"❌ Create team failed: {response.status_code} - {response.text}")
        if response.status_code == 403:
            print("   (User might not be admin)")

def main():
    """Main test function."""
    print("="*60)
    print("BACKEND API TESTING")
    print("="*60)
    
    # Get auth token
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Cannot continue tests.")
        return
    
    print("✅ Authentication successful")
    
    # Test admin endpoints
    test_admin_endpoints(token)
    
    # Test team endpoints
    test_team_endpoints(token)
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
