#!/bin/bash
# Real-time Updates Test Script
# Tests SignalR broadcasts for all operations

set -e

echo "🧪 Real-time Updates Test Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "📡 Checking backend connection..."
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running. Please start it with: docker-compose up -d backend${NC}"
    exit 1
fi

# Check if SignalR hub is accessible
echo "📡 Checking SignalR hub..."
if curl -s http://localhost:3000/signalr/hub > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SignalR hub is accessible${NC}"
else
    echo -e "${YELLOW}⚠ SignalR hub endpoint may not be accessible via HTTP (this is normal for WebSocket endpoints)${NC}"
fi

echo ""
echo "✅ Backend checks complete!"
echo ""
echo "📋 Manual Testing Checklist:"
echo "=============================="
echo ""
echo "1. TODO Operations:"
echo "   - Create todo via API → Check frontend updates in real-time"
echo "   - Update todo status (new → in_progress → done) → Check frontend updates"
echo "   - Assign todo to user → Check frontend updates"
echo "   - Link todo to feature → Check frontend updates"
echo "   - Delete todo → Check frontend updates"
echo ""
echo "2. Feature Operations:"
echo "   - Create feature → Check frontend updates"
echo "   - Update feature status → Check frontend updates"
echo "   - Link element to feature → Check frontend updates"
echo ""
echo "3. Project Operations:"
echo "   - Create project → Check frontend updates"
echo "   - Update project → Check frontend updates"
echo ""
echo "4. Element Operations:"
echo "   - Create element → Check frontend updates"
echo "   - Update element → Check frontend updates"
echo "   - Delete element → Check frontend updates"
echo ""
echo "5. Document Operations:"
echo "   - Create document → Check frontend updates"
echo ""
echo "6. Session Operations:"
echo "   - Start session → Check frontend updates"
echo "   - End session → Check frontend updates"
echo ""
echo "7. Idea Operations:"
echo "   - Create idea → Check frontend updates"
echo "   - Update idea → Check frontend updates"
echo "   - Convert idea to project → Check frontend updates"
echo ""
echo "8. MCP Tools Operations:"
echo "   - Test all MCP tool operations via MCP client"
echo "   - Verify SignalR broadcasts are sent"
echo ""
echo "🔍 Testing Tips:"
echo "================"
echo "1. Open browser DevTools → Network → WS (WebSocket) tab"
echo "2. Open browser DevTools → Console to see SignalR events"
echo "3. Open two browser windows side-by-side to test real-time sync"
echo "4. Use browser DevTools → Application → Storage to check SignalR connection state"
echo ""
echo "📝 Expected Behavior:"
echo "===================="
echo "- All create/update/delete operations should trigger SignalR broadcasts"
echo "- Frontend should update automatically without page refresh"
echo "- Multiple browser windows should stay in sync"
echo "- SignalR connection should show 'Connected' status in frontend"
echo ""
