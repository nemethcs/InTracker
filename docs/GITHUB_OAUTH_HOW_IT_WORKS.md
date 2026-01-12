# GitHub OAuth App - Hogyan működik?

## Alapvető működés

### OAuth App vs. Felhasználói token

**Fontos megértés:**
- Az **OAuth App** csak egy "kapu" vagy "engedélyező mechanizmus"
- Amikor egy felhasználó összeköti a GitHub fiókját, az OAuth App **nem** az OAuth App tulajdonosának token-jét használja
- Minden felhasználó **saját, egyedi OAuth token-t** kap
- Ez a token a **felhasználó saját GitHub jogosultságait** használja

### Példa: Csapat és projektek

Tegyük fel:
- Van egy csapat: "Development Team"
- A csapathoz tartozik 3 projekt:
  - Projekt A: `github.com/company/project-a`
  - Projekt B: `github.com/company/project-b`
  - Projekt C: `github.com/company/project-c`

**Felhasználó regisztrál és összeköti a GitHub fiókját:**
1. A felhasználó regisztrál az InTracker-be és csatlakozik a "Development Team"-hez
2. Az InTracker-ben látja mind a 3 projektet (mert a csapat tagja)
3. Összeköti a GitHub fiókját az OAuth App-pal
4. Az OAuth App létrehoz egy **felhasználó-specifikus tokent**
5. Ez a token a **felhasználó GitHub jogosultságait** használja

**Mi történik a hozzáférés ellenőrzésnél:**
- Projekt A: A felhasználó GitHub-on hozzáfér → ✅ **Access granted**
- Projekt B: A felhasználó GitHub-on hozzáfér → ✅ **Access granted**
- Projekt C: A felhasználó GitHub-on **NEM** fér hozzá → ❌ **No access**

**Eredmény:**
- Az InTracker-ben látja mind a 3 projektet (csapat tagja)
- De csak 2 projekthez fér hozzá GitHub-on keresztül (ahol van GitHub jogosultsága)

## Miért van így?

### OAuth App tulajdonos vs. Felhasználó

**OAuth App tulajdonos:**
- Az OAuth App-ot létrehozó személy (pl. te, az admin)
- Az OAuth App csak egy "kapu" - nem ad hozzáférést repository-khoz
- Az OAuth App Client ID és Secret csak az OAuth flow-hoz kell

**Felhasználó:**
- Minden felhasználó, aki összeköti a GitHub fiókját
- Saját, egyedi OAuth token-t kap
- Ez a token csak azokhoz a repository-khoz fér hozzá, amelyekhez a **felhasználó** hozzáfér

### GitHub jogosultságok

A felhasználó GitHub-on hozzáférhet egy repository-hoz, ha:
1. **Repository owner/collaborator** - közvetlenül hozzáadva
2. **Organization member** - a repository-hoz tartozó organization tagja
3. **Team member** - egy team tagja, ami hozzáfér a repository-hoz
4. **Public repository** - mindenki hozzáfér

## Gyakori kérdések

### Q: Ha én hozom létre az OAuth App-ot, akkor az nem csak az én repo-jaimat látja?

**A:** Nem! Az OAuth App csak egy "kapu". Minden felhasználó saját tokent kap, ami a **felhasználó** jogosultságait használja, nem a te jogosultságaidat.

### Q: Hogyan lehet, hogy egy felhasználó látja a projektet az InTracker-ben, de nem fér hozzá GitHub-on?

**A:** Ez normális! Az InTracker-ben a projektek a **csapat tagság** alapján láthatók. A GitHub hozzáférés a **GitHub jogosultságok** alapján működik. Ez két külön rendszer:
- **InTracker**: Csapat tagság → Projekt láthatóság
- **GitHub**: Repository jogosultságok → Repository hozzáférés

### Q: Mit kell tenni, ha egy felhasználó hozzáférést szeretne egy repository-hoz?

**A:** A repository owner-nek vagy admin-nak hozzá kell adnia a felhasználót a GitHub repository-hoz:
- Collaborator-ként, vagy
- Organization/Team tagként

### Q: Mi történik, ha egy projektnek nincs GitHub repository-ja?

**A:** Ha egy projektnek nincs `github_repo_url` mezője, akkor a felhasználó automatikusan hozzáfér (nincs GitHub függőség). Csak azokhoz a projektekhez kell GitHub hozzáférés, amelyeknek van GitHub repository-ja.

## Technikai részletek

### Token tárolás

- Minden felhasználó token-je **külön-külön** van tárolva az adatbázisban
- A token-ek **titkosítva** vannak tárolva (Fernet encryption)
- A token-ek a felhasználó `users` táblájában vannak:
  - `github_access_token_encrypted`
  - `github_refresh_token_encrypted`
  - `github_token_expires_at`

### Hozzáférés ellenőrzés

Amikor egy MCP tool vagy API endpoint hozzáférést ellenőriz:
1. Lekéri a felhasználó OAuth token-jét
2. Inicializál egy `GitHubService`-t a felhasználó token-jével
3. Ellenőrzi, hogy a token hozzáfér-e a repository-hoz
4. Visszaadja az eredményt

### Példa kód

```python
# Backend: github_access_service.py
def validate_project_access_for_user(db, user_id):
    # 1. Lekéri a felhasználó token-jét
    token = github_token_service.get_user_token(db, user_id)
    
    # 2. GitHubService a felhasználó token-jével
    github_service = GitHubService(user_id=user_id)
    
    # 3. Ellenőrzi a repository hozzáférést
    has_access = github_service.validate_repo_access(owner, repo)
    
    # 4. Visszaadja az eredményt
    return has_access
```

## Összefoglalás

✅ **OAuth App** = Csak egy "kapu", nem ad hozzáférést  
✅ **Felhasználói token** = A felhasználó saját jogosultságait használja  
✅ **InTracker projektek** = Csapat tagság alapján láthatók  
✅ **GitHub hozzáférés** = Repository jogosultságok alapján működik  
✅ **Két külön rendszer** = InTracker és GitHub jogosultságok függetlenek
