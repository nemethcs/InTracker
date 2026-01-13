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
- 🔍 **Optional:** Verify connection (ping MCP endpoint)

**Validáció:** Nem lehet továbblépni, amíg nincs API key generálva.

**Flow:**
```
User clicks "Generate MCP Key"
  ↓
Backend generates key
  ↓
Frontend shows deeplink + manual config
  ↓
User clicks "Add to Cursor" OR copies config
  ↓
User clicks "Next" (key existence validated)
  ↓
→ Step 3
```

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
    # Computed: MCP key exists AND GitHub connected
```

### Setup Completion Logic
```python
def is_setup_complete(user: User) -> bool:
    has_mcp_key = db.query(McpApiKey).filter(McpApiKey.user_id == user.id, McpApiKey.is_active == True).first() is not None
    has_github = user.github_access_token_encrypted is not None
    return has_mcp_key and has_github
```

### API Endpoint
```
GET /auth/me
Response:
{
  ...user fields,
  "setup_completed": true/false
}
```

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
- [ ] Create `McpSetupStep.tsx`
- [ ] Create `GitHubSetupStep.tsx`
- [ ] Create `CompletionStep.tsx`
- [ ] Create `Onboarding.tsx` (main page with stepper)
- [ ] Update `Register.tsx` (redirect to `/onboarding`)
- [ ] Add route guard in `App.tsx`
- [ ] Create `ExpirationWarningBanner.tsx`

### Backend (FastAPI)
- [ ] Add `setup_completed` field to User model
- [ ] Add `github_token_expires_at` to `/auth/me` response
- [ ] Create Alembic migration for new field

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

