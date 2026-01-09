"""Test audit trail implementation."""
import requests
import json

# Configuration
BASE_URL = "http://localhost:3000/api"
TEST_EMAIL = "test@intracker.dev"
TEST_PASSWORD = "test123"

def test_audit_trail():
    """Test audit trail implementation."""
    print("=" * 80)
    print("AUDIT TRAIL IMPLEMENTATION TEST")
    print("=" * 80)
    
    # 1. Login
    print("\n1. Login...")
    login_response = requests.post(
        "http://localhost:3000/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    user_id = login_data["user"]["id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"✅ Login successful! User ID: {user_id}")
    
    # 2. Get user's teams
    print("\n2. Get user's teams...")
    teams_response = requests.get(f"{BASE_URL}/teams", headers=headers)
    
    if teams_response.status_code != 200:
        print(f"❌ Failed to get teams: {teams_response.status_code}")
        return
    
    teams = teams_response.json()
    if not teams:
        print("❌ No teams found")
        return
    
    team_id = teams[0]["id"]
    print(f"✅ Found team: {teams[0]['name']} (ID: {team_id})")
    
    # 3. Create a test project
    print("\n3. Create a test project...")
    project_data = {
        "team_id": team_id,
        "name": "Audit Trail Test Project",
        "description": "Testing audit trail functionality",
        "status": "active"
    }
    
    project_response = requests.post(
        f"{BASE_URL}/projects",
        headers=headers,
        json=project_data
    )
    
    if project_response.status_code != 201:
        print(f"❌ Failed to create project: {project_response.status_code} - {project_response.text}")
        return
    
    project = project_response.json()
    project_id = project["id"]
    print(f"✅ Project created: {project['name']} (ID: {project_id})")
    print(f"   created_by: {project.get('created_by')}")
    print(f"   updated_by: {project.get('updated_by')}")
    
    # 4. Update the project
    print("\n4. Update the project...")
    update_data = {
        "description": "Updated description for audit trail test"
    }
    
    update_response = requests.put(
        f"{BASE_URL}/projects/{project_id}",
        headers=headers,
        json=update_data
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update project: {update_response.status_code} - {update_response.text}")
        return
    
    updated_project = update_response.json()
    print(f"✅ Project updated")
    print(f"   created_by: {updated_project.get('created_by')}")
    print(f"   updated_by: {updated_project.get('updated_by')}")
    
    # 5. Get audit trail for project
    print("\n5. Get audit trail for project...")
    audit_response = requests.get(
        f"{BASE_URL}/audit/entity/project/{project_id}",
        headers=headers
    )
    
    if audit_response.status_code != 200:
        print(f"❌ Failed to get audit trail: {audit_response.status_code} - {audit_response.text}")
        return
    
    audit_data = audit_response.json()
    print(f"✅ Audit trail retrieved:")
    print(f"   Entity: {audit_data['entity_type']} ({audit_data['entity_id']})")
    print(f"   Created by: {audit_data['created_by']}")
    print(f"   Updated by: {audit_data['updated_by']}")
    print(f"   Created at: {audit_data['created_at']}")
    print(f"   Updated at: {audit_data['updated_at']}")
    
    # 6. Get all entities created by user
    print(f"\n6. Get all entities created by user {user_id}...")
    created_response = requests.get(
        f"{BASE_URL}/audit/user/{user_id}/created",
        headers=headers,
        params={"limit": 10}
    )
    
    if created_response.status_code != 200:
        print(f"❌ Failed to get created entities: {created_response.status_code} - {created_response.text}")
        return
    
    created_data = created_response.json()
    print(f"✅ Found {created_data['total']} entities created by user:")
    for entity in created_data['entities'][:5]:
        print(f"   - {entity['entity_type']}: {entity.get('name') or entity.get('title')} (created: {entity['created_at']})")
    
    # 7. Get all entities updated by user
    print(f"\n7. Get all entities updated by user {user_id}...")
    updated_response = requests.get(
        f"{BASE_URL}/audit/user/{user_id}/updated",
        headers=headers,
        params={"limit": 10}
    )
    
    if updated_response.status_code != 200:
        print(f"❌ Failed to get updated entities: {updated_response.status_code} - {updated_response.text}")
        return
    
    updated_data = updated_response.json()
    print(f"✅ Found {updated_data['total']} entities updated by user:")
    for entity in updated_data['entities'][:5]:
        print(f"   - {entity['entity_type']}: {entity.get('name') or entity.get('title')} (updated: {entity['updated_at']})")
    
    # 8. Cleanup - Delete test project
    print(f"\n8. Cleanup - Delete test project...")
    delete_response = requests.delete(
        f"{BASE_URL}/projects/{project_id}",
        headers=headers
    )
    
    if delete_response.status_code == 204:
        print(f"✅ Test project deleted")
    else:
        print(f"⚠️  Failed to delete test project: {delete_response.status_code}")
    
    print("\n" + "=" * 80)
    print("✅ AUDIT TRAIL TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_audit_trail()
