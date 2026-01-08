"""
API Test Script for Real-time Updates
Tests that all operations trigger SignalR broadcasts correctly.
"""
import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

# Test credentials (adjust if needed)
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

class RealtimeTestClient:
    def __init__(self):
        self.token: Optional[str] = None
        self.headers: dict = {}
    
    def login(self) -> bool:
        """Login and get JWT token."""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json=TEST_USER
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def create_project(self, name: str, team_id: str) -> Optional[str]:
        """Create a test project."""
        try:
            response = requests.post(
                f"{API_BASE}/projects",
                json={
                    "name": name,
                    "team_id": team_id,
                    "description": f"Test project: {name}",
                    "status": "active"
                },
                headers=self.headers
            )
            if response.status_code == 201:
                project = response.json()
                print(f"✅ Created project: {project['id']}")
                return project['id']
            else:
                print(f"❌ Failed to create project: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            return None
    
    def create_element(self, project_id: str, title: str) -> Optional[str]:
        """Create a test element."""
        try:
            response = requests.post(
                f"{API_BASE}/elements",
                json={
                    "project_id": project_id,
                    "title": title,
                    "type": "module",
                    "description": f"Test element: {title}"
                },
                headers=self.headers
            )
            if response.status_code == 201:
                element = response.json()
                print(f"✅ Created element: {element['id']}")
                return element['id']
            else:
                print(f"❌ Failed to create element: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating element: {e}")
            return None
    
    def create_todo(self, element_id: str, title: str, feature_id: Optional[str] = None) -> Optional[str]:
        """Create a test todo."""
        try:
            payload = {
                "element_id": element_id,
                "title": title,
                "description": f"Test todo: {title}",
                "status": "new"
            }
            if feature_id:
                payload["feature_id"] = feature_id
            
            response = requests.post(
                f"{API_BASE}/todos",
                json=payload,
                headers=self.headers
            )
            if response.status_code == 201:
                todo = response.json()
                print(f"✅ Created todo: {todo['id']}")
                return todo['id']
            else:
                print(f"❌ Failed to create todo: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating todo: {e}")
            return None
    
    def update_todo_status(self, todo_id: str, status: str, expected_version: int) -> bool:
        """Update todo status."""
        try:
            response = requests.put(
                f"{API_BASE}/todos/{todo_id}/status",
                json={
                    "status": status,
                    "expected_version": expected_version
                },
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"✅ Updated todo status to: {status}")
                return True
            else:
                print(f"❌ Failed to update todo status: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error updating todo status: {e}")
            return False
    
    def create_feature(self, project_id: str, name: str) -> Optional[str]:
        """Create a test feature."""
        try:
            response = requests.post(
                f"{API_BASE}/features",
                json={
                    "project_id": project_id,
                    "name": name,
                    "description": f"Test feature: {name}",
                    "status": "new"
                },
                headers=self.headers
            )
            if response.status_code == 201:
                feature = response.json()
                print(f"✅ Created feature: {feature['id']}")
                return feature['id']
            else:
                print(f"❌ Failed to create feature: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating feature: {e}")
            return None
    
    def create_document(self, project_id: str, title: str) -> Optional[str]:
        """Create a test document."""
        try:
            response = requests.post(
                f"{API_BASE}/documents",
                json={
                    "project_id": project_id,
                    "type": "adr",
                    "title": title,
                    "content": f"# {title}\n\nTest document content."
                },
                headers=self.headers
            )
            if response.status_code == 201:
                document = response.json()
                print(f"✅ Created document: {document['id']}")
                return document['id']
            else:
                print(f"❌ Failed to create document: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating document: {e}")
            return None


def main():
    """Run real-time updates API tests."""
    print("🧪 Real-time Updates API Test")
    print("=" * 50)
    print()
    
    client = RealtimeTestClient()
    
    # Login
    if not client.login():
        print("❌ Cannot proceed without login")
        return
    
    # Get or create a team (you may need to adjust this)
    # For now, we'll assume you have a team_id
    print("\n⚠️  Note: You need to provide a valid team_id for testing")
    print("   You can get it from the database or create one via API")
    print()
    
    # Example test flow (uncomment and adjust team_id):
    """
    team_id = "your-team-id-here"
    
    # Create project
    project_id = client.create_project("Realtime Test Project", team_id)
    if not project_id:
        return
    
    time.sleep(1)  # Wait for SignalR broadcast
    
    # Create element
    element_id = client.create_element(project_id, "Test Module")
    if not element_id:
        return
    
    time.sleep(1)
    
    # Create feature
    feature_id = client.create_feature(project_id, "Test Feature")
    if not feature_id:
        return
    
    time.sleep(1)
    
    # Create todo
    todo_id = client.create_todo(element_id, "Test Todo", feature_id)
    if not todo_id:
        return
    
    time.sleep(1)
    
    # Update todo status
    client.update_todo_status(todo_id, "in_progress", 1)
    time.sleep(1)
    client.update_todo_status(todo_id, "done", 2)
    
    time.sleep(1)
    
    # Create document
    client.create_document(project_id, "Test ADR")
    
    print("\n✅ All API tests completed!")
    print("📡 Check frontend to verify real-time updates were received")
    """
    
    print("\n💡 To run full tests:")
    print("   1. Uncomment the test code above")
    print("   2. Set a valid team_id")
    print("   3. Ensure backend is running")
    print("   4. Open frontend in browser to see real-time updates")


if __name__ == "__main__":
    main()
