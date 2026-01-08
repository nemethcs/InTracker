# Team Context Design for MCP Tools

## Jelenlegi helyzet

### Adatmodell
- **Project**: Nincs `team_id` mező, csak `UserProject` kapcsolat (user-alapú hozzáférés)
- **Idea**: Nincs `team_id` mező, nincs team kapcsolat
- **Team**: Létezik, de nincs kapcsolat projektekkel vagy ötletekkel
- **User**: Több team tagja lehet (`TeamMember` kapcsolaton keresztül)

### MCP Toolok jelenlegi működése
- **Project tools**: User-alapúak (`UserProject` kapcsolaton keresztül)
- **Idea tools**: Nincs team kontextus
- **Project identification**: Path, GitHub URL, vagy név alapján azonosít
- **Resume context**: Project-alapú, user filtering opcionális

## Probléma

Ha egy user több team tagja is lehet, és a team-eknek több projektje/ötlete is lehet, akkor:
1. **Hogyan azonosítjuk, hogy melyik team kontextusban dolgozunk?**
2. **Hogyan szűrjük a projekteket/ötleteket team alapján?**
3. **Hogyan viselkedjenek az MCP toolok, ha nincs explicit team kontextus?**

## Javasolt megoldások

### 1. Adatmodell bővítése

#### Opció A: Egyszerű team_id hozzáadása (1 team per project/idea)
```python
# Project model
team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)

# Idea model  
team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
```

**Előnyök:**
- Egyszerű implementáció
- Gyors szűrés
- Egyértelmű ownership

**Hátrányok:**
- Egy projekt csak egy team-hez tartozhat
- Ha egy projekt több team-hez is tartozik, nem működik

#### Opció B: Junction táblák (many-to-many)
```python
class TeamProject(Base):
    team_id = Column(UUID, ForeignKey("teams.id"), primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"), primary_key=True)
    role = Column(String)  # owner, editor, viewer

class TeamIdea(Base):
    team_id = Column(UUID, ForeignKey("teams.id"), primary_key=True)
    idea_id = Column(UUID, ForeignKey("ideas.id"), primary_key=True)
```

**Előnyök:**
- Egy projekt/ötlet több team-hez is tartozhat
- Rugalmasabb

**Hátrányok:**
- Bonyolultabb implementáció
- Több join szükséges

#### Opció C: User-alapú marad, team filtering a user team membership alapján
- Nem változtatunk az adatmodellen
- A projektek továbbra is `UserProject` kapcsolaton keresztül vannak
- Az MCP toolok szűrnek team alapján: ha `teamId` van megadva, csak azok a projektek jelennek meg, ahol a user team tagja

**Előnyök:**
- Nincs adatmodell változás
- Backward compatible
- A user továbbra is közvetlenül hozzáférhet projektekhez

**Hátrányok:**
- Nem egyértelmű, hogy egy projekt melyik team-hez tartozik
- Ha egy user több team tagja, mindkét team projekteit látja

### 2. MCP Toolok frissítése

#### Javasolt megközelítés: **Opció C + opcionális team kontextus**

**Alapelv:**
- Az MCP toolok továbbra is működnek user-alapúan (backward compatible)
- Opcionális `teamId` paraméter hozzáadása a releváns toolokhoz
- Ha `teamId` nincs megadva, akkor minden projekt/ötlet látható, amit a user elérhet
- Ha `teamId` meg van adva, akkor csak azok a projektek/ötletek láthatók, ahol a user tagja a megadott team-nek

#### Módosítandó MCP Toolok:

1. **`mcp_list_projects`**
   - Új paraméter: `teamId` (opcionális)
   - Ha `teamId` van: csak azok a projektek, ahol a user tagja a team-nek
   - Ha nincs: minden projekt, amit a user elérhet

2. **`mcp_get_project_context`**
   - Nincs változás (projectId alapján működik)
   - De ellenőrizni kell, hogy a user hozzáfér-e a projekthez (team vagy UserProject alapján)

3. **`mcp_get_resume_context`**
   - Nincs változás (projectId alapján működik)

4. **`mcp_identify_project_by_path`**
   - Új paraméter: `teamId` (opcionális)
   - Ha `teamId` van: csak azok a projektek jöhetnek szóba, ahol a user tagja a team-nek
   - Ha több match van, prioritizáljuk a team projekteket

5. **`mcp_create_project`**
   - Új paraméter: `teamId` (opcionális)
   - Ha `teamId` van: a projekt automatikusan hozzáadódik a team-hez (ha TeamProject tábla van)
   - Vagy: csak a user létrehozza, és a team tagok hozzáférnek (ha UserProject marad)

6. **`mcp_list_ideas`**
   - Új paraméter: `teamId` (opcionális)
   - Ha `teamId` van: csak azok az ötletek, ahol a user tagja a team-nek
   - Ha nincs: minden ötlet, amit a user elérhet

7. **`mcp_create_idea`**
   - Új paraméter: `teamId` (opcionális)
   - Ha `teamId` van: az ötlet automatikusan hozzáadódik a team-hez

#### Hozzáférés ellenőrzés logika:

```python
def check_user_team_project_access(db, user_id, project_id, team_id=None):
    """Check if user has access to project via team or UserProject."""
    user = db.query(User).filter(User.id == user_id).first()
    
    # Admins have access to all projects
    if user.role == "admin":
        return True
    
    # Check UserProject relationship
    user_project = db.query(UserProject).filter(
        UserProject.user_id == user_id,
        UserProject.project_id == project_id
    ).first()
    
    if user_project:
        # If team_id is specified, check if user is member of that team
        if team_id:
            team_member = db.query(TeamMember).filter(
                TeamMember.user_id == user_id,
                TeamMember.team_id == team_id
            ).first()
            if team_member:
                return True
        else:
            # No team filter, user has access via UserProject
            return True
    
    # Check if user is member of any team that has access to this project
    # (if TeamProject junction table exists)
    if team_id:
        team_project = db.query(TeamProject).filter(
            TeamProject.team_id == team_id,
            TeamProject.project_id == project_id
        ).first()
        if team_project:
            team_member = db.query(TeamMember).filter(
                TeamMember.user_id == user_id,
                TeamMember.team_id == team_id
            ).first()
            if team_member:
                return True
    
    return False
```

## Implementációs lépések

### Fázis 1: Adatmodell döntés
1. Döntés: Opció A, B, vagy C?
2. Ha A vagy B: migráció létrehozása
3. Ha C: nincs adatmodell változás

### Fázis 2: Service réteg frissítése
1. `ProjectService.get_user_projects()` - hozzáadni `team_id` paramétert
2. `IdeaService.list_ideas()` - hozzáadni `team_id` paramétert
3. Hozzáférés ellenőrzés frissítése team kontextussal

### Fázis 3: MCP Toolok frissítése
1. Tool definíciók frissítése (új `teamId` paraméterek)
2. Handler függvények frissítése
3. Hozzáférés ellenőrzés implementálása

### Fázis 4: Dokumentáció
1. MCP tool dokumentáció frissítése
2. Cursor rules frissítése team kontextussal

## Ajánlás

**Opció C (User-alapú marad + opcionális team filtering)** ajánlott, mert:
- Backward compatible
- Nincs adatmodell változás
- Rugalmas: a user továbbra is közvetlenül hozzáférhet projektekhez
- Az MCP toolok opcionálisan szűrhetnek team alapján
- Ha később szükség van rá, könnyen hozzáadhatunk TeamProject táblát

**Team kontextus kezelése:**
- Ha a user csak egy team tagja, automatikusan az a team kontextus
- Ha több team tagja, az MCP tooloknak explicit `teamId` paramétert kell megadni
- A Cursor rules-ban lehet konfigurálni az alapértelmezett team-t
