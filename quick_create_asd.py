#!/usr/bin/env python3
import requests
import sys

API_BASE_URL = "http://localhost:3000"

# Login (használd a saját credentialseidet)
print("🔐 Login...")
response = requests.post(f"{API_BASE_URL}/auth/login", json={
    "email": "test@intracker.dev",
    "password": "test123"
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.json()}")
    sys.exit(1)

token = response.json()['tokens']['access_token']
print(f"✅ Logged in!")

# Create project
print("\n📝 Creating project 'asd'...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{API_BASE_URL}/projects",
    headers=headers,
    json={
        "name": "asd",
        "description": "Test repository for GitHub OAuth access validation",
        "status": "active",
        "tags": ["test", "github-oauth"],
        "github_repo_url": "https://github.com/nemethcs/asd"
    }
)

if response.status_code == 201:
    project = response.json()
    print(f"✅ Project created!")
    print(f"   ID: {project['id']}")
    print(f"   Name: {project['name']}")
    print(f"   GitHub: {project.get('github_repo_url')}")
    
    # Check GitHub access
    print("\n🧪 Checking GitHub access...")
    response = requests.get(
        f"{API_BASE_URL}/github/projects/access",
        headers=headers
    )
    
    if response.status_code == 200:
        projects = response.json()
        print("\n📊 Accessible projects:")
        for proj in projects:
            if proj['project_name'] == 'asd':
                access_icon = "✅" if proj['has_access'] else "❌"
                print(f"{access_icon} {proj['project_name']}: has_access={proj['has_access']}, access_level={proj.get('access_level')}")
    else:
        print(f"❌ Failed to check access: {response.text}")
else:
    print(f"❌ Project creation failed: {response.status_code}")
    print(f"   Response: {response.text}")
