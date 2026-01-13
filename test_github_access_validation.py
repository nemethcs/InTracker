#!/usr/bin/env python3
"""
Test script to validate GitHub OAuth access control.

This script:
1. Creates a test repo "asd" on GitHub (inticky account)
2. Creates a test project in InTracker
3. Connects the GitHub repo to the project
4. Tests MCP tools to verify access validation
"""
import requests
import json
import sys

# Configuration
API_BASE_URL = "http://localhost:3000"
GITHUB_OWNER = "inticky"
GITHUB_REPO = "asd"

def login():
    """Login and get access token."""
    response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": "test@intracker.dev",
        "password": "test123"
    })
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ Logged in as: {data['user']['email']}")
    return data['tokens']['access_token']

def get_or_create_project(token):
    """Get or create test project."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing projects
    response = requests.get(f"{API_BASE_URL}/projects", headers=headers)
    if response.status_code == 200:
        projects = response.json().get("projects", [])
        for project in projects:
            if project["name"] == "GitHub Access Test":
                print(f"✅ Found existing project: {project['id']}")
                return project["id"]
    
    # Create new project
    response = requests.post(
        f"{API_BASE_URL}/projects",
        headers=headers,
        json={
            "name": "GitHub Access Test",
            "description": "Test project for GitHub OAuth access validation"
        }
    )
    
    if response.status_code != 201:
        print(f"❌ Failed to create project: {response.text}")
        sys.exit(1)
    
    project_id = response.json()["id"]
    print(f"✅ Created test project: {project_id}")
    return project_id

def check_github_connection(token):
    """Check if GitHub is connected."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        if user.get("github_username"):
            print(f"✅ GitHub connected: {user['github_username']}")
            return True
        else:
            print("❌ GitHub not connected")
            return False
    return False

def connect_repo_to_project(token, project_id):
    """Connect GitHub repo to project."""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_BASE_URL}/github/projects/{project_id}/connect",
        headers=headers,
        json={
            "owner": GITHUB_OWNER,
            "repo": GITHUB_REPO
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Connected {GITHUB_OWNER}/{GITHUB_REPO} to project")
        return True
    else:
        print(f"❌ Failed to connect repo: {response.text}")
        return False

def test_access_validation(token, project_id):
    """Test GitHub OAuth access validation."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🧪 Testing GitHub access validation...")
    
    # Test 1: Get branches (should validate access)
    print("\n1. Testing get branches...")
    response = requests.get(
        f"{API_BASE_URL}/github/projects/{project_id}/branches",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Get branches: {response.json()}")
    else:
        print(f"❌ Get branches failed: {response.status_code} - {response.text}")
    
    # Test 2: Get repo info (should validate access)
    print("\n2. Testing get repo info...")
    response = requests.get(
        f"{API_BASE_URL}/github/projects/{project_id}/repo",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Get repo info: {response.json()}")
    else:
        print(f"❌ Get repo info failed: {response.status_code} - {response.text}")
    
    # Test 3: List accessible projects
    print("\n3. Testing list accessible projects...")
    response = requests.get(
        f"{API_BASE_URL}/github/projects/access",
        headers=headers
    )
    
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Accessible projects:")
        for proj in projects:
            print(f"   - {proj['project_name']}: has_access={proj['has_access']}")
    else:
        print(f"❌ List accessible projects failed: {response.status_code} - {response.text}")

def main():
    """Main test flow."""
    print("=" * 60)
    print("GitHub OAuth Access Validation Test")
    print("=" * 60)
    
    # Step 1: Login
    print("\n📝 Step 1: Login")
    token = login()
    
    # Step 2: Check GitHub connection
    print("\n📝 Step 2: Check GitHub connection")
    if not check_github_connection(token):
        print("⚠️  Please connect GitHub account in Settings first!")
        sys.exit(1)
    
    # Step 3: Get or create project
    print("\n📝 Step 3: Get or create test project")
    project_id = get_or_create_project(token)
    
    # Step 4: Connect repo to project
    print("\n📝 Step 4: Connect GitHub repo to project")
    print(f"   Repo: {GITHUB_OWNER}/{GITHUB_REPO}")
    print(f"   ⚠️  Make sure this repo exists on GitHub first!")
    input("   Press Enter to continue...")
    
    connect_repo_to_project(token, project_id)
    
    # Step 5: Test access validation
    print("\n📝 Step 5: Test access validation")
    test_access_validation(token, project_id)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
