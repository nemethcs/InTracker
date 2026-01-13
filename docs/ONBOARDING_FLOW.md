# User Onboarding Flow

Teljes onboarding folyamat új felhasználók számára regisztráció után.

## 🎯 Cél

**Kötelező setup biztosítása** minden új felhasználónak:
1. ✅ MCP API Key generálása és Cursor integráció
2. ✅ GitHub OAuth csatlakozás

**Amíg nincs kész mindkettő, a felhasználó nem használhatja az InTracker-t.**

## 📋 Onboarding Lépések

### 1. Welcome Screen (Bevezetés)
**Component:** `WelcomeScreen.tsx`

**Tartalom:**
- **"Mi az InTracker?"** - Rövid bevezető
- **Quick Overview Cards:**
  - 📁 **Projects** - Organize your work
  - ⚡ **Features** - Group related tasks
  - ✅ **Todos** - Track progress
  - 🤖 **MCP** - Cursor AI integration
  - 🔗 **GitHub** - Version control sync
- **Call-to-action:** "Start Setup" gomb → Step 2

**Cél:** Gyors áttekintés az InTracker képességeiről.

---

### 2. MCP Setup (Kötelező)
**Component:** `McpSetupStep.tsx`

**Funkciók:**
- ✅ **Generate MCP API Key** gomb
- ✅ **Add to Cursor** deeplink (one-click install)
- ✅ **Manual Config** fallback (copy/paste JSON)
- ✅ **Verify Connection** gomb (KÖTELEZŐ!) - Hívja az `mcp_verify_connection` tool-t

**Validáció:** 
- Nem lehet továbblépni, amíg nincs API key generálva
- **KÖTELEZŐ:** MCP verify sikeresen lefutott (Cursor tényleg csatlakozva van)

**Flow:**
```
User clicks "Generate MCP Key"
  ↓
Backend generates key
  ↓
Frontend shows deeplink + manual config
  ↓
User clicks "Add to Cursor" deeplink (opens Cursor, installs MCP)
  ↓
Frontend shows "Verify Connection" button with Cursor prompt deeplink
  ↓
User clicks deeplink: cursor://anysphere.cursor-deeplink/prompt?text=Use+the+mcp_verify_connection+tool
  ↓
Cursor opens with prompt pre-filled: "Use the mcp_verify_connection tool"
  ↓
User confirms prompt in Cursor
  ↓
Cursor Agent: Calls mcp_verify_connection tool
  ↓
Backend: Saves mcp_verified_at timestamp, broadcasts SignalR 'mcpVerified' event
  ↓
Frontend: SignalR listener receives 'mcpVerified' event (real-time, no polling!)
  ↓
Frontend: Shows success ✅, enables "Next" button, saves onboarding_step=3
  ↓
User clicks "Next" (only if verified)
  ↓
→ Step 3 (GitHub Setup)
```

**MCP Verify Tool:**
- **Tool name:** `mcp_verify_connection`
- **Purpose:** Ellenőrzi, hogy a Cursor valóban csatlakozva van és kommunikál az MCP szerverrel
- **Called by:** Cursor Agent (via prompt deeplink)
- **Implementation:** 
  - Simple verification: Returns success if tool can be called
  - Backend saves `mcp_verified_at` timestamp to User model
  - Backend broadcasts SignalR event: `mcpVerified` with user_id
  - Returns: `{verified: true, message: "MCP connection verified successfully"}`
- **Frontend Integration:**
  - Shows "Verify Connection" button with Cursor prompt deeplink
  - Deeplink format: `cursor://anysphere.cursor-deeplink/prompt?text=Use+the+mcp_verify_connection+tool`
  - Frontend subscribes to SignalR `mcpVerified` event (real-time, no polling!)
  - When event received, shows success ✅ and enables "Next" button
  - Web fallback: `https://cursor.com/link/prompt?text=Use+the+mcp_verify_connection+tool`

**Cursor Prompt Deeplink:**
- **Format:** `cursor://anysphere.cursor-deeplink/prompt?text=Use+the+mcp_verify_connection+tool`
- **Web format:** `https://cursor.com/link/prompt?text=Use+the+mcp_verify_connection+tool`
- **Reference:** [Cursor Deeplinks Documentation](https://cursor.com/docs/integrations/deeplinks)
- **Benefits:** 
  - One-click verify (no manual typing)
  - Pre-filled prompt in Cursor
  - Better UX than instruction text

---

### 3. GitHub Setup (Kötelező)
**Component:** `GitHubSetupStep.tsx`

**Funkciók:**
- ✅ **"Connect with GitHub"** OAuth button
- ✅ Handle OAuth callback (code, state)
- ✅ Display connected status (username + avatar)
- ✅ Show accessible projects/repos preview (optional)

**Validáció:** Nem lehet továbblépni, amíg nincs GitHub csatlakozva.

**Flow:**
```
User clicks "Connect with GitHub"
  ↓
Redirect to GitHub OAuth (authorize)
  ↓
GitHub redirects back to /onboarding?code=XXX&state=YYY&step=3
  ↓
Frontend exchanges code for tokens
  ↓
Display connected status
  ↓
User clicks "Next"
  ↓
→ Step 4
```

---

### 4. Completion (Befejezés)
**Component:** `CompletionStep.tsx`

**Tartalom:**
- ✅ **Success message:** "Setup Complete! 🎉"
- ✅ **Summary:** What was configured (MCP + GitHub)
- ✅ **"Go to Dashboard"** button → redirect to `/`
- 🎓 **Optional:** Quick tips vagy "Next steps"

**Flow:**
```
Display success screen
  ↓
User clicks "Go to Dashboard"
  ↓
Update user.setup_completed = true (backend or localStorage)
  ↓
→ Redirect to Dashboard (/)
```

---

## 🚧 Route Guard & Access Control

### ProtectedRoute Logic

```typescript
// App.tsx vagy route guard
if (!user.setup_completed) {
  // Allow only onboarding and settings
  if (path !== '/onboarding' && path !== '/settings') {
    redirect('/onboarding')
  }
} else {
  // Setup complete, allow all routes
  // But still show token expiration warning if needed
}
```

### Allowed Routes Before Setup Complete
- ✅ `/onboarding` (all steps)
- ✅ `/settings` (for manual config/reconnect)
- ✅ `/logout`
- ❌ All other routes (redirect to `/onboarding`)

---

## 🗄️ Backend Changes

### User Model
```python
class User(Base):
    # ... existing fields
    setup_completed = Column(Boolean, default=False, nullable=False)
    onboarding_step = Column(Integer, default=0, nullable=False)  # 0=not started, 1=welcome, 2=mcp_setup, 3=mcp_verify, 4=github_setup, 5=complete
    mcp_verified_at = Column(DateTime, nullable=True)  # Timestamp when mcp_verify_connection was successfully called
    # Computed: MCP key exists AND GitHub connected
```

**Onboarding Step Values:**
- `0` = Not started (new user)
- `1` = Welcome screen completed
- `2` = MCP key generated
- `3` = MCP connection verified
- `4` = GitHub connected
- `5` = Complete (setup_completed = true)

### Setup Completion Logic
```python
def is_setup_complete(user: User) -> bool:
    has_mcp_key = db.query(McpApiKey).filter(McpApiKey.user_id == user.id, McpApiKey.is_active == True).first() is not None
    has_github = user.github_access_token_encrypted is not None
    return has_mcp_key and has_github
```

### API Endpoints

#### GET /auth/me
```json
{
  ...user fields,
  "setup_completed": true/false,
  "onboarding_step": 3,
  "github_token_expires_at": "2025-01-13T..."
}
```

#### GET /api/onboarding/mcp-verification-status
**Request:** (no body, uses current user from auth)
**Response:**
```json
{
  "verified": true,
  "verified_at": "2025-01-13T15:30:00Z",
  "message": "MCP connection verified successfully"
}
```
**Not Verified Response:**
```json
{
  "verified": false,
  "verified_at": null,
  "message": "MCP connection not yet verified. Please add MCP to Cursor and use the verify tool."
}
```

**Note:** This endpoint is polled by frontend every 2-3 seconds during onboarding Step 2.

---

## 🎨 UI/UX Design

### Stepper Component
```
[1] Welcome  →  [2] MCP Setup  →  [3] GitHub  →  [4] Complete
  (active)       (disabled)       (disabled)     (disabled)
```

**Progress indicator:**
- Active step: Highlighted
- Completed steps: ✅ Check mark
- Future steps: Greyed out

### Navigation
- **"Next"** button (disabled if step not complete)
- **"Back"** button (optional, allows going back)
- **"Skip"** button (disabled/hidden - no skipping allowed!)

---

## 🔔 Token Expiration Warning

**Post-onboarding feature** (shows after setup complete):

### ExpirationWarningBanner Component
```typescript
if (user.github_token_expires_at) {
  const daysUntilExpiration = calculateDays(user.github_token_expires_at)
  if (daysUntilExpiration < 7) {
    <Alert variant="warning">
      ⚠️ Your GitHub token expires in {daysUntilExpiration} days.
      <Button>Reconnect GitHub</Button>
    </Alert>
  }
}
```

**Placement:** Top of Dashboard or main layout (after completing onboarding).

---

## 📊 Implementation Todos

### Frontend (React)
- [ ] Create `WelcomeScreen.tsx`
- [ ] Create `McpSetupStep.tsx` (with Cursor prompt deeplink + SignalR listener)
- [ ] Create `GitHubSetupStep.tsx`
- [ ] Create `CompletionStep.tsx`
- [ ] Create `Onboarding.tsx` (main page with stepper + progress persistence)
- [ ] Create `ProgressBar.tsx` component (visual progress indicator)
- [ ] Add error handling to all onboarding steps
- [ ] Add back button to all steps (except Welcome)
- [ ] Update `Register.tsx` (redirect to `/onboarding`)
- [ ] Add route guard in `App.tsx`
- [ ] Create `ExpirationWarningBanner.tsx`

### Backend (FastAPI)
- [ ] Add `setup_completed` field to User model
- [ ] Add `onboarding_step` field to User model (INTEGER, default=0)
- [ ] Add `mcp_verified_at` field to User model (DateTime, nullable=True)
- [ ] Add `github_token_expires_at` to `/auth/me` response
- [ ] Create Alembic migration for new fields
- [ ] Create MCP verify tool (`mcp_verify_connection`) - saves `mcp_verified_at` when called
- [ ] Add SignalR broadcast in `mcp_verify_connection` handler: `mcpVerified` event
- [ ] Update `/auth/me` to return `onboarding_step` and `mcp_verified_at`

---

## 🧪 Testing

### Manual Test Flow
1. Register new user
2. Check redirect to `/onboarding`
3. Try to navigate to `/` → should redirect back
4. Complete Step 1 (Welcome)
5. Complete Step 2 (MCP)
6. Complete Step 3 (GitHub)
7. Complete Step 4 (Completion)
8. Verify redirect to Dashboard
9. Verify access to all routes
10. Check token expiration warning (if applicable)

---

## 🚀 Deployment

1. Deploy backend with migration
2. Deploy frontend with new onboarding flow
3. Existing users: `setup_completed = true` (migration default or manual update)
4. New users: Must complete onboarding

---

## 📝 Notes

- **Existing users:** Should have `setup_completed = true` by default (or set via migration)
- **Token expiration:** Check on every `/auth/me` call (app load)
- **Stepper UI:** Consider using a library like `react-step-wizard` or build custom
- **Accessibility:** Ensure keyboard navigation and screen reader support

