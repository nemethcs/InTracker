# GitHub OAuth Token Expiration Fix

## Probléma
- A GitHub OAuth tokenek 8 óránként lejárnak
- Nincs refresh token
- Rossz UX: 8 óránként újra kell csatlakozni

## Megoldások

### ✅ Option 1: Non-Expiring Tokens (Javasolt)

A GitHub OAuth Apps alapértelmezésben **nem lejáró tokeneket** adnak (kivéve 1 év inaktivitás után).

**GitHub OAuth App Settings-ben:**
1. Menj: https://github.com/settings/developers
2. Keresd meg az OAuth App-ot (InTracker)
3. **Refresh token expiration**: Állítsd **"Opt-out"**-ra vagy **ne állíts be semmilyen expiration-t**
4. Ez biztosítja hogy a tokenek NE járjanak le 8 óra után

**Backend kód változás:**
```python
# backend/src/services/github_oauth_service.py
# Ha a GitHub NEM ad expires_in-t, akkor nincs lejárat (vagy 1 év)
expires_in = token_data.get("expires_in")  # None ha nincs expiration
if expires_in:
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
else:
    # No expiration vagy 1 year
    expires_at = datetime.utcnow() + timedelta(days=365)
```

### ✅ Option 2: Refresh Token Support

GitHub OAuth Apps (2021 után) támogatják a refresh token-eket.

**GitHub OAuth App Settings-ben:**
1. Menj: https://github.com/settings/developers
2. OAuth App → Settings
3. **Enable refresh token rotation**: Check ✅
4. **Refresh token expiration**: Állítsd be (pl. 6 months)

**Backend kód változás:**
```python
# backend/src/services/github_oauth_service.py
# Amikor refresh token van, használjuk
if user.github_refresh_token_encrypted:
    refreshed = github_oauth_service.refresh_access_token(refresh_token)
    # Update user tokens
```

### ⚠️ Option 3: Token Expiry Frontend Warning

Ha megtartjuk a 8 órás lejáratot, legalább jelezzük a felhasználónak időben.

**Frontend változás:**
```typescript
// frontend/src/pages/Settings.tsx
// Ha token hamarosan lejár (1 óra múlva), figyelmeztessük
if (githubStatus.token_expires_at) {
  const expiresAt = new Date(githubStatus.token_expires_at);
  const now = new Date();
  const hoursRemaining = (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60);
  
  if (hoursRemaining < 1) {
    // Show warning: "GitHub token expires soon, please reconnect"
  }
}
```

## Javasolt megoldás

**1. Azonnal: Reconnect (workaround)**
- Settings → Disconnect
- Connect with GitHub újra

**2. Rövid távon: Non-expiring tokens (Option 1)**
- GitHub OAuth App settings módosítása
- Backend kód frissítése

**3. Hosszú távon: Refresh token support (Option 2)**
- Teljes OAuth flow frissítése
- Automatikus token refresh implementálása

## Implementáció

### Step 1: Ellenőrizd a GitHub OAuth App-ot
```bash
# GitHub Settings → Developer settings → OAuth Apps → InTracker
# Token expiration policy: "Tokens expire"? Change to "No expiration"
```

### Step 2: Update backend code
```python
# backend/src/services/github_oauth_service.py:163
# OLD:
expires_in = token_data.get("expires_in", 28800)  # Default: 8 hours

# NEW:
expires_in = token_data.get("expires_in")  # None if no expiration
if expires_in:
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
else:
    # No expiration - set to 1 year (GitHub expires after 1 year of inactivity)
    expires_at = datetime.utcnow() + timedelta(days=365)
```

### Step 3: Update get_user_token logic
```python
# backend/src/services/github_token_service.py
# Ha token lejárt DE nincs refresh token, NE térjünk vissza None-nal
# Inkább próbáljuk meg használni a tokent (lehet hogy még működik)
if user.github_token_expires_at and user.github_token_expires_at < (now + buffer):
    if user.github_refresh_token_encrypted:
        # Try to refresh
        refreshed = GitHubTokenService.refresh_user_token(db, user_id)
        if refreshed:
            db.refresh(user)
            if user.github_access_token_encrypted:
                return github_oauth_service.decrypt_token(user.github_access_token_encrypted)
    else:
        # No refresh token, but try to use the token anyway (might still work)
        print(f"⚠️  Token expired but no refresh token, trying anyway...")
        return github_oauth_service.decrypt_token(user.github_access_token_encrypted)

# Token is valid
return github_oauth_service.decrypt_token(user.github_access_token_encrypted)
```

## Testing

1. Disconnect GitHub
2. Connect GitHub újra
3. Check backend logs:
   - Keresd: `expires_in` value
   - Ha None vagy nagy szám (> 28800), akkor jó!
4. Várj 9 órát és ellenőrizd hogy működik-e még

## References

- [GitHub OAuth Token Expiration](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation)
- [GitHub Apps User-to-Server Tokens](https://docs.github.com/developers/apps/building-github-apps/refreshing-user-to-server-access-tokens)
