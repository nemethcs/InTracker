# GitHub MCP Tools Workflow Analysis & Optimization

## Jelenlegi GitHub MCP Tools (15 tool)

### 1. Repository Management (2 tool)
- ✅ **mcp_connect_github_repo** - Értelmes, MCP-n keresztül kell megtenni
- ✅ **mcp_get_repo_info** - Értelmes, információ lekérése

### 2. Branch Management (6 tool)
- ❓ **mcp_create_branch_for_feature** - **KÉRDÉSES**: Branch-et lokálisan hozzuk létre (`git checkout -b`), de lehet, hogy érdemes GitHub-on is létrehozni és linkelni
- ✅ **mcp_link_branch_to_feature** - **ÉRTELMES**: Ha lokálisan hoztuk létre, linkeljük a feature-hez
- ✅ **mcp_get_feature_branches** - **ÉRTELMES**: Látni kell, milyen branch-ek vannak egy feature-hez
- ✅ **mcp_get_branches** - **ÉRTELMES**: Projekt szintű branch lista
- ✅ **mcp_get_branch_status** - **ÉRTELMES**: Látni kell az ahead/behind/conflicts állapotot

### 3. Commits (2 tool)
- ❓ **mcp_get_commits_for_feature** - **KÉRDÉSES**: Commit-ok lokálisan történnek, de lehet, hogy érdemes követni GitHub-on
- ✅ **mcp_parse_commit_message** - **ÉRTELMES**: Parse-oljuk a commit message-t és kinyerjük a feature ID-t

### 4. Issues (3 tool)
- ✅ **mcp_link_element_to_issue** - **ÉRTELMES**: Linkeljük az elemeket GitHub issue-khoz
- ✅ **mcp_get_github_issue** - **ÉRTELMES**: Issue információ lekérése
- ✅ **mcp_create_github_issue** - **ÉRTELMES**: Issue létrehozása (pl. bug report)

### 5. Pull Requests (3 tool)
- ✅ **mcp_link_todo_to_pr** - **ÉRTELMES**: Linkeljük a todo-kat PR-hez (amikor PR kész)
- ✅ **mcp_get_github_pr** - **ÉRTELMES**: PR információ lekérése
- ✅ **mcp_create_github_pr** - **ÉRTELMES**: PR létrehozása (amikor feature kész)

## Optimalizált Workflow Javaslat

### 🎯 Alapelv: Git lokálisan, GitHub integráció csak linkeléshez és információhoz

### Workflow Lépések:

#### 1. **Feature Branch Létrehozása** (Lokális Git)
```bash
# Lokálisan hozzuk létre a branch-et
git checkout -b feature/feature-name develop
git push -u origin feature/feature-name
```

**MCP Tool használata:**
- **mcp_link_branch_to_feature(featureId, branchName)** - Linkeljük a lokálisan létrehozott branch-et a feature-hez

**❌ NEM használjuk:** `mcp_create_branch_for_feature` - Felesleges, mert lokálisan hozzuk létre

#### 2. **Branch Állapot Ellenőrzése** (MCP)
```bash
# Lokálisan ellenőrizzük
git status
git branch --show-current
```

**MCP Tool használata:**
- **mcp_get_feature_branches(featureId)** - Látni, milyen branch-ek vannak a feature-hez
- **mcp_get_branch_status(projectId, branchName)** - Látni az ahead/behind/conflicts állapotot

#### 3. **Munka Feature-n** (Lokális Git + InTracker)
```bash
# Lokálisan dolgozunk
git add .
git commit -m "feat(scope): description [feature:featureId]"
git push
```

**MCP Tool használata:**
- **mcp_parse_commit_message(commitMessage)** - Parse-oljuk a commit message-t és kinyerjük a feature ID-t (opcionális, validációhoz)
- **mcp_update_todo_status(todoId, "in_progress")** - Todo státusz frissítése
- **mcp_update_todo_status(todoId, "tested")** - Todo tesztelés után
- **mcp_update_todo_status(todoId, "done")** - Todo kész

#### 4. **Pull Request Létrehozása** (MCP)
Amikor a feature kész (minden todo `done`, feature `tested`):

**MCP Tool használata:**
- **mcp_create_github_pr(projectId, title, head, body, base, todoId?)** - PR létrehozása
- **mcp_link_todo_to_pr(todoId, prNumber)** - Todo-k linkelése a PR-hez (ha több todo van, mindegyiket linkeljük)

#### 5. **PR Merge Után** (Lokális Git + InTracker)
```bash
# Lokálisan merge-eljük
git checkout develop
git pull origin develop
git merge feature/feature-name
git push origin develop
```

**MCP Tool használata:**
- **mcp_update_feature_status(featureId, "merged")** - Feature státusz frissítése
- **mcp_get_github_pr(projectId, prNumber)** - PR információ lekérése (ellenőrzéshez)

#### 6. **Issue Kezelés** (MCP - Opcionális)
Ha bug report vagy feature request van:

**MCP Tool használata:**
- **mcp_create_github_issue(projectId, title, body, labels?, elementId?)** - Issue létrehozása
- **mcp_link_element_to_issue(elementId, issueNumber)** - Elem linkelése issue-hoz
- **mcp_get_github_issue(projectId, issueNumber)** - Issue információ lekérése

## 🔄 Optimalizált Tool Használat

### ✅ **Használjuk ezeket:**
1. **mcp_connect_github_repo** - Repository kapcsolás
2. **mcp_get_repo_info** - Repository információ
3. **mcp_link_branch_to_feature** - Branch linkelés (lokálisan létrehozott branch-hez)
4. **mcp_get_feature_branches** - Feature branch-ek lekérése
5. **mcp_get_branch_status** - Branch állapot ellenőrzése
6. **mcp_parse_commit_message** - Commit message parse-olás (validációhoz)
7. **mcp_create_github_pr** - PR létrehozása
8. **mcp_link_todo_to_pr** - Todo linkelés PR-hez
9. **mcp_get_github_pr** - PR információ
10. **mcp_create_github_issue** - Issue létrehozása
11. **mcp_link_element_to_issue** - Elem linkelés issue-hoz
12. **mcp_get_github_issue** - Issue információ

### ❓ **Kérdéses / Kevesebb használat:**
1. **mcp_create_branch_for_feature** - **DEPRECATED / NEM AJÁNLOTT**: Branch-et lokálisan hozzuk létre, csak linkeljük
2. **mcp_get_commits_for_feature** - **OPCIONÁLIS**: Commit-ok lokálisan történnek, de lehet, hogy érdemes követni GitHub-on (statisztikákhoz)

### ❌ **NEM használjuk:**
- Nincs olyan tool, amit teljesen el kellene távolítani, de `mcp_create_branch_for_feature` helyett inkább `mcp_link_branch_to_feature`-t használjuk

## 📋 Javasolt Workflow Frissítések

### 1. **Branch Létrehozás Workflow Módosítása**

**Jelenlegi (ROSSZ):**
```
1. mcp_create_branch_for_feature(featureId)
2. git checkout feature/feature-name
```

**Javasolt (JÓ):**
```
1. git checkout -b feature/feature-name develop  # Lokálisan
2. git push -u origin feature/feature-name       # Push lokálisan
3. mcp_link_branch_to_feature(featureId, "feature/feature-name")  # Linkelés
```

### 2. **Commit Workflow**

**Jelenlegi:**
```
1. git commit -m "feat(scope): description [feature:featureId]"
2. git push
```

**Javasolt (ugyanaz, de parse-olhatjuk):**
```
1. git commit -m "feat(scope): description [feature:featureId]"
2. git push
3. mcp_parse_commit_message(commitMessage)  # Opcionális validációhoz
```

### 3. **PR Létrehozás Workflow**

**Jelenlegi:**
```
1. mcp_create_github_pr(projectId, title, head, base, todoId?)
2. mcp_link_todo_to_pr(todoId, prNumber)
```

**Javasolt (ugyanaz, de jobban dokumentálva):**
```
1. Feature tested státuszban van
2. mcp_create_github_pr(projectId, title, head="feature/feature-name", base="develop", todoId?)
3. Minden kapcsolódó todo linkelése: mcp_link_todo_to_pr(todoId, prNumber)
```

## 🎯 Összefoglalás

### Alapelv:
- **Git parancsok lokálisan futnak** (branch creation, commits, push, merge)
- **MCP toolok csak linkeléshez és információhoz** (branch linking, PR creation, issue linking)
- **InTracker-ben követjük a haladást** (feature status, todo status)

### Optimalizált Tool Használat:
- ✅ **12 tool aktívan használva**
- ❓ **1 tool opcionális** (mcp_get_commits_for_feature)
- ⚠️ **1 tool deprecated** (mcp_create_branch_for_feature) - helyette lokális git + link_branch

### Következő Lépések:
1. Frissítsük a workflow dokumentációt
2. Deprecate-eljük vagy módosítsuk a `mcp_create_branch_for_feature` tool leírását
3. Frissítsük a Cursor Guide-ot az új workflow-val
4. Frissítsük a cursor rules-t az optimalizált workflow-val
