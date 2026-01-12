# GitHub OAuth App Setup Guide

Ez az útmutató leírja, hogyan kell létrehozni és konfigurálni a GitHub OAuth App-ot az InTracker-hez.

> **💡 Fontos megértés:** Az OAuth App csak egy "kapu" - minden felhasználó saját tokent kap, ami a **felhasználó saját GitHub jogosultságait** használja, nem az OAuth App tulajdonosának jogosultságait. Részletek: [GitHub OAuth - Hogyan működik?](./GITHUB_OAUTH_HOW_IT_WORKS.md)

## 1. GitHub OAuth App létrehozása

1. Lépj be a GitHub fiókodba
2. Menj a **Settings** → **Developer settings** → **OAuth Apps** menüpontra
   - URL: https://github.com/settings/developers
3. Kattints a **"New OAuth App"** gombra
4. Töltsd ki az űrlapot:
   - **Application name**: `InTracker` (vagy bármilyen nevet szeretnél)
   - **Homepage URL**: 
     - Production: `https://intracker.kesmarki.com`
     - Development: `http://localhost:5173`
   - **Authorization callback URL**:
     - Production: `https://intracker-api.kesmarki.com/auth/github/callback`
     - Development: `http://localhost:3000/auth/github/callback`
5. Kattints a **"Register application"** gombra

## 2. OAuth App konfiguráció

A GitHub OAuth App létrehozása után:

1. **Client ID** és **Client Secret** másolása
   - Ezeket a backend config-ban kell beállítani
   - **SOHA ne commitold ezeket a git repository-ba!**

2. **Scopes** beállítása:
   - `repo` - Teljes hozzáférés a privát repository-khoz
   - `read:org` - Szervezet információk olvasása
   - `read:user` - Felhasználói információk olvasása
   - `user:email` - Email címek olvasása

## 3. Backend konfiguráció

Add hozzá a következő environment változókat a `.env` fájlhoz:

```bash
# GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=your_client_id_here
GITHUB_OAUTH_CLIENT_SECRET=your_client_secret_here
GITHUB_OAUTH_ENCRYPTION_KEY=your_base64_encoded_fernet_key_here
```

### Encryption Key generálása

A `GITHUB_OAUTH_ENCRYPTION_KEY` egy base64-encoded Fernet key. Generálás:

```python
from cryptography.fernet import Fernet
import base64

# Generate a new key
key = Fernet.generate_key()
print(f"GITHUB_OAUTH_ENCRYPTION_KEY={base64.urlsafe_b64encode(key).decode()}")
```

**FONTOS**: 
- Ezt a kulcsot biztonságosan tárold!
- Ha elveszíted, nem tudod dekódolni a meglévő token-eket
- Használj különböző kulcsot development és production környezetekhez

## 4. Frontend URL konfiguráció

A callback URL-nek meg kell egyeznie a backend konfigurációval:

- **Development**: `http://localhost:3000/api/auth/github/callback`
- **Production**: `https://intracker-api.kesmarki.com/api/auth/github/callback`

## 5. Tesztelés

1. Indítsd el a backend-et
2. Nyisd meg a Settings oldalt a frontenden
3. Kattints a "Connect with GitHub" gombra
4. Engedélyezd a hozzáférést a GitHub-on
5. Ellenőrizd, hogy a callback sikeresen lefut

## Troubleshooting

### "Invalid redirect_uri" hiba
- Ellenőrizd, hogy a callback URL pontosan egyezik-e a GitHub OAuth App beállításaival
- A callback URL case-sensitive!

### "Invalid client_id" hiba
- Ellenőrizd, hogy a `GITHUB_OAUTH_CLIENT_ID` helyesen van-e beállítva
- Ellenőrizd, hogy nincs-e extra space vagy newline a végén

### "Invalid client_secret" hiba
- Ellenőrizd, hogy a `GITHUB_OAUTH_CLIENT_SECRET` helyesen van-e beállítva
- Lehet, hogy újra kell generálni a secret-et a GitHub-on

### Token encryption hiba
- Ellenőrizd, hogy a `GITHUB_OAUTH_ENCRYPTION_KEY` helyesen van-e beállítva
- A key base64-encoded kell legyen
