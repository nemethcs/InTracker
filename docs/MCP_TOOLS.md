# InTracker MCP Tools Dokumentáció

Ez a dokumentum röviden és közérthetően leírja az összes elérhető MCP tool-t és azok használatát.

## ⚠️ Fontos megjegyzések

### Git műveletek
- **Lokális git műveletek** (pl. `git status`, `git branch --show-current`, `git commit`, `git push`) **nem** MCP toolok, hanem **Cursor terminal parancsok**.
- Az MCP szerver Docker container-ben fut, **nem fér hozzá a lokális git repository-hoz**.
- A GitHub toolok **GitHub API-t** használnak (pl. branch létrehozás, PR kezelés, issue kezelés), **nem lokális git-et**.

### Lokális fájlrendszer hozzáférés
- **Fájlrendszer toolok** (pl. `mcp_identify_project_by_path`, `mcp_parse_file_structure`, `mcp_analyze_codebase`) **kötelező path paramétert igényelnek** Docker környezetben.
- Az MCP szerver Docker container-ben fut, **nem fér hozzá a lokális fájlrendszerhez** `os.getcwd()` nélkül.
- Ha path paraméter nélkül hívod ezeket a toolokat, hibaüzenetet kapsz.

### Workflow
- **Branch ellenőrzés:** `git branch --show-current` (Cursor terminal)
- **Git műveletek:** `git status`, `git diff`, `git add`, `git commit`, `git push` (Cursor terminal)
- **GitHub műveletek:** MCP toolok (pl. `mcp_create_branch_for_feature`, `mcp_create_github_pr`)

## 📋 Tartalomjegyzék

- [Projekt Műveletek](#projekt-műveletek) (10 tool)
- [Feature Műveletek](#feature-műveletek) (7 tool)
- [Todo Műveletek](#todo-műveletek) (5 tool)
- [Session Műveletek](#session-műveletek) (3 tool)
- [Dokumentum Műveletek](#dokumentum-műveletek) (3 tool)
- [GitHub Integráció](#github-integráció) (15 tool)
- [Idea Műveletek](#idea-műveletek) (5 tool)
- [Import és Analízis](#import-és-analízis) (4 tool)

---

## Projekt Műveletek

### `mcp_get_project_context`
**Mit csinál:** Teljes projekt információ lekérése (metadata, struktúra, feature-ök, todo-k, resume context).  
**Mikor használd:** Amikor átfogó projekt információra van szükséged. Nagy projekteknél opcionális paraméterekkel csökkentheted a válasz méretét.  
**Paraméterek:** `projectId` (kötelező), `includeFeatures`, `includeTodos`, `includeStructure`, `includeResumeContext`, `featuresLimit`, `todosLimit`, `summaryOnly`

### `mcp_get_resume_context`
**Mit csinál:** Resume context lekérése - mi volt az utolsó session, mik a következő todo-k, aktív elemek, blokkolók, korlátok.  
**Mikor használd:** Minden session elején, hogy folytasd a munkát ott, ahol abbahagytad.  
**Paraméterek:** `projectId` (kötelező), `userId` (opcionális)

### `mcp_get_project_structure`
**Mit csinál:** Projekt hierarchikus struktúra lekérése (elemek fa struktúrában).  
**Mikor használd:** Amikor a projekt struktúráját szeretnéd megérteni vagy megjeleníteni.  
**Paraméterek:** `projectId` (kötelező)

### `mcp_get_active_todos`
**Mit csinál:** Aktív todo-k lekérése (new, in_progress, done státuszúak).  
**Mikor használd:** Amikor a következő munkához szükséges todo-kat szeretnéd látni.  
**Paraméterek:** `projectId` (kötelező), `status`, `featureId`, `userId` (opcionális)

### `mcp_create_project`
**Mit csinál:** Új projekt létrehozása egy team számára.  
**Mikor használd:** Amikor új projektet indítasz.  
**Paraméterek:** `name`, `teamId` (kötelező), `description`, `status`, `tags`, `technologyTags`, `cursorInstructions`, `githubRepoUrl` (opcionális)

### `mcp_list_projects`
**Mit csinál:** Projekt lista lekérése (szűrhető státusz szerint).  
**Mikor használd:** Amikor a hozzáférhető projekteket szeretnéd listázni.  
**Paraméterek:** `status` (opcionális)

### `mcp_update_project`
**Mit csinál:** Projekt frissítése (név, leírás, státusz, stb.).  
**Mikor használd:** Amikor projekt információt módosítasz.  
**Paraméterek:** `projectId` (kötelező), `name`, `description`, `status`, `tags`, `technologyTags`, `cursorInstructions`, `githubRepoUrl` (opcionális)

### `mcp_identify_project_by_path`
**Mit csinál:** Projekt azonosítása working directory alapján (.intracker/config.json, GitHub repo URL, vagy projekt név alapján).  
**Mikor használd:** Amikor automatikusan szeretnéd azonosítani a projektet a jelenlegi munkakönyvtárból.  
**Paraméterek:** `path` (kötelező Docker környezetben)  
**⚠️ FONTOS:** Docker környezetben a `path` paraméter **kötelező**, mert az MCP szerver nem fér hozzá a lokális fájlrendszerhez `os.getcwd()` nélkül.

### `mcp_load_cursor_rules`
**Mit csinál:** Cursor rules automatikus generálása és betöltése a projekt `.cursor/rules/intracker-project-rules.mdc` fájlba.  
**Mikor használd:** Minden session elején (első alkalommal), vagy amikor a rules változnak.  
**Paraméterek:** `projectId` (kötelező), `projectPath` (opcionális)

### `mcp_enforce_workflow`
**Mit csinál:** **KÖTELEZŐ** - Automatikusan azonosítja a projektet, betölti a resume context-et és cursor rules-t, visszaadja a workflow checklist-et.  
**Mikor használd:** **MINDEN session elején KÖTELEZŐEN!**  
**Paraméterek:** `path` (opcionális)

---

## Feature Műveletek

### `mcp_create_feature`
**Mit csinál:** Új feature létrehozása egy projekthez. Feature-ök csoportosítják a kapcsolódó todo-kat és követik a haladást.  
**Mikor használd:** Amikor új funkciót indítasz, amit több todo-val fogsz megvalósítani.  
**Paraméterek:** `projectId`, `name` (kötelező), `description`, `elementIds` (opcionális)

### `mcp_get_feature`
**Mit csinál:** Feature részletes információinak lekérése todo-kkal és elemekkel.  
**Mikor használd:** Amikor egy feature részleteit szeretnéd látni.  
**Paraméterek:** `featureId` (kötelező)

### `mcp_list_features`
**Mit csinál:** Feature lista lekérése egy projekthez (szűrhető státusz szerint).  
**Mikor használd:** Amikor egy projekt összes feature-jét szeretnéd látni.  
**Paraméterek:** `projectId` (kötelező), `status` (opcionális)

### `mcp_update_feature_status`
**Mit csinál:** Feature státusz frissítése (new → in_progress → done → tested → merged). Automatikusan újraszámolja a haladást a todo-k alapján.  
**Mikor használd:** Amikor egy feature státuszát változtatod (pl. amikor minden todo kész).  
**Paraméterek:** `featureId` (kötelező), `status` (kötelező)

### `mcp_get_feature_todos`
**Mit csinál:** Egy feature-hez tartozó todo-k lekérése.  
**Mikor használd:** Amikor egy feature todo-jait szeretnéd látni.  
**Paraméterek:** `featureId` (kötelező), `status` (opcionális)

### `mcp_get_feature_elements`
**Mit csinál:** Egy feature-hez kapcsolódó projekt elemek lekérése.  
**Mikor használd:** Amikor egy feature-hez kapcsolódó kód elemeket szeretnéd látni.  
**Paraméterek:** `featureId` (kötelező)

### `mcp_link_element_to_feature`
**Mit csinál:** Projekt elem kapcsolása egy feature-hez.  
**Mikor használd:** Amikor egy kód elemet (pl. modult) egy feature-hez szeretnél kapcsolni.  
**Paraméterek:** `featureId`, `elementId` (kötelező)

---

## Todo Műveletek

### `mcp_create_todo`
**Mit csinál:** Új todo létrehozása egy projekt elemhez. Opcionálisan kapcsolható egy feature-hez.  
**Mikor használd:** Amikor új feladatot hozol létre. **Fontos:** Használd a team nyelvét a cím és leírás létrehozásánál!  
**Paraméterek:** `elementId`, `title` (kötelező), `description`, `featureId`, `priority` (opcionális)

### `mcp_update_todo_status`
**Mit csinál:** Todo státusz frissítése (new → in_progress → done). Optimistic locking-ot használ a konfliktusok elkerülésére.  
**Mikor használd:** Amikor egy todo státuszát változtatod (pl. munkakezdés, befejezés).  
**Paraméterek:** `todoId` (kötelező), `status` (kötelező), `expectedVersion` (kötelező - az előző olvasásból)

### `mcp_list_todos`
**Mit csinál:** Todo lista lekérése (szűrhető projekt, feature, elem, státusz szerint).  
**Mikor használd:** Amikor todo-kat szeretnél listázni.  
**Paraméterek:** `projectId`, `featureId`, `elementId`, `status`, `userId` (opcionális)

### `mcp_assign_todo`
**Mit csinál:** Todo hozzárendelése egy felhasználóhoz. Ha egy todo "in_progress" és hozzá van rendelve, más felhasználók nem látják a "next todos" listában.  
**Mikor használd:** Amikor egy todo-t egy konkrét felhasználóhoz szeretnél rendelni.  
**Paraméterek:** `todoId` (kötelező), `userId` (opcionális, ha null, akkor törli a hozzárendelést)

### `mcp_link_todo_to_feature`
**Mit csinál:** Todo kapcsolása egy feature-hez (vagy kapcsolat törlése).  
**Mikor használd:** Amikor egy todo-t egy feature-hez szeretnél kapcsolni, vagy el szeretnéd távolítani.  
**Paraméterek:** `todoId` (kötelező), `featureId` (opcionális, ha null, akkor törli a kapcsolatot), `expectedVersion` (kötelező)

---

## Session Műveletek

### `mcp_start_session`
**Mit csinál:** Új munkamenet indítása. Automatikusan betölti a workflow-t és resume context-et (ha `auto_enforce_workflow: true`).  
**Mikor használd:** Minden session elején.  
**Paraméterek:** `projectId` (kötelező), `goal`, `featureIds` (opcionális)

### `mcp_update_session`
**Mit csinál:** Session frissítése - befejezett todo-k, feature-ök, jegyzetek hozzáadása.  
**Mikor használd:** Session közben, amikor haladást szeretnél rögzíteni.  
**Paraméterek:** `sessionId` (kötelező), `completedTodos`, `completedFeatures`, `notes` (opcionális)

### `mcp_end_session`
**Mit csinál:** Session befejezése és összefoglaló generálása. Frissíti a resume context-et a következő session-hez.  
**Mikor használd:** Session végén.  
**Paraméterek:** `sessionId` (kötelező), `summary` (opcionális)

---

## Dokumentum Műveletek

### `mcp_get_document`
**Mit csinál:** Dokumentum tartalmának lekérése.  
**Mikor használd:** Amikor egy dokumentum tartalmát szeretnéd olvasni.  
**Paraméterek:** `documentId` (kötelező)

### `mcp_list_documents`
**Mit csinál:** Dokumentum lista lekérése egy projekthez (szűrhető típus, elem szerint).  
**Mikor használd:** Amikor egy projekt dokumentumait szeretnéd listázni.  
**Paraméterek:** `projectId` (kötelező), `type`, `elementId`, `search`, `page`, `pageSize` (opcionális)

### `mcp_create_document`
**Mit csinál:** Új dokumentum létrehozása (pl. architecture doc, ADR, domain doc, constraints, runbook, AI instructions).  
**Mikor használd:** Amikor projekt dokumentációt hozol létre.  
**Paraméterek:** `projectId`, `type`, `title`, `content` (kötelező), `elementId`, `todoId`, `tags` (opcionális)

---

## GitHub Integráció

### Repository Műveletek

#### `mcp_connect_github_repo`
**Mit csinál:** GitHub repository kapcsolása egy projekthez.  
**Mikor használd:** Amikor egy projekthez GitHub repo-t szeretnél kapcsolni.  
**Paraméterek:** `projectId` (kötelező), `owner`, `repo` (kötelező)

#### `mcp_get_repo_info`
**Mit csinál:** GitHub repository információk lekérése (név, owner, default branch, stb.).  
**Mikor használd:** Amikor a GitHub repo információit szeretnéd látni.  
**Paraméterek:** `projectId` (kötelező)

### Branch Műveletek

#### `mcp_get_branches`
**Mit csinál:** Branch lista lekérése egy projekthez vagy feature-hez.  
**Mikor használd:** Amikor a projekthez tartozó branch-eket szeretnéd látni.  
**Paraméterek:** `projectId` (kötelező), `featureId` (opcionális)

#### `mcp_create_branch_for_feature`
**Mit csinál:** GitHub branch létrehozása egy feature-hez.  
**Mikor használd:** Amikor egy feature-hez új branch-et szeretnél létrehozni.  
**Paraméterek:** `featureId` (kötelező), `baseBranch` (opcionális, alapértelmezett: main)

#### `mcp_link_branch_to_feature`
**Mit csinál:** GitHub branch kapcsolása egy feature-hez.  
**Mikor használd:** Amikor egy meglévő branch-et egy feature-hez szeretnél kapcsolni.  
**Paraméterek:** `featureId`, `branchName` (kötelező)

#### `mcp_get_feature_branches`
**Mit csinál:** Egy feature-hez tartozó branch-ek lekérése.  
**Mikor használd:** Amikor egy feature branch-jeit szeretnéd látni.  
**Paraméterek:** `featureId` (kötelező)

#### `mcp_get_branch_status`
**Mit csinál:** Branch státusz lekérése (ahead/behind, konfliktusok).  
**Mikor használd:** Amikor ellenőrizni szeretnéd, hogy a branch mennyire van előrébb/hátrébb a base branch-hez képest.  
**Paraméterek:** `projectId`, `branchName` (kötelező)

#### `mcp_get_commits_for_feature`
**Mit csinál:** Commit lista lekérése egy feature-hez.  
**Mikor használd:** Amikor egy feature commit történetét szeretnéd látni.  
**Paraméterek:** `featureId` (kötelező)

#### `mcp_parse_commit_message`
**Mit csinál:** Commit message elemzése metadata kinyeréséhez.  
**Mikor használd:** Amikor commit message-ből szeretnél információt kinyerni (pl. feature ID, todo-k).  
**Paraméterek:** `commitMessage` (kötelező)

### Issue Műveletek

#### `mcp_link_element_to_issue`
**Mit csinál:** Projekt elem kapcsolása egy GitHub issue-hoz.  
**Mikor használd:** Amikor egy kód elemet egy GitHub issue-hoz szeretnél kapcsolni.  
**Paraméterek:** `elementId`, `issueNumber` (kötelező)

#### `mcp_get_github_issue`
**Mit csinál:** GitHub issue információk lekérése.  
**Mikor használd:** Amikor egy GitHub issue részleteit szeretnéd látni.  
**Paraméterek:** `projectId`, `issueNumber` (kötelező)

#### `mcp_create_github_issue`
**Mit csinál:** Új GitHub issue létrehozása.  
**Mikor használd:** Amikor új GitHub issue-t szeretnél létrehozni.  
**Paraméterek:** `projectId`, `title` (kötelező), `body`, `labels`, `elementId` (opcionális)

### Pull Request Műveletek

#### `mcp_link_todo_to_pr`
**Mit csinál:** Todo kapcsolása egy GitHub pull request-hez.  
**Mikor használd:** Amikor egy todo-t egy PR-hez szeretnél kapcsolni.  
**Paraméterek:** `todoId`, `prNumber` (kötelező)

#### `mcp_get_github_pr`
**Mit csinál:** GitHub pull request információk lekérése.  
**Mikor használd:** Amikor egy PR részleteit szeretnéd látni.  
**Paraméterek:** `projectId`, `prNumber` (kötelező)

#### `mcp_create_github_pr`
**Mit csinál:** Új GitHub pull request létrehozása.  
**Mikor használd:** Amikor új PR-t szeretnél létrehozni.  
**Paraméterek:** `projectId`, `title`, `head` (kötelező), `body`, `base`, `todoId` (opcionális)

---

## Idea Műveletek

### `mcp_create_idea`
**Mit csinál:** Új ötlet létrehozása egy team számára.  
**Mikor használd:** Amikor új ötletet szeretnél rögzíteni. **Fontos:** Használd a team nyelvét a cím és leírás létrehozásánál!  
**Paraméterek:** `title`, `teamId` (kötelező), `description`, `status`, `tags` (opcionális)

### `mcp_list_ideas`
**Mit csinál:** Ötlet lista lekérése (szűrhető státusz, team szerint).  
**Mikor használd:** Amikor a hozzáférhető ötleteket szeretnéd listázni.  
**Paraméterek:** `status`, `teamId`, `userId` (opcionális)

### `mcp_get_idea`
**Mit csinál:** Ötlet részletes információinak lekérése.  
**Mikor használd:** Amikor egy ötlet részleteit szeretnéd látni.  
**Paraméterek:** `ideaId` (kötelező)

### `mcp_update_idea`
**Mit csinál:** Ötlet frissítése (cím, leírás, státusz, címkék).  
**Mikor használd:** Amikor egy ötlet információit módosítod.  
**Paraméterek:** `ideaId` (kötelező), `title`, `description`, `status`, `tags` (opcionális)

### `mcp_convert_idea_to_project`
**Mit csinál:** Ötlet konvertálása projektté.  
**Mikor használd:** Amikor egy ötletet projektté szeretnél alakítani.  
**Paraméterek:** `ideaId` (kötelező), `projectName`, `projectDescription`, `projectStatus`, `projectTags`, `technologyTags` (opcionális)

---

## Import és Analízis

### `mcp_parse_file_structure`
**Mit csinál:** Projekt fájl struktúra elemzése és automatikus projekt elemek létrehozása hierarchikus struktúrában (modulok, komponensek).  
**Mikor használd:** Új projekteknél, amikor a könyvtár struktúrából szeretnél automatikusan projekt elemeket létrehozni. Csak akkor működik, ha nincsenek még elemek.  
**Paraméterek:** `projectId`, `projectPath` (kötelező Docker környezetben), `maxDepth` (alapértelmezett: 3), `ignorePatterns` (opcionális)  
**⚠️ FONTOS:** Docker környezetben a `projectPath` paraméter **kötelező**, mert az MCP szerver nem fér hozzá a lokális fájlrendszerhez.

### `mcp_import_github_issues`
**Mit csinál:** GitHub issue-k importálása todo-kként egy projekthez. Opcionálisan létrehozhat elemeket issue-khoz, ha nincs megfelelő elem.  
**Mikor használd:** Amikor meglévő GitHub issue-kat szeretnél importálni InTracker todo-kként.  
**Paraméterek:** `projectId` (kötelező), `labels`, `state` (alapértelmezett: open), `createElements` (alapértelmezett: true)

### `mcp_import_github_milestones`
**Mit csinál:** GitHub milestone-ok importálása feature-ként egy projekthez. Kapcsolódó issue-k todo-kként lesznek linkelve.  
**Mikor használd:** Amikor meglévő GitHub milestone-okat szeretnél importálni InTracker feature-ként.  
**Paraméterek:** `projectId` (kötelező), `state` (alapértelmezett: open)

### `mcp_analyze_codebase`
**Mit csinál:** Meglévő codebase elemzése és kezdeti projekt struktúra javaslat. Azonosítja a modulokat, komponenseket és javasol hierarchikus struktúrát.  
**Mikor használd:** Meglévő projekteknél, amikor InTracker-be szeretnéd beállítani a projektet.  
**Paraméterek:** `projectId`, `projectPath` (kötelező Docker környezetben)  
**⚠️ FONTOS:** Docker környezetben a `projectPath` paraméter **kötelező**, mert az MCP szerver nem fér hozzá a lokális fájlrendszerhez.

---

## 🔑 Fontos Megjegyzések

### Nyelv Követelmény
- **Ha a team nyelv beállítva van, MINDIG használd azt a nyelvet** todo-k, feature-ök és idea-k létrehozásánál!
- Magyar team (hu) → magyarul kell létrehozni a tartalmat
- Angol team (en) vagy nincs beállítva → angolul kell létrehozni

### Workflow
- **MINDEN session elején KÖTELEZŐ:** `mcp_enforce_workflow` hívása
- Ez automatikusan azonosítja a projektet, betölti a resume context-et és cursor rules-t

### Todo Státuszok
- `new` → `in_progress` → `done`
- Feature szinten: `new` → `in_progress` → `done` → `tested` → `merged`

### Optimistic Locking
- `mcp_update_todo_status` és `mcp_link_todo_to_feature` használ `expectedVersion` paramétert
- Mindig használd az előző olvasásból kapott version számot!

---

**Összesen: 52 MCP Tool**
