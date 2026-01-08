# Real-time Update Patterns

## 📋 Áttekintés

Ez a dokumentum leírja a real-time update pattern-eket, amelyeket az InTracker projektben használunk. A rendszer SignalR (WebSocket) alapú real-time kommunikációt használ a frontend és backend között, hogy a felhasználók azonnal lássák a változásokat anélkül, hogy oldalt kellene frissíteniük.

## 🏗️ Architektúra

### Backend (FastAPI + SignalR)

```
Controller → Service → Database
     ↓
BackgroundTasks → SignalR Hub → WebSocket → Frontend
```

### Frontend (React + Zustand)

```
SignalR Service → Event Handlers → Store Update → Component Re-render
```

## 🔄 Backend Pattern

### 1. Controller Pattern

Minden controller művelet, ami UI változást okoz, **KÖTELEZŐEN** tartalmaznia kell SignalR broadcast-et.

#### Alapvető struktúra:

```python
from fastapi import BackgroundTasks
from src.services.signalr_hub import broadcast_*_update

@router.post("", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: EntityCreate,
    background_tasks: BackgroundTasks = BackgroundTasks(),  # ✅ KÖTELEZŐ
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ... business logic ...
    entity = entity_service.create_entity(...)
    
    # ✅ KÖTELEZŐ: Broadcast SignalR update
    if entity:
        background_tasks.add_task(
            broadcast_entity_update,
            str(entity.project_id),  # vagy team_id
            str(entity.id),
            {"action": "created", "title": entity.title, ...}
        )
    
    return entity
```

#### Broadcast függvények:

**Project-level entities:**
- `broadcast_todo_update(project_id: str, todo_id: str, user_id: UUID, changes: dict)`
  - Broadcasts: `todoUpdated`
  - Changes: `{"action": "created|updated|deleted", "status": "...", "title": "...", ...}`
  
- `broadcast_feature_update(project_id: str, feature_id: str, progress: int, status: Optional[str])`
  - Broadcasts: `featureUpdated`
  - Updates: progress percentage, status
  
- `broadcast_project_update(project_id: str, changes: dict)`
  - Broadcasts: `projectUpdated`
  - Changes: `{"action": "created|updated|deleted", "name": "...", "status": "...", ...}`
  
- `broadcast_session_start(project_id: str, user_id: str)`
  - Broadcasts: `sessionStarted`
  
- `broadcast_session_end(project_id: str, user_id: str)`
  - Broadcasts: `sessionEnded`

**Team-level entities:**
- `broadcast_idea_update(team_id: str, idea_id: str, changes: dict)`
  - Broadcasts: `ideaUpdated`
  - Changes: `{"action": "created|updated|deleted|converted_to_project", "title": "...", ...}`

### 2. MCP Tools Pattern

MCP tools is **KÖTELEZŐEN** broadcast-elnek, ha UI változást okoznak.

```python
from src.services.signalr_hub import broadcast_*_update
import asyncio

async def handle_create_entity(...):
    # ... create entity ...
    
    # ✅ KÖTELEZŐ: Broadcast SignalR update (fire and forget)
    import asyncio
    asyncio.create_task(
        broadcast_entity_update(
            project_id,
            str(entity.id),
            {"action": "created", ...}
        )
    )
    
    return result
```

**Fontos:** MCP tools esetén `asyncio.create_task`-ot használunk, mert nincs `BackgroundTasks` dependency.

### 3. Broadcast Message Formátum

```python
# SignalR message format
message = {
    "type": 1,  # SignalR invocation
    "target": "entityUpdated",  # Event name
    "arguments": [{
        "entityId": str(entity_id),
        "projectId": str(project_id),  # vagy teamId
        "changes": {
            "action": "created" | "updated" | "deleted",
            "field1": value1,
            "field2": value2,
            ...
        }
    }]
}
```

### 4. Project vs Team Broadcast

- **Project-level entities** (todo, feature, element, document, session):
  - `broadcast_to_project(project_id, message)`
  - Csak azok a kapcsolatok kapják meg, akik a projekthez csatlakoztak

- **Team-level entities** (idea):
  - `broadcast_to_team(team_id, message)`
  - Minden kapcsolat megkapja (frontend szűr team_id alapján)

## 🎨 Frontend Pattern

### 1. SignalR Service Setup

```typescript
// frontend/src/services/signalrService.ts

export interface SignalREvents {
  todoUpdated: (data: { todoId: string; projectId: string; userId: string; changes: any }) => void
  featureUpdated: (data: { featureId: string; projectId: string; progress: number; status?: string }) => void
  projectUpdated: (data: { projectId: string; changes: any }) => void
  ideaUpdated: (data: { ideaId: string; teamId: string; changes: any }) => void
  // ... más események
}

// Event handler regisztrálás
this.connection.on('entityUpdated', (data: any) => {
  const eventData = Array.isArray(data) ? data[0] : (data?.arguments?.[0] || data)
  this.emit('entityUpdated', eventData)
})
```

### 2. Store Pattern (Zustand)

#### Optimalizált Store Update (AJÁNLOTT)

```typescript
// ✅ JÓ: Közvetlen store frissítés, nincs loading state
useEffect(() => {
  const handleEntityUpdate = (data: { entityId: string; changes: any }) => {
    const { entities } = useEntityStore.getState()
    
    if (data.changes?.action === 'created') {
      // Új entitás - fetch silently (nincs loading state)
      fetchEntitySilently(data.entityId)
    } else if (data.changes?.action === 'deleted') {
      // Törlés - eltávolítás store-ból
      useEntityStore.setState({ 
        entities: entities.filter(e => e.id !== data.entityId) 
      })
    } else {
      // Update - közvetlen store frissítés changes alapján
      const index = entities.findIndex(e => e.id === data.entityId)
      if (index >= 0) {
        const updated = [...entities]
        updated[index] = { ...updated[index], ...data.changes }
        useEntityStore.setState({ entities: updated })
      }
    }
  }
  
  signalrService.on('entityUpdated', handleEntityUpdate)
  return () => signalrService.off('entityUpdated', handleEntityUpdate)
}, [])
```

#### Store metódusok

```typescript
// ✅ JÓ: Silently fetch (nincs loading state trigger)
fetchEntitySilently: async (id: string) => {
  try {
    const entity = await entityService.getEntity(id)
    set(state => {
      const index = state.entities.findIndex(e => e.id === id)
      if (index >= 0) {
        const entities = [...state.entities]
        entities[index] = entity
        return { entities }
      }
      return { entities: [...state.entities, entity] }
    })
    return entity
  } catch (error) {
    console.error('Failed to fetch entity silently:', error)
    throw error
  }
}
```

#### ❌ ROSSZ: Teljes lista újratöltés

```typescript
// ❌ ROSSZ: Teljes lista újratöltés triggerel loading state-et
const handleEntityUpdate = (data) => {
  refetch()  // ❌ Ez újratölti az egész listát és triggerel loading state-et
}
```

### 3. Component Pattern

```typescript
// frontend/src/pages/EntityPage.tsx

export function EntityPage() {
  const { entities } = useEntityStore()  // Store-ból olvasás
  
  useEffect(() => {
    // SignalR subscription (lásd Store Pattern fent)
    // A store automatikusan frissül, a komponens re-renderelődik
  }, [])
  
  return (
    <div>
      {entities.map(entity => (
        <EntityCard key={entity.id} entity={entity} />
      ))}
    </div>
  )
}
```

## 📝 Best Practices

### Backend

1. **MINDIG használj BackgroundTasks-ot** controller műveleteknél
2. **MINDIG broadcast-elj** create/update/delete műveleteknél
3. **Fire and forget**: Ne várj a broadcast befejezésére
4. **Message formátum**: Kövesd a SignalR message formátumot
5. **Error handling**: Broadcast hibák ne akadályozzák a műveletet

### Frontend

1. **Nincs teljes lista újratöltés**: Csak a módosított entitást frissítsd
2. **Nincs loading state trigger**: Használj `fetchSilently` metódusokat
3. **Közvetlen store frissítés**: UPDATE esetén használd a `changes` objektumot
4. **Cleanup**: Mindig unsubscribe-olj SignalR eseményekről
5. **Error handling**: Broadcast hibák ne törjék el a UI-t

## 🔍 Példák

### Backend: Todo Create

```python
@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = todo_service.create_todo(...)
    
    # Broadcast todo creation
    element = db.query(ProjectElement).filter(ProjectElement.id == todo.element_id).first()
    if element:
        background_tasks.add_task(
            broadcast_todo_update,
            str(element.project_id),
            str(todo.id),
            UUID(current_user["user_id"]),
            {"action": "created", "title": todo.title, "status": todo.status}
        )
        # Feature progress update if linked
        if todo.feature_id:
            progress = feature_service.calculate_feature_progress(db, todo.feature_id)
            feature = feature_service.get_feature_by_id(db, todo.feature_id)
            background_tasks.add_task(
                broadcast_feature_update,
                str(element.project_id),
                str(todo.feature_id),
                progress["percentage"],
                feature.status if feature else None
            )
    
    return todo
```

### Frontend: Idea Update Handler

```typescript
useEffect(() => {
  const { fetchIdeaSilently } = useIdeaStore.getState()
  
  const handleIdeaUpdate = (data: { ideaId: string; teamId: string; changes: any }) => {
    const { ideas } = useIdeaStore.getState()
    
    if (data.changes?.action === 'created') {
      fetchIdeaSilently(data.ideaId).catch(console.error)
    } else if (data.changes?.action === 'deleted') {
      useIdeaStore.setState({ 
        ideas: ideas.filter(i => i.id !== data.ideaId) 
      })
    } else {
      // Update: közvetlen store frissítés
      const index = ideas.findIndex(i => i.id === data.ideaId)
      if (index >= 0) {
        const updated = [...ideas]
        updated[index] = { ...updated[index], ...data.changes }
        useIdeaStore.setState({ ideas: updated })
      } else {
        fetchIdeaSilently(data.ideaId).catch(console.error)
      }
    }
  }
  
  signalrService.on('ideaUpdated', handleIdeaUpdate)
  return () => signalrService.off('ideaUpdated', handleIdeaUpdate)
}, [])
```

## 🧪 Tesztelés

### Manuális tesztelés

1. Nyiss két böngészőablakot egymás mellett
2. Az egyikben végezz műveleteket (create/update/delete)
3. A másikban ellenőrizd, hogy real-time frissül-e

### DevTools ellenőrzés

- **Network → WS**: Nézd a SignalR üzeneteket
- **Console**: Nézd a SignalR eseményeket
- **Application → Storage**: Nézd a SignalR connection state-et

### Várható viselkedés

- ✅ Minden create/update/delete művelet triggerel broadcast-et
- ✅ Frontend automatikusan frissül, oldal újratöltés nélkül
- ✅ Több böngészőablak szinkronban marad
- ✅ Nincs teljes lista újratöltés
- ✅ Nincs loading state trigger
- ✅ Csak a módosított entitás komponens re-renderelődik

## 📚 További információk

- [SignalR Hub Implementation](../backend/src/services/signalr_hub.py)
- [Frontend SignalR Service](../frontend/src/services/signalrService.ts)
- [Testing Guide](../TESTING_REALTIME.md)

## ✅ Checklist új entitás hozzáadásához

- [ ] Backend controller: `BackgroundTasks` hozzáadása
- [ ] Backend controller: `broadcast_*_update` hívás
- [ ] Backend: Broadcast függvény létrehozása (ha új)
- [ ] Frontend: SignalR event interface-hez hozzáadás
- [ ] Frontend: SignalR event handler regisztrálás
- [ ] Frontend: Store `fetchSilently` metódus
- [ ] Frontend: Component SignalR subscription
- [ ] Tesztelés: Manuális end-to-end teszt
- [ ] Dokumentáció: Pattern dokumentálása
