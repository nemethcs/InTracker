# Real-time Updates Testing Guide

## 🎯 Testing Strategy

### 1. Backend Build & Verification

```bash
# Rebuild backend to ensure all changes are included
cd backend
docker-compose build backend

# Or if running locally
docker-compose up -d --build backend

# Check backend logs for errors
docker-compose logs -f backend
```

**What to check:**
- ✅ Backend starts without errors
- ✅ SignalR hub endpoint is accessible
- ✅ No import errors related to `signalr_hub` or `broadcast_*` functions
- ✅ Database migrations are applied

### 2. SignalR Connection Test

**Frontend Connection:**
1. Open browser DevTools → Network → WS (WebSocket)
2. Navigate to frontend (http://localhost:5173)
3. Login to the application
4. Check WebSocket connection appears in Network tab
5. Verify connection status shows "Connected" in console

**Expected:**
- WebSocket connection to `ws://localhost:3000/signalr/hub`
- Connection state: `Connected`
- No connection errors in console

### 3. End-to-End Testing Checklist

#### A. TODO Operations

**Test 1: Create Todo**
1. Open two browser windows side-by-side
2. In Window 1: Create a new todo via UI
3. **Expected:** Window 2 should show the new todo immediately without refresh

**Test 2: Update Todo Status**
1. In Window 1: Change todo status (new → in_progress → done)
2. **Expected:** Window 2 should reflect status changes in real-time

**Test 3: Assign Todo**
1. In Window 1: Assign todo to a user
2. **Expected:** Window 2 should show assignment update immediately

**Test 4: Link Todo to Feature**
1. In Window 1: Link todo to a feature
2. **Expected:** Window 2 should show todo linked to feature, feature progress updates

**Test 5: Delete Todo**
1. In Window 1: Delete a todo
2. **Expected:** Window 2 should remove todo from list immediately

#### B. Feature Operations

**Test 6: Create Feature**
1. In Window 1: Create a new feature
2. **Expected:** Window 2 should show new feature in feature list

**Test 7: Update Feature Status**
1. In Window 1: Update feature status (new → in_progress → done)
2. **Expected:** Window 2 should reflect status changes

**Test 8: Link Element to Feature**
1. In Window 1: Link an element to a feature
2. **Expected:** Window 2 should show element linked, feature progress may update

#### C. Project Operations

**Test 9: Create Project**
1. In Window 1: Create a new project
2. **Expected:** Window 2 should show new project in project list

**Test 10: Update Project**
1. In Window 1: Update project name/description/status
2. **Expected:** Window 2 should reflect changes immediately

#### D. Element Operations

**Test 11: Create Element**
1. In Window 1: Create a new element
2. **Expected:** Window 2 should show new element in element tree

**Test 12: Update Element**
1. In Window 1: Update element title/description
2. **Expected:** Window 2 should reflect changes

**Test 13: Delete Element**
1. In Window 1: Delete an element
2. **Expected:** Window 2 should remove element from tree

#### E. Document Operations

**Test 14: Create Document**
1. In Window 1: Create a new document
2. **Expected:** Window 2 should show new document in document list

#### F. Session Operations

**Test 15: Start Session**
1. In Window 1: Start a work session
2. **Expected:** Window 2 should show user activity/session started notification

**Test 16: End Session**
1. In Window 1: End a work session
2. **Expected:** Window 2 should show session ended notification

#### G. Idea Operations

**Test 17: Create Idea**
1. In Window 1: Create a new idea
2. **Expected:** Window 2 should show new idea in idea list

**Test 18: Update Idea**
1. In Window 1: Update idea title/status
2. **Expected:** Window 2 should reflect changes

**Test 19: Convert Idea to Project**
1. In Window 1: Convert an idea to a project
2. **Expected:** Window 2 should show new project created, idea marked as converted

#### H. MCP Tools Operations

**Test 20: MCP Tool - Create Todo**
1. Use MCP client to create a todo via `mcp_create_todo`
2. **Expected:** Frontend should show new todo in real-time

**Test 21: MCP Tool - Update Todo Status**
1. Use MCP client to update todo status via `mcp_update_todo_status`
2. **Expected:** Frontend should reflect status change immediately

**Test 22: MCP Tool - Create Feature**
1. Use MCP client to create a feature via `mcp_create_feature`
2. **Expected:** Frontend should show new feature in real-time

**Test 23: MCP Tool - Create Project**
1. Use MCP client to create a project via `mcp_create_project`
2. **Expected:** Frontend should show new project in real-time

### 4. Browser DevTools Monitoring

**Network Tab (WebSocket):**
- Monitor WebSocket messages
- Check for `todoUpdated`, `featureUpdated`, `projectUpdated` messages
- Verify message format matches expected structure

**Console Tab:**
- Check for SignalR connection logs
- Look for any error messages
- Verify event handlers are firing

**Application Tab:**
- Check SignalR connection state
- Verify project groups are joined correctly

### 5. Backend Logs Monitoring

```bash
# Watch backend logs in real-time
docker-compose logs -f backend | grep -i "signalr\|broadcast\|websocket"
```

**What to look for:**
- ✅ Broadcast functions being called
- ✅ No errors in broadcast execution
- ✅ WebSocket connections being established
- ✅ Project groups being joined/left

### 6. Common Issues & Debugging

**Issue: No real-time updates**
- Check SignalR connection is established
- Verify project group is joined
- Check backend logs for broadcast errors
- Verify frontend event handlers are registered

**Issue: Updates delayed or missing**
- Check WebSocket connection stability
- Verify broadcast functions are being called
- Check for errors in backend logs
- Verify frontend is subscribed to correct events

**Issue: Multiple updates for single action**
- Check for duplicate broadcast calls
- Verify background tasks are not duplicating
- Check frontend handlers are not firing multiple times

### 7. Automated Testing (Future)

For automated testing, consider:
- WebSocket client library for Python/Node.js
- Mock SignalR hub for unit tests
- Integration tests with real WebSocket connections
- E2E tests with Playwright/Cypress

### 8. Performance Testing

**Test with multiple clients:**
1. Open 5+ browser windows
2. Perform operations in one window
3. Verify all windows update correctly
4. Monitor backend performance

**Test with high frequency:**
1. Rapidly create/update/delete multiple items
2. Verify all updates are received
3. Check for message ordering issues
4. Monitor WebSocket connection stability

## ✅ Success Criteria

- [ ] All create operations trigger real-time updates
- [ ] All update operations trigger real-time updates
- [ ] All delete operations trigger real-time updates
- [ ] Multiple browser windows stay in sync
- [ ] No page refresh required for updates
- [ ] SignalR connection remains stable
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] Performance is acceptable (< 100ms latency)

## 📝 Test Results Template

```
Date: [DATE]
Tester: [NAME]
Backend Version: [VERSION]

TODO Operations:
- [ ] Create todo
- [ ] Update todo status
- [ ] Assign todo
- [ ] Link todo to feature
- [ ] Delete todo

Feature Operations:
- [ ] Create feature
- [ ] Update feature status
- [ ] Link element to feature

Project Operations:
- [ ] Create project
- [ ] Update project

Element Operations:
- [ ] Create element
- [ ] Update element
- [ ] Delete element

Document Operations:
- [ ] Create document

Session Operations:
- [ ] Start session
- [ ] End session

Idea Operations:
- [ ] Create idea
- [ ] Update idea
- [ ] Convert idea to project

MCP Tools:
- [ ] MCP create todo
- [ ] MCP update todo
- [ ] MCP create feature
- [ ] MCP create project

Issues Found:
[LIST ISSUES HERE]

Notes:
[ADDITIONAL NOTES]
```
