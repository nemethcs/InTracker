# Cursor Rules Rendszer - Általános Megoldás

## Áttekintés

Az InTracker egy **dinamikus, moduláris cursor rules generáló rendszert** használ, ami projekt-specifikus szabályokat generál a projekt konfigurációja alapján.

## Főbb Jellemzők

### 1. Moduláris Szekciók (Rules Sections)

A rules generálás **moduláris szekciókon** alapul, amik **feltételesen** kerülnek be a generált rules fájlba:

- **Core Workflow** - Mindig benne van (kötelező munkafolyamat)
- **Docker Setup** - Csak ha `docker` van a `technology_tags`-ben
- **MCP Server** - Csak ha `mcp` van a `technology_tags`-ben
- **Frontend** - Csak ha `react`, `vue`, `angular`, `svelte` vagy `frontend` van a `technology_tags`-ben
- **GitHub** - Csak ha a projektnek van `github_repo_url`-je
- **InTracker Integration** - Mindig benne van
- **User Interaction** - Mindig benne van

### 2. Dinamikus Tartalom Generálás

A generált rules **dinamikusan változik** a projekt konfigurációja alapján:

```python
# Példa: MCP szerver információ csak akkor jelenik meg, ha a projekt használ MCP-t
uses_mcp = project.technology_tags and "mcp" in [tag.lower() for tag in project.technology_tags]

if uses_mcp:
    # MCP szerver restart információk
    # MCP szerver újratöltés Cursor-ban
    # MCP szerver log ellenőrzés
```

### 3. Projekt-Specifikus Információk

A generált rules tartalmazza:
- **Projekt alapinformációk**: ID, státusz, címkék, technológiai stack
- **Cursor Instructions**: A projekt `cursor_instructions` mezője
- **Dinamikus szekciók**: Csak a releváns információk jelennek meg

## Hogyan Működik?

### Rules Generálás

1. **Projekt lekérdezése**: A `rules_generator.generate_rules(project)` meghívása
2. **Szekciók szűrése**: Minden szekció ellenőrzi, hogy be kell-e venni (`should_include()`)
3. **Tartalom összeállítása**: A releváns szekciók összefűzése
4. **Fájl írása**: Automatikusan mentés `.cursor/rules/intracker-project-rules.mdc`-be

### Automatikus Frissítés

**Amikor frissíteni kell a rules-t:**

1. **Projekt konfiguráció változás** (technology_tags, github_repo_url, stb.)
   - Automatikus: A `mcp_update_project` tool hívásakor
   - Manuális: `mcp_load_cursor_rules(projectId)` meghívása

2. **Új technológia hozzáadása**
   - Példa: `mcp_update_project(projectId, technologyTags=["python", "fastapi", "mcp"])`
   - Utána: `mcp_load_cursor_rules(projectId)` - újragenerálja a rules-t

3. **Cursor Instructions módosítása**
   - Példa: `mcp_update_project(projectId, cursorInstructions="Új instrukciók...")`
   - Utána: `mcp_load_cursor_rules(projectId)` - frissíti a rules-t

## Használat

### 1. Rules Generálás (első alkalommal)

```python
# MCP tool használata
mcp_load_cursor_rules(projectId)
```

Ez:
- Generálja a rules-t a projekt konfigurációja alapján
- Elmenti `.cursor/rules/intracker-project-rules.mdc`-be
- Visszaadja a tartalmat, ha nem tudja elmenteni

### 2. Rules Frissítés (amikor változás történik)

**Automatikus frissítés:**
- Amikor `technology_tags` változik → újragenerálja a rules-t
- Amikor `github_repo_url` hozzáadódik → GitHub szekció hozzáadódik
- Amikor `cursor_instructions` változik → frissíti a rules-t

**Manuális frissítés:**
```python
# Újragenerálás
mcp_load_cursor_rules(projectId)
```

### 3. Új Szekció Hozzáadása

Ha új technológia vagy workflow kerül be, új szekciót lehet hozzáadni:

```python
from src.services.rules_generator import rules_generator, RulesSection

# Új szekció hozzáadása
new_section = RulesSection(
    name="new_technology",
    content="### New Technology\n\n...",
    conditions={"technology_tags": "new_tech"}  # Csak ha "new_tech" van a technology_tags-ben
)

rules_generator.add_custom_section(new_section)
```

## Példák

### Példa 1: Projekt MCP-vel

**Projekt konfiguráció:**
```json
{
  "name": "InTracker",
  "technology_tags": ["python", "fastapi", "postgresql", "docker", "mcp"],
  "github_repo_url": "https://github.com/user/intracker"
}
```

**Generált rules tartalmazza:**
- ✅ Core Workflow
- ✅ Docker Setup (mert `docker` van a tags-ben)
- ✅ MCP Server (mert `mcp` van a tags-ben)
- ✅ GitHub (mert van `github_repo_url`)
- ✅ InTracker Integration
- ✅ User Interaction

### Példa 2: Projekt MCP nélkül

**Projekt konfiguráció:**
```json
{
  "name": "Simple Web App",
  "technology_tags": ["python", "django"],
  "github_repo_url": null
}
```

**Generált rules tartalmazza:**
- ✅ Core Workflow
- ❌ Docker Setup (nincs `docker` tag)
- ❌ MCP Server (nincs `mcp` tag)
- ❌ GitHub (nincs `github_repo_url`)
- ✅ InTracker Integration
- ✅ User Interaction

## Karbantartás

### Rules Verziózás

A generált rules tartalmazza a verziót:
```markdown
---
name: intracker-project-rules
description: Cursor AI instructions for ProjectName
version: 2026-01-07T08:14:29.168183
---
```

### Automatikus Frissítés Trigger-ek

**Jelenleg nincs automatikus trigger**, de lehet hozzáadni:

1. **Project Update Hook**: Amikor `mcp_update_project` hívódik, automatikusan újragenerálja a rules-t
2. **Technology Tags Change Detection**: Ha `technology_tags` változik, újragenerálja
3. **GitHub Repo Connection**: Amikor GitHub repo kapcsolódik, újragenerálja

## Jövőbeli Fejlesztések

### 1. Automatikus Frissítés

```python
# project_service.py-ben
async def update_project(...):
    # ... meglévő kód ...
    
    # Automatikus rules frissítés, ha releváns mezők változtak
    if technology_tags_changed or github_repo_url_changed or cursor_instructions_changed:
        await auto_regenerate_cursor_rules(project.id)
```

### 2. Rules Diff/Merge

- Összehasonlítani a régi és új rules-t
- Felhasználó által hozzáadott szekciók megőrzése
- Automatikus merge stratégia

### 3. Rules Template Rendszer

- Előre definiált template-ek különböző projekttípusokhoz
- Példa: `web-app`, `api-only`, `full-stack`, `library`

### 4. Rules Update MCP Tool

```python
# Új tool: mcp_update_cursor_rules_section
# Lehetővé teszi, hogy a Cursor frissítse egy adott szekciót
mcp_update_cursor_rules_section(projectId, sectionName, content)
```

## Összefoglalás

Az InTracker cursor rules rendszere:
- ✅ **Dinamikus**: Projekt-specifikus tartalom generálás
- ✅ **Moduláris**: Feltételes szekciók be/ki kapcsolása
- ✅ **Karbantartható**: Könnyen bővíthető új szekciókkal
- ✅ **Automatikus**: Fájl írása a projekt könyvtárába
- ✅ **Rugalmas**: Különböző projekttípusokhoz különböző rules

**Fontos**: A rules mindig a projekt aktuális konfigurációját tükrözi, így a Cursor mindig naprakész információkat kap.
