# InTracker - Cursor AI előtét rendszer működése

## 1. Rendszer működése - AI-first megközelítés

Az InTracker egy **teljesen AI-driven rendszer**, ahol a Cursor (AI) kezeli az összes műveletet, és a felhasználó csak **nézőként** követi a folyamatokat. Nincs felhasználói interakció a rendszerrel - minden a Cursor-on keresztül történik.

### 1.1. Dashboard nézet (csak olvasható)

**Mit lát a felhasználó (csak megtekintés):**

```
┌─────────────────────────────────────────────────────────────┐
│  InTracker                          [Profil] [Beállítások]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Gyors váltás:                                        │  │
│  │  [Projekt 1] [Projekt 2] [Projekt 3] [+ Új projekt]  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Aktív projektek (3)                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ E-commerce   │  │ Blog Engine  │  │ API Gateway  │      │
│  │ React/TS     │  │ Next.js      │  │ Node.js      │      │
│  │              │  │              │  │              │      │
│  │ Last: Auth   │  │ Last: SEO    │  │ Last: Rate   │      │
│  │ Now: Cart    │  │ Now: CMS     │  │ Now: Auth    │      │
│  │              │  │              │  │              │      │
│  │ [Megnyitás]  │  │ [Megnyitás]  │  │ [Megnyitás]  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Ötletek (5)                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Mobile App  │  │ Analytics    │  │ ...          │      │
│  │ [Projektté] │  │ [Projektté]  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Információk (csak olvasható):**
- **Projekt kártyák:** Minden kártya mutatja a legfontosabb információkat
  - Projekt neve és technológia
  - **Last:** Mit csináltunk legutóbb (session summary rövidítve)
  - **Now:** Mi a következő 1-3 lépés
  - **Aktív funkciók:** Jelenleg fejlesztés alatt lévő funkciók
- **Ötletek tábla:** Nem konvertált ötletek (AI automatikusan konvertálja projektté)
- **Megjegyzés:** A felhasználó NEM kattinthat, NEM szerkeszthet - csak nézi az információkat

---

### 1.2. Projekt nézet (csak olvasható)

**Mit lát a felhasználó (automatikus betöltés Cursor által):**

```
┌─────────────────────────────────────────────────────────────┐
│  E-commerce Platform                    [Csak olvasható nézet] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Resume Context ─────────────────────────────────────┐  │
│  │                                                       │  │
│  │  📍 Last (2 napja):                                   │  │
│  │  Authentication modul implementálva. JWT token        │  │
│  │  kezelés, login/logout flow. 3 todo kész.            │  │
│  │                                                       │  │
│  │  🎯 Now (következő 1-3 lépés):                        │  │
│  │  • Shopping cart komponens létrehozása                │  │
│  │  • Product list API integráció                        │  │
│  │  • Cart state management (Zustand)                    │  │
│  │                                                       │  │
│  │  ⚠️  Blockers:                                         │  │
│  │  • Product API endpoint még nincs kész (backend)     │  │
│  │                                                       │  │
│  │  📋 Constraints:                                      │  │
│  │  • TypeScript strict mode                            │  │
│  │  • Nem használhatunk Redux-ot, csak Zustand          │  │
│  │  • Minden komponens function component                │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Projekt struktúra                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📁 Authentication [✓ Done]                          │  │
│  │    ├─ Login form [✓]                                 │  │
│  │    ├─ JWT handling [✓]                               │  │
│  │    └─ Protected routes [✓]                            │  │
│  │                                                       │  │
│  │  📁 Shopping Cart [🔄 In Progress]                   │  │
│  │    ├─ Cart component [🔄]                            │  │
│  │    ├─ Product list [📝 Todo]                         │  │
│  │    └─ State management [📝 Todo]                      │  │
│  │                                                       │  │
│  │  📁 Checkout [📝 Todo]                                │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Aktív feladatok (5)                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ☐ Cart component UI létrehozása          [2h] [🔄]  │  │
│  │  ☐ Product list API integráció            [3h] [📝]  │  │
│  │  ☐ Zustand store setup                   [1h] [📝]  │  │
│  │  ☐ Cart item add/remove logika            [2h] [📝]  │  │
│  │  ☐ Responsive design                      [2h] [📝]  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Kulcsfontosságú információk (csak olvasható):**
- **Resume Context panel:** Automatikusan frissül, hol tartunk, mi a következő, mi akadályoz
- **Projekt struktúra:** Hierarchikus fa, státuszokkal (✓ Done, 🔄 In Progress, 📝 Todo)
- **Aktív funkciók:** Jelenleg fejlesztés alatt lévő funkciók, hozzájuk tartozó todo-k
- **Aktív feladatok:** Következő todo-k, funkciókhoz csoportosítva
- **Megjegyzés:** Minden automatikusan frissül, amikor a Cursor dolgozik a projekten

---

### 1.3. Aktív munkamenet nézet (automatikus)

**Session automatikus indítás (Cursor által):**

Amikor a felhasználó Cursor-ban dolgozik egy projekten, a Cursor automatikusan:
1. Azonosítja az aktív projektet (working directory alapján)
2. Indít egy session-t (ha még nincs aktív)
3. Betölti a projekt kontextusát
4. Frissíti az InTracker UI-t

**Session közben (felhasználó csak nézi):**

```
┌─────────────────────────────────────────────────────────────┐
│  🔄 Aktív munkamenet: Shopping cart implementálása          │
│  ⏱️  1h 23m | Automatikus frissítés                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Session panel - jobb oldalon vagy alul]                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cél: Shopping cart komponens implementálása          │  │
│  │                                                       │  │
│  │  Elvégzett:                                          │  │
│  │  ✓ Cart component UI létrehozva                     │  │
│  │  ✓ Zustand store setup kész                         │  │
│  │                                                       │  │
│  │  Folyamatban:                                        │  │
│  │  🔄 Product list API integráció                       │  │
│  │                                                       │  │
│  │  Jegyzetek:                                          │  │
│  │  - API endpoint: /api/products                       │  │
│  │  - Backend még fejlesztés alatt                      │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  [Fő projekt nézet továbbra is látható]                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Session automatikus befejezése (Cursor által):**

Amikor a Cursor befejezi a munkát vagy a felhasználó elhagyja a projektet:

1. **Automatikus összefoglaló generálás (AI által):**
   - Mit csináltunk (completed todos)
   - Mit változtattunk (updated elements)
   - Melyik funkciók készültek el
   - Mi a következő lépés
   - Blokkoló tényezők

2. **Resume Context automatikus frissítés:**
   - Last szekció frissül az új session summary-vel
   - Now szekció frissül a következő lépésekkel
   - Blockers frissül, ha vannak új akadályok

3. **UI automatikus frissítés:**
   - Session panel frissül
   - Frissített Resume Context látható
   - Projekt struktúra frissül
   - Aktív funkciók státusza frissül

---

### 1.4. Projektváltás - Automatikus kontextus visszaállítás

**Példa: 3 projektről váltás**

**1. E-commerce projekt (jelenleg aktív):**
- Last: Shopping cart implementálva
- Now: Checkout flow
- Aktív funkció: "Shopping Cart" (3 todo, 2 kész)
- Blocker: Payment gateway integráció várható

**2. Blog Engine projekt (2 napja inaktív):**
- Last: SEO optimalizálás elkezdve
- Now: CMS admin panel fejlesztése
- Aktív funkció: "SEO Optimization" (5 todo, 2 kész)
- Blocker: Nincs

**3. API Gateway projekt (1 hete inaktív):**
- Last: Rate limiting implementálva
- Now: Authentication middleware
- Aktív funkció: "Rate Limiting" (4 todo, 4 kész - done)
- Blocker: Nincs

**Automatikus váltás folyamata (Cursor által):**

1. Felhasználó Cursor-ban vált projektet (cd másik könyvtárba)
2. **Cursor automatikusan (1-2 másodperc alatt):**
   - Azonosítja az új projektet
   - MCP-n keresztül betölti a Resume Context-et
   - Aktív funkciókat és todo-kat lekérdezi
   - Projekt struktúrát betölti
3. **InTracker UI automatikusan frissül:**
   - Új projekt nézet megjelenik
   - Resume Context panel frissül
   - Aktív funkciók és todo-k megjelennek
   - Felhasználó azonnal látja: hol tartottunk, mi a következő, van-e blocker

**Nincs kontextusvesztés - minden automatikus!**

---

### 1.5. Ötlet → Projekt automatikus konverzió

**Ötlet nézet (csak olvasható):**

```
┌─────────────────────────────────────────────────────────────┐
│  Ötlet: Mobile App                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Leírás:                                                     │
│  React Native mobilalkalmazás a fő webapp kiegészítésére.    │
│  Offline támogatás, push notifications.                      │
│                                                              │
│  Címkék: [mobile] [react-native] [offline]                  │
│                                                              │
│  Státusz: Várakozás AI konverzióra                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Automatikus konverzió folyamata (Cursor/AI által):**

1. Felhasználó megemlíti az ötletet Cursor-ban vagy létrehoz egy új könyvtárat
2. **Cursor automatikusan:**
   - MCP-n keresztül ellenőrzi, van-e már ilyen ötlet
   - Ha nincs, létrehozza az ötletet
   - AI dönt: konvertálja-e projektté (template alapján)
3. **Template automatikus alkalmazása:**
   - AI kiválasztja a megfelelő template-t (pl. Mobile App template)
   - Automatikusan létrehozza:
     - Authentication modul
     - Offline storage modul
     - Push notifications modul
     - Navigation modul
     - stb.
4. **Projekt automatikusan létrejön:**
   - Ötlet → Projekt konvertálva
   - Alap struktúra kész
   - Resume Context inicializálva
   - InTracker UI automatikusan frissül
   - Készen áll a munkára

---

### 1.6. Dokumentáció nézet (csak olvasható)

**Dokumentum nézet (automatikus frissítés):**

```
┌─────────────────────────────────────────────────────────────┐
│  Dokumentumok - E-commerce Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Típus szerint:                                              │
│  [Összes] [Architecture] [ADR] [Domain] [Constraints]        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📐 Architecture Snapshot                              │  │
│  │  Utolsó frissítés: 3 napja (AI által)                 │  │
│  │  [Csak olvasható]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📋 ADR-001: State Management választás               │  │
│  │  Döntés: Zustand használata Redux helyett            │  │
│  │  [Csak olvasható]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ⚠️  Constraints                                       │  │
│  │  - TypeScript strict mode                            │  │
│  │  - Nincs Redux                                        │  │
│  │  [Csak olvasható]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  🤖 AI Instructions                                    │  │
│  │  Projekt-specifikus AI munkaszabályok                 │  │
│  │  [Csak olvasható]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Dokumentum kezelés (AI által):**

- Markdown formátum
- Projekt elemekhez hivatkozhatók
- Verziókezelés
- AI automatikusan olvassa és frissíti (MCP-n keresztül)
- Felhasználó csak olvashatja

---

## 2. MCP (Model Context Protocol) integráció

### 2.1. MCP Server működése

Az MCP Server lehetővé teszi, hogy az AI (pl. Cursor) közvetlenül hozzáférjen az InTracker adataihoz és műveleteket hajtson végre.

**Kapcsolat létrejötte:**

```
Cursor (AI)  ←→  MCP Server  ←→  InTracker Backend  ←→  Database
```

Amikor a felhasználó Cursor-ban dolgozik egy projekten:
1. Cursor automatikusan csatlakozik az MCP Server-hez
2. MCP Server azonosítja az aktív projektet (working directory alapján)
3. AI automatikusan hozzáfér a projekt teljes kontextusához
4. AI automatikusan indít egy session-t (ha még nincs aktív)
5. Minden változás automatikusan szinkronizálódik az InTracker-be

---

### 2.2. MCP Tools - AI által használható funkciók

#### 2.2.1. Projekt kontextus lekérdezés

**Tool: `mcp_get_project_context`**

**Használati példa (AI szemszögéből):**

```
Felhasználó: "Implementáld a shopping cart komponenst"

AI belső folyamat:
1. MCP: mcp_get_project_context(projectId: "ecommerce-123")
   → Visszaadja:
     - Projekt struktúrát
     - Aktív todos
     - Resume Context
     - Constraints
     - Cursor instructions

2. AI látja:
   - "Shopping Cart" modul már létezik
   - 3 todo van: Cart component UI, Product list API, State management
   - Constraint: Zustand használata, TypeScript strict mode
   - Cursor instruction: "Mindig function components, hooks használata"

3. AI implementálja a komponenst a kontextus alapján
```

**Visszaadott adatok:**
```json
{
  "project": {
    "id": "ecommerce-123",
    "name": "E-commerce Platform",
    "status": "active"
  },
  "resume_context": {
    "last": { ... },
    "now": { ... },
    "blockers": [ ... ],
    "constraints": [ ... ],
    "cursor_instructions": "..."
  },
  "structure": [ ... ],
  "active_todos": [ ... ],
  "documents": [ ... ]
}
```

#### 2.2.2. Feature/Funkció kezelés

**Tool: `mcp_create_feature`**

**Példa - Funkció létrehozása több todo-val:**
```
Felhasználó: "Implementáld a shopping cart funkciót"

AI:
1. MCP: mcp_create_feature(
     projectId: "ecommerce-123",
     feature: {
       name: "Shopping Cart",
       description: "Teljes shopping cart funkcionalitás",
       related_elements: ["cart-module", "product-list", "state-management"]
     }
   )
2. Feature létrejön, majd AI létrehozza a hozzá tartozó todo-kat több helyen:
   - Cart component UI (cart-module elemben)
   - Product list API integráció (product-list elemben)
   - State management (state-management elemben)
   - Cart item add/remove (cart-module elemben)
   - Responsive design (cart-module elemben)
3. Minden todo hozzárendelve a "Shopping Cart" funkcióhoz
4. Felhasználó látja a funkciót és az összes hozzá tartozó todo-t
```

**Tool: `mcp_get_feature_todos`**

**Példa:**
```
AI: "Nézd meg mi van még hátra a Shopping Cart funkcióból"

1. MCP: mcp_get_feature_todos(featureId: "feature-shopping-cart-123")
2. Visszaadja az összes todo-t, ami ehhez a funkcióhoz tartozik
3. AI látja a teljes képet: melyik elemben milyen todo-k vannak
```

#### 2.2.3. Todo kezelés

**Tool: `mcp_create_todo`**

**Példa:**
```
AI automatikusan létrehozza a todo-kat egy funkció fejlesztésekor:

1. MCP: mcp_create_todo(
     elementId: "cart-module-456",
     featureId: "feature-shopping-cart-123", // Funkcióhoz kapcsolva
     todo: {
       title: "Add error handling to cart",
       description: "Handle API errors, network failures",
       estimated_effort: 2
     }
   )
2. Todo létrejön az InTracker-ben, funkcióhoz kapcsolva
3. Felhasználó látja az új todo-t a projekt nézetben, funkció szerint csoportosítva
```

**Tool: `mcp_update_todo_status`**

**Példa - Automatikus frissítés:**
```
AI implementál egy todo-t:
1. Kód kész
2. MCP: mcp_update_todo_status(
     todoId: "todo-789",
     status: "done"
   )
3. Todo automatikusan "done" státuszú lesz
4. Feature státusza automatikusan frissül (hány todo kész/hátra)
5. Projekt struktúra frissül
6. InTracker UI automatikusan frissül (felhasználó látja a változást)
```

**Tool: `mcp_list_todos`**

**Példa:**
```
AI automatikusan lekérdezi a todo-kat:

1. MCP: mcp_list_todos(
     projectId: "ecommerce-123", 
     filters: { 
       status: "todo",
       featureId: "feature-shopping-cart-123" // Opcionális: funkció szerint
     }
   )
2. Visszaadja az összes aktív todo-t (funkció szerint csoportosítva)
3. AI látja a teljes képet: melyik funkcióban milyen todo-k vannak
```

**Tool: `mcp_list_features`**

**Példa:**
```
AI: "Melyik funkciók vannak fejlesztés alatt?"

1. MCP: mcp_list_features(
     projectId: "ecommerce-123",
     filters: { status: "in_progress" }
   )
2. Visszaadja az összes aktív funkciót és a hozzájuk tartozó todo-kat
3. AI látja: "Shopping Cart" funkció - 5 todo, 2 kész, 3 hátra
```

#### 2.2.4. Dokumentáció olvasása

**Tool: `mcp_read_document`**

**Példa:**
```
AI: "Nézzük meg az architektúrát"

1. MCP: mcp_read_document(documentId: "arch-snapshot-001")
2. Visszaadja a teljes architecture snapshot-ot
3. AI tudja, hogyan kell implementálni a feature-t az architektúra szerint
```

**Tool: `mcp_get_documents_by_type`**

**Példa:**
```
AI: "Mik a constraints ezen a projekten?"

1. MCP: mcp_get_documents_by_type(
     projectId: "ecommerce-123",
     type: "constraints"
   )
2. Visszaadja az összes constraint dokumentumot
3. AI betartja a szabályokat implementáláskor
```

**Tool: `mcp_search_documents`**

**Példa:**
```
AI: "Keress információt a state management-ről"

1. MCP: mcp_search_documents(
     projectId: "ecommerce-123",
     query: "state management"
   )
2. Visszaadja a releváns dokumentumokat (ADR-001, Architecture snapshot)
3. AI megtudja, hogy Zustand-ot kell használni
```

#### 2.2.5. Session kezelés

**Tool: `mcp_start_session`**

**Példa - Automatikus session indítás:**
```
Amikor a felhasználó Cursor-ban dolgozik egy projekten:

AI automatikusan:
1. MCP: mcp_start_session(
     projectId: "ecommerce-123",
     goal: "Shopping Cart funkció implementálása",
     featureIds: ["feature-shopping-cart-123"] // Melyik funkciókra fókuszál
   )
2. Session létrejön
3. InTracker UI-ban automatikusan megjelenik a session panel
4. Felhasználó látja az aktív munkamenetet
```

**Tool: `mcp_update_session`**

**Példa - Automatikus frissítés:**
```
AI implementál közben, automatikusan frissíti:

1. Todo kész → MCP: mcp_update_session(
     sessionId: "session-456",
     updates: {
       completed_todos: ["todo-789"],
       completed_features: ["feature-shopping-cart-123"], // Ha minden todo kész
       notes: "Cart component kész, Zustand store működik"
     }
   )
2. Session panel automatikusan frissül
3. Feature státusza frissül (pl. "Shopping Cart" - 5/5 todo kész)
4. Felhasználó látja a változást valós időben
```

**Tool: `mcp_end_session`**

**Példa - Automatikus befejezés:**
```
Amikor a felhasználó elhagyja a projektet vagy a Cursor befejezi a munkát:

AI automatikusan:
1. MCP: mcp_end_session(sessionId: "session-456")
2. Automatikus summary generálás:
   - Mit csináltunk
   - Melyik funkciók készültek el (vagy részben)
   - Melyik todo-k készültek el
   - Mi a következő lépés
   - Melyik funkciókban van még munka
3. Resume Context automatikusan frissül
4. Session panel frissül (nem tűnik el, csak archiválódik)
5. Felhasználó látja a summary-t
```

#### 2.2.6. GitHub integráció

**Tool: `mcp_link_element_to_issue`**

**Példa:**
```
AI: "Hozzunk létre egy GitHub issue-t a checkout modulhoz"

1. MCP: mcp_link_element_to_issue(
     elementId: "checkout-modul-123",
     issueNumber: 42
   )
2. Element és GitHub issue összekapcsolódik
3. Kétirányú szinkronizáció aktív
```

**Tool: `mcp_link_todo_to_pr`**

**Példa:**
```
Felhasználó PR-t nyit:
1. AI észleli a PR-t
2. MCP: mcp_link_todo_to_pr(
     todoId: "todo-789",
     prNumber: 15
   )
3. PR merge → Todo automatikusan "done"
```

**Tool: `mcp_get_github_issue`**

**Példa:**
```
AI: "Nézzük meg mi van a GitHub issue-ban"

1. MCP: mcp_get_github_issue(
     repo: "user/ecommerce",
     issueNumber: 42
   )
2. Visszaadja az issue részleteit
3. AI használhatja a kontextusban
```

---

### 2.3. MCP Resources - AI által elérhető erőforrások

Az MCP Resources lehetővé teszik, hogy az AI közvetlenül olvassa a projekt adatait anélkül, hogy explicit tool hívást kellene tennie.

#### 2.3.1. Projekt kontextus resource

**Resource: `project://{projectId}/context`**

```
AI automatikusan hozzáfér:
- Teljes projekt kontextus
- Resume Context
- Aktív todos
- Projekt struktúra
- Dokumentációk

Használat: Amikor a felhasználó egy projekten dolgozik,
az AI automatikusan betölti ezt a resource-t
```

#### 2.3.2. Resume Context resource

**Resource: `project://{projectId}/resume`**

```
AI látja:
- Last: Mit csináltunk legutóbb
- Now: Mi a következő lépés
- Blockers: Mi akadályoz
- Constraints: Milyen szabályokat kell követni
- Cursor instructions: Hogyan dolgozzon az AI

Használat: Gyors kontextus visszaállítás projektről projektre
```

#### 2.3.3. Dokumentum resource

**Resource: `document://{documentId}`**

```
AI közvetlenül olvashatja:
- Architecture snapshots
- ADR-ek
- Constraints
- AI instructions
- Domain fogalomtár

Használat: Amikor az AI implementál, automatikusan
betöltődnek a releváns dokumentumok
```

---

### 2.4. Konkrét AI használati esetek

#### 2.4.1. Eset 1: Új funkció implementálása (több todo, több helyen)

**Felhasználó:** "Implementáld a user profile funkciót"

**AI folyamat:**
1. **Kontextus betöltés (automatikus):**
   - MCP: `mcp_get_project_context(projectId)`
   - Resource: `project://{id}/context` automatikusan betöltve

2. **Dokumentáció olvasás (automatikus):**
   - MCP: `mcp_get_documents_by_type(type: "architecture")`
   - MCP: `mcp_get_documents_by_type(type: "constraints")`
   - AI megtudja: React, TypeScript, Zustand, function components

3. **Funkció létrehozása:**
   - MCP: `mcp_create_feature()` - "User Profile" funkció
   - AI azonosítja, hogy ez több modult érint:
     - User Profile komponens (frontend)
     - User API endpoint (backend)
     - User service (backend)
     - Form validation (frontend)

4. **Todo-k létrehozása több helyen (automatikus):**
   - MCP: `mcp_create_todo()` - "User Profile komponens" (frontend modul, featureId: "user-profile")
   - MCP: `mcp_create_todo()` - "User API endpoint" (backend modul, featureId: "user-profile")
   - MCP: `mcp_create_todo()` - "User service" (backend modul, featureId: "user-profile")
   - MCP: `mcp_create_todo()` - "Form validation" (frontend modul, featureId: "user-profile")
   - Minden todo ugyanahhoz a funkcióhoz tartozik

5. **Session automatikus indítás:**
   - MCP: `mcp_start_session()` - "User Profile funkció implementálása"
   - Feature ID hozzárendelve a session-hez

6. **Implementálás (automatikus):**
   - AI implementálja a todo-kat sorrendben
   - Közben automatikusan frissíti a todo-k státuszát
   - MCP: `mcp_update_todo_status()` - minden todo-nál

7. **Session automatikus frissítés:**
   - MCP: `mcp_update_session()` - completed todos, completed features
   - Feature státusza frissül: "User Profile" - 4/4 todo kész

8. **Session automatikus befejezés:**
   - MCP: `mcp_end_session()` - summary generálás
   - Resume Context frissül

**Eredmény:**
- Funkció implementálva (több modulban, több todo)
- Minden todo funkcióhoz kapcsolva
- Projekt struktúra naprakész
- Dokumentáció követve
- Felhasználó látja: "User Profile" funkció - 4/4 todo kész ✓

#### 2.4.2. Eset 2: Projektváltás után visszatérés (automatikus)

**Felhasználó:** 2 hét után visszatér egy projekthez (cd másik könyvtárba)

**AI folyamat (teljesen automatikus):**
1. **Projekt automatikus azonosítás:**
   - Cursor észleli a working directory változást
   - MCP Server automatikusan azonosítja a projektet

2. **Resume Context automatikus betöltés:**
   - Resource: `project://{id}/resume` automatikusan betöltve
   - AI látja:
     - Last: "Authentication modul kész, Shopping Cart funkció elkezdve"
     - Now: "Shopping Cart funkció befejezése - 3/5 todo kész"
     - Aktív funkciók: "Shopping Cart" (3/5 todo), "Checkout" (0/4 todo)
     - Blockers: "Product API endpoint hiányzik"

3. **Aktív funkciók és todo-k automatikus lekérdezés:**
   - MCP: `mcp_list_features(projectId, status: "in_progress")`
   - MCP: `mcp_get_feature_todos(featureId: "shopping-cart")`
   - AI látja:
     - "Shopping Cart" funkció: 3/5 todo kész
     - Melyik todo-k vannak még hátra (melyik modulban)
     - Melyik elemekben kell dolgozni

4. **Session automatikus indítás:**
   - MCP: `mcp_start_session()` - "Shopping Cart funkció folytatása"
   - Feature ID hozzárendelve

5. **Kontextus automatikus visszaállítás:**
   - AI érti, hol tartottunk
   - Tudja, melyik funkciókban van még munka
   - Tudja, melyik todo-kat kell befejezni
   - Ismeri a blokkoló tényezőket

6. **Folytatás (automatikus):**
   - AI azonnal folytatja a munkát
   - Nem kell újra elmagyarázni a projektet
   - Felhasználó csak nézi, ahogy az AI dolgozik

**Eredmény:**
- 1-2 másodperc alatt visszarázódás (teljesen automatikus)
- Nincs kontextusvesztés
- AI azonnal produktív
- Felhasználó látja: melyik funkciókban van még munka, hol tartunk

#### 2.4.3. Eset 3: GitHub issue kezelés

**Felhasználó:** "Nézd meg a #42 issue-t és implementáld"

**AI folyamat:**
1. **Issue lekérdezés:**
   - MCP: `mcp_get_github_issue(repo, 42)`
   - AI látja az issue részleteit

2. **Projekt kontextus:**
   - MCP: `mcp_get_project_context(projectId)`
   - AI érti, hogyan illeszkedik a projektbe

3. **Element linkelés:**
   - Ha még nincs, létrehoz egy projekt elemet
   - MCP: `mcp_link_element_to_issue(elementId, 42)`

4. **Todo-k létrehozása:**
   - Issue alapján todo-k létrehozása
   - MCP: `mcp_create_todo()` - minden lépéshez

5. **Implementálás:**
   - AI implementálja az issue követelményeit
   - Todo-k frissítése

6. **PR linkelés:**
   - PR létrehozásakor
   - MCP: `mcp_link_todo_to_pr(todoId, prNumber)`

**Eredmény:**
- Issue → Projekt elem → Todo → PR teljes kapcsolat
- Kétirányú szinkronizáció
- Minden összekapcsolva

#### 2.4.4. Eset 4: Dokumentáció alapú implementálás

**Felhasználó:** "Implementáld a payment flow-t"

**AI folyamat:**
1. **Dokumentáció keresés:**
   - MCP: `mcp_search_documents(query: "payment")`
   - MCP: `mcp_get_documents_by_type(type: "architecture")`

2. **Constraints ellenőrzés:**
   - MCP: `mcp_get_documents_by_type(type: "constraints")`
   - AI megtudja: "Nem használhatunk külső payment gateway-t, csak saját megoldás"

3. **ADR olvasás:**
   - MCP: `mcp_search_documents(query: "payment ADR")`
   - AI megtudja a döntéseket

4. **AI instructions:**
   - Resource: `document://ai-instructions-001`
   - AI megtudja a projekt-specifikus szabályokat

5. **Implementálás:**
   - AI implementálja a dokumentáció alapján
   - Betartja a constraints-eket
   - Követi az ADR-eket

**Eredmény:**
- Dokumentáció-alapú implementálás
- Nincs konfliktus a projekt szabályaival
- Konzisztens kód

---

### 2.5. Teljes automatizált workflow (felhasználó csak néző)

**Tipikus workflow (teljesen automatikus):**

```
1. Felhasználó Cursor-ban dolgozik egy projekten (cd projekt-könyvtár)
   ↓
2. Cursor automatikusan csatlakozik MCP Server-hez
   ↓
3. AI automatikusan:
   - Azonosítja a projektet (working directory alapján)
   - Betölti a Resume Context-et (MCP Resource)
   - Indít egy session-t (ha még nincs aktív)
   ↓
4. Felhasználó: "Implementáld a shopping cart funkciót"
   ↓
5. AI automatikusan:
   - Lekérdezi a teljes projekt kontextust
   - Olvassa a releváns dokumentációkat
   - Ellenőrzi a constraints-eket
   - Létrehozza a funkciót (mcp_create_feature)
   - Létrehozza a szükséges todo-kat több helyen (mcp_create_todo)
   - Minden todo-t funkcióhoz kapcsol
   - Implementálja a feature-t (több modulban, több todo)
   - Automatikusan frissíti a todo-k státuszát
   - Automatikusan frissíti a funkció státuszát
   ↓
6. Felhasználó elhagyja a projektet vagy befejezi a munkát
   ↓
7. AI automatikusan:
   - Befejezi a session-t (mcp_end_session)
   - Generál session summary-t
   - Frissíti a Resume Context-et
   - Archiválja a session-t
   ↓
8. InTracker UI automatikusan frissül
   - Felhasználó látja: melyik funkciók készültek el
   - Felhasználó látja: hol tartunk, mi a következő
   ↓
9. Következő belépéskor (cd ugyanabba a könyvtárba):
   - AI automatikusan betölti a Resume Context-et
   - AI azonnal látja, hol tartottunk
   - AI azonnal folytatja a munkát
```

**Kulcs előnyök:**
- ✅ **Teljes automatizáció:** Felhasználó csak nézi, minden automatikus
- ✅ **Funkció-alapú csoportosítás:** Todo-k funkciókhoz kapcsolva, több helyen
- ✅ **AI nem találgat:** Valós projektállapotból dolgozik
- ✅ **Kontextus megmarad:** Projektről projektre automatikus visszaállítás
- ✅ **Dokumentáció automatikus:** Releváns infók automatikusan betöltődnek
- ✅ **Todo-k automatikus szinkronizáció:** Minden változás valós időben
- ✅ **Funkció követés:** Látható, melyik funkciókban van még munka
- ✅ **GitHub integráció:** Zökkenőmentes, automatikus

---

## 3. Összefoglalás

### 3.1. Felhasználói élmény (csak néző)

- **Csak olvasható nézet:** Felhasználó NEM szerkeszthet, NEM kattinthat - csak nézi
- **Automatikus frissítés:** Minden változás valós időben látható
- **Funkció-alapú nézet:** Látható, melyik funkciókban van még munka
- **Kontextus megmarad:** Resume Context mindig naprakész, automatikusan
- **Strukturált nézet:** Hierarchikus projekt struktúra, funkciók szerint csoportosítva
- **Session követés:** Aktív munkamenetek automatikusan követve
- **Dokumentáció központi:** Minden egy helyen, AI által automatikusan olvasva

### 3.2. AI (MCP) lehetőségek

- **Teljes projekt kontextus:** AI mindig tudja, hol tartunk
- **Automatikus dokumentáció:** Releváns infók automatikusan betöltődnek
- **Funkció kezelés:** AI létrehozhat funkciókat, több todo-val több helyen
- **Todo kezelés:** AI létrehozhat és frissíthet todo-kat, funkciókhoz kapcsolva
- **Session kezelés:** AI automatikusan követi és összefoglalja a munkát
- **GitHub integráció:** Issue/PR kapcsolatok automatikus kezelése
- **Kontextus visszaállítás:** Projektről projektre automatikus, 1-2 másodperc
- **Teljes automatizáció:** Minden művelet AI által kezelve

### 3.3. Fő előnyök

1. **Teljes automatizáció:** Felhasználó csak nézi, minden AI által kezelve
2. **Funkció-alapú csoportosítás:** Egy funkció több todo-t tartalmaz több helyen
3. **Nincs kontextusvesztés:** Resume Context mindig naprakész, automatikusan
4. **AI-val való együttműködés:** MCP integráció teljes automatizációt tesz lehetővé
5. **Strukturált gondolkodás:** Hierarchikus projekt struktúra, funkciók szerint
6. **Azonnali projektváltás:** 1-2 másodperc alatt automatikus visszarázódás
7. **Dokumentáció él:** AI automatikusan használja és frissíti
8. **GitHub integráció:** Kétirányú szinkronizáció, automatikus

### 3.4. Funkció-alapú fejlesztés példa

**Példa: "Shopping Cart" funkció fejlesztése**

```
Funkció: Shopping Cart
├─ Frontend modul
│  ├─ Todo: Cart component UI [✓ Done]
│  ├─ Todo: Cart item add/remove [✓ Done]
│  └─ Todo: Responsive design [🔄 In Progress]
│
├─ Backend modul
│  ├─ Todo: Cart API endpoint [📝 Todo]
│  └─ Todo: Cart service [📝 Todo]
│
└─ State Management modul
   └─ Todo: Zustand store [✓ Done]

Státusz: 3/6 todo kész (50%)
```

**AI automatikusan:**
- Látja, hogy a funkció 3/6 todo kész
- Tudja, melyik modulban van még munka
- Automatikusan folytatja a fejlesztést
- Frissíti a funkció státuszát valós időben

---

Ez a dokumentum részletesen bemutatja, hogyan működik az InTracker **teljesen AI-driven rendszerként**, ahol a felhasználó csak néző, és minden a Cursor (AI) által automatikusan kezelve. A rendszer célja, hogy minimalizálja a kontextusvesztést és maximalizálja az AI automatizációt, miközben a funkciók több todo-t tartalmaznak több helyen a projektben.
