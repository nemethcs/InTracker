# InTracker - Cursor MCP Integráció Összefoglaló

## Vizsgált Követelmények

1. ✅ Az InTracker ötletek rögzítését és projektek rögzítését tudja
2. ❌ A projekteket 100% tudja kezelni a Cursor MCP-n keresztül
3. ⚠️ Ha a Cursor dolgozik egy projekten, akkor gyorsan fel tudja venni a fonalat
4. ❌ Projekt-specifikus Cursor rules a helyes munkarenddel
5. ⚠️ GitHub naprakészen tartása MCP-n keresztül

---

## Főbb Hiányosságok

### 1. Ideas (Ötletek) Kezelés ❌
**Probléma:** Nincs backend API és MCP tool az Ideas kezelésére.

**Hiányzik:**
- Backend: `idea_controller.py`, `idea_service.py`
- MCP Tools: `mcp_create_idea`, `mcp_list_ideas`, `mcp_convert_idea_to_project`

**Megoldás:** Implementálni kell az Ideas kezelést teljes körűen.

---

### 2. Projekt Kezelés MCP-n Keresztül ⚠️
**Probléma:** Csak lekérdezés van, nincs létrehozás/frissítés.

**Hiányzik:**
- `mcp_create_project` - Új projekt létrehozása
- `mcp_update_project` - Projekt frissítése
- `mcp_list_projects` - Projektek listázása
- `mcp_identify_project_by_path` - Automatikus projekt azonosítás

**Megoldás:** Bővíteni kell a projekt MCP tools-okat.

---

### 3. Automatikus Projekt Azonosítás ❌
**Probléma:** Nincs mechanizmus, ami automatikusan azonosítja a projektet working directory alapján.

**Hiányzik:**
- Working directory alapján projekt keresés
- GitHub repo URL alapján projekt keresés
- `.intracker/config.json` fájl támogatás

**Megoldás:** Implementálni kell az automatikus projekt azonosítást.

---

### 4. Cursor Rules Automatikus Betöltés ❌
**Probléma:** Nincs automatikus betöltés a projekt `cursor_instructions` mezőjéből.

**Hiányzik:**
- MCP Resource: `intracker://project/{id}/cursor-rules`
- Automatikus `.cursor/rules/intracker-project-rules.mdc` generálás
- Projekt-specifikus munkarend dokumentáció

**Megoldás:** Implementálni kell a cursor rules automatikus generálását és betöltését.

---

### 5. GitHub Teljes Szinkronizáció ⚠️
**Probléma:** Csak branch lekérdezés van, nincs teljes GitHub integráció.

**Hiányzik:**
- Issues kezelés (`mcp_link_element_to_issue`, `mcp_get_github_issue`)
- PR kezelés (`mcp_link_todo_to_pr`, `mcp_get_github_pr`)
- Automatikus szinkronizáció (webhook, periodikus sync)

**Megoldás:** Bővíteni kell a GitHub MCP tools-okat és implementálni az automatikus szinkronizációt.

---

## Prioritás Szerinti Implementációs Terv

### 🔴 Kritikus (Fázis 1)
1. **Ideas kezelés:**
   - Backend API implementálása
   - MCP Tools implementálása

2. **Projekt kezelés MCP-n:**
   - `mcp_create_project`
   - `mcp_update_project`
   - `mcp_list_projects`

### 🟡 Fontos (Fázis 2)
3. **Automatikus projekt azonosítás:**
   - Working directory alapján
   - GitHub repo alapján

4. **Cursor rules automatikus generálás:**
   - MCP Resource
   - Automatikus fájl generálás

### 🟢 Kiegészítő (Fázis 3)
5. **GitHub teljes szinkronizáció:**
   - Issues/PR kezelés
   - Automatikus szinkronizáció

---

## Részletes Elemzés

Lásd: `CURSOR-INTEGRATION-ANALYSIS.md` - Teljes elemzés minden hiányosságról.

---

**Státusz:** Elemzés kész, implementáció szükséges
**Dátum:** 2025-01-05
