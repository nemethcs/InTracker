"""Update onboarding feature description and todos."""
import requests
import sys

API_BASE_URL = "http://localhost:3000"
FEATURE_ID = "25c124c6-c7ea-405e-81ec-6cc68cbab664"

# New feature description
NEW_DESCRIPTION = """
User Onboarding Flow - teljes folyamat regisztráció után:

**Onboarding Steps:**
1. **Welcome Screen** - Mi az InTracker? Gyors overview (Projects, Features, Todos, MCP, GitHub)
2. **MCP Setup (Kötelező)** - Generate MCP Key, Add to Cursor, verify connection
3. **GitHub Setup (Kötelező)** - Connect GitHub, show accessible repos/projects
4. **Complete!** - Redirect to Dashboard with success message

**Mandatory Setup Check:**
- Block user from accessing main app until both MCP + GitHub setup complete
- Only allow: /onboarding, /settings routes
- Track completion: setup_completed field on User model
- Show progress indicator during onboarding

**Token Expiration Handling:**
- Show warning banner when token expires in < 7 days
- Auto-check on every app load
- Provide easy reconnect button
"""

print(f"Updated feature description for: {FEATURE_ID}")
print(NEW_DESCRIPTION)
