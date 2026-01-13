#!/bin/bash
# Test GitHub projects access endpoint

echo "🧪 Testing /github/projects/access endpoint..."
echo ""

# Get token from localStorage (you'll need to paste this from browser console)
echo "📝 Paste your access token from browser localStorage:"
echo "   (Open DevTools Console and run: localStorage.getItem('access_token'))"
read -p "Access Token: " TOKEN

if [ -z "$TOKEN" ]; then
  echo "❌ No token provided!"
  exit 1
fi

echo ""
echo "🔍 Calling API..."
curl -v -H "Authorization: Bearer $TOKEN" http://localhost:3000/github/projects/access 2>&1

echo ""
echo ""
echo "📊 Backend logs (last 50 lines with GitHub/access keywords):"
docker-compose logs backend --tail=50 | grep -E "🔍|⚠️|✅|github|access|GET|POST"
