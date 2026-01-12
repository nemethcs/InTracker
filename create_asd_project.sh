#!/bin/bash
# Create "asd" project via REST API

echo "🚀 Creating 'asd' project in InTracker..."

# Login to get token (using test@intracker.dev or your actual user)
echo "📝 Please provide your InTracker credentials:"
read -p "Email: " EMAIL
read -sp "Password: " PASSWORD
echo ""

# Login
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo "✅ Logged in successfully!"

# Create project
echo ""
echo "📝 Creating project 'asd'..."
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:3000/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "asd",
    "description": "Test repository for GitHub OAuth access validation",
    "status": "active",
    "tags": ["test", "github-oauth"],
    "github_repo_url": "https://github.com/nemethcs/asd"
  }')

echo "Response: $PROJECT_RESPONSE"

PROJECT_ID=$(echo $PROJECT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Project creation failed!"
  exit 1
fi

echo ""
echo "✅ Project created successfully!"
echo "   Project ID: $PROJECT_ID"
echo "   GitHub Repo: https://github.com/nemethcs/asd"
echo ""
echo "🧪 Now test GitHub access validation:"
echo "   1. Go to Settings → GitHub Integration"
echo "   2. Check 'Accessible Projects' list"
echo "   3. Project 'asd' should show: has_access = true/false"
