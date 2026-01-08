# Team-Based Projects and Ideas Migration Plan

## Áttekintés

Ez a dokumentum leírja a nagyobb átalakítás tervét, ahol:
1. **Minden user (admin kivételével) kötelezően tagja kell legyen valamilyen csapatnak**
2. **A projektek és ötletek team szintűek lesznek** (nem user szintűek)

## Változások

### 1. Adatmodell Változások

#### Project Modell
- ✅ Hozzáadás: `team_id` mező (UUID, ForeignKey to teams.id, nullable=False, index=True)
- ❌ Eltávolítás: `UserProject` kapcsolat (vagy deprecate)
- ✅ Hozzáadás: `created_by` mező (opcionális, aki létrehozta, de a projekt a team-hez tartozik)

#### Idea Modell
- ✅ Hozzáadás: `team_id` mező (UUID, ForeignKey to teams.id, nullable=False, index=True)
- ❌ Eltávolítás: user ownership (ha volt)

#### User Modell
- ✅ Validáció: non-admin user-ek kötelezően team tagok (application-level vagy DB constraint)

### 2. Backend Változások

#### Service Réteg
- **ProjectService**: 
  - `create_project()`: `team_id` paraméter user_id helyett
  - `get_user_projects()` → `get_team_projects()` vagy `get_user_accessible_projects()`
  - `check_user_access()`: team membership alapján
  
- **IdeaService**:
  - `create_idea()`: `team_id` paraméter
  - `list_ideas()`: team filtering
  - `convert_idea_to_project()`: team_id használata

- **AuthService**:
  - `register()`: validáció, hogy user team tag legyen
  - Admin user creation: team tag lehet, de nem kötelező

#### Controller Réteg
- **ProjectController**: 
  - Minden endpoint team-based access control
  - `create_project`: team_id required
  - `list_projects`: team filtering
  
- **IdeaController**:
  - Minden endpoint team-based access control
  - `create_idea`: team_id required
  - `list_ideas`: team filtering

#### MCP Tools
- Minden project tool: team-based filtering
- Minden idea tool: team-based filtering
- User context automatikus (MCP API key-ből)

### 3. Frontend Változások

#### UI Komponensek
- **Project Creation**: Team selector required
- **Idea Creation**: Team selector required
- **Project List**: Team filter
- **Idea List**: Team filter
- **Project Detail**: Team information display

#### Services
- `projectService`: team_id használata
- `ideaService`: team_id használata
- State management: team context

### 4. Migráció

#### Adat Migráció
1. **Meglévő projektek**: 
   - Minden projekthez team_id hozzárendelése
   - Logika: user első team-je, vagy default team létrehozása
   
2. **Meglévő ötletek**:
   - Minden ötlethez team_id hozzárendelése
   - Logika: user első team-je, vagy default team létrehozása

3. **UserProject tábla**:
   - Eltávolítás vagy deprecate
   - Adatok migrálása (ha szükséges)

## Implementációs Lépések

### Fázis 1: Adatmodell (Kritikus)
1. ✅ Alembic migráció: `team_id` hozzáadása Project-hez
2. ✅ Alembic migráció: `team_id` hozzáadása Idea-hoz
3. ✅ Adat migráció: meglévő projektekhez team_id
4. ✅ Adat migráció: meglévő ötletekhez team_id
5. ✅ UserProject tábla eltávolítása vagy deprecate

### Fázis 2: Backend Services (Kritikus)
1. ✅ ProjectService refaktorálás
2. ✅ IdeaService refaktorálás
3. ✅ AuthService validáció hozzáadása
4. ✅ Access control logika frissítése

### Fázis 3: Backend Controllers (Kritikus)
1. ✅ ProjectController frissítése
2. ✅ IdeaController frissítése
3. ✅ API schemas frissítése

### Fázis 4: MCP Tools (Kritikus)
1. ✅ Project MCP tools frissítése
2. ✅ Idea MCP tools frissítése
3. ✅ Access control MCP-ben

### Fázis 5: Frontend (Magas prioritás)
1. ✅ Project UI frissítése
2. ✅ Idea UI frissítése
3. ✅ Services frissítése
4. ✅ State management frissítése

### Fázis 6: Tesztelés (Magas prioritás)
1. ✅ Unit tesztek
2. ✅ Integration tesztek
3. ✅ E2E tesztek

## Hozzáférési Szabályok

### Projektek
- **Admin**: Hozzáférés minden projekthez
- **Team Leader**: Hozzáférés saját team projekteihez (teljes kezelés)
- **Team Member**: Hozzáférés saját team projekteihez (olvasás, korlátozott szerkesztés)

### Ötletek
- **Admin**: Hozzáférés minden ötlethez
- **Team Leader**: Hozzáférés saját team ötleteihez (teljes kezelés)
- **Team Member**: Hozzáférés saját team ötleteihez (olvasás, korlátozott szerkesztés)

## Edge Cases

1. **Meglévő projektek/ötletek**: Migrálás user első team-jéhez
2. **User-ek team nélkül**: 
   - Regisztrációkor automatikusan team-hez adás
   - Meglévő user-ek: default team létrehozása vagy admin hozzárendelése
3. **UserProject tábla**: 
   - Deprecate, de ne töröljük azonnal (backward compatibility)
   - Később eltávolítás
4. **Orphaned projects/ideas**: 
   - Migráció során kezelés
   - Validáció, hogy ne lehessen team nélküli projekt/ötlet

## Tesztelési Terv

1. **Unit tesztek**: Service réteg, access control
2. **Integration tesztek**: API endpoints, MCP tools
3. **E2E tesztek**: Teljes workflow (project/idea creation, listing, access)
4. **Migráció tesztek**: Meglévő adatok migrálása

## Rollback Terv

Ha valami nem működik:
1. Migráció visszavonása (Alembic downgrade)
2. UserProject tábla visszaállítása
3. Kód visszaállítása előző verzióra

## Jegyzetek

- **Fontos**: Ez egy breaking change, minden frontend és backend kódot frissíteni kell
- **Kompatibilitás**: UserProject tábla deprecate, de ne töröljük azonnal
- **Migráció**: Gondosan kell kezelni a meglévő adatokat
