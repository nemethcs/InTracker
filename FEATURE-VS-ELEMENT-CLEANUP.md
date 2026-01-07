# Feature vs Element Cleanup - Javaslatok

## ⚠️ Probléma

A jelenlegi adatbázisban vannak olyan **Feature-ök**, amik valójában **ProjectElement-ek** kellene legyenek:

### Példák:
- ❌ **"Database Setup"** - Feature
- ❌ **"Frontend Web Application"** - Feature  
- ❌ **"Backend API"** - Feature
- ❌ **"MCP Server"** - Feature

### Miért probléma?

Ezek **technikai struktúra elemek**, nem **funkcionalitások**:

| Jelenleg (Feature) | Helyes (ProjectElement) |
|-------------------|------------------------|
| Database Setup | "Database Setup" (module type) |
| Frontend Web Application | "Frontend Setup & Configuration" (module type) |
| Backend API | "Backend API" (module type) |
| MCP Server | "MCP Server" (module type) |

---

## ✅ Helyes használat

### Feature-ök (funkcionalitások):
- ✅ "User Authentication" - Felhasználó bejelentkezés
- ✅ "Project Management" - Projekt kezelés
- ✅ "Real-time Collaboration" - Valós idejű együttműködés
- ✅ "Cursor MCP Integráció Fejlesztés" - Ez is jó, mert egy funkcionalitás

### ProjectElement-ek (technikai struktúra):
- ✅ "Database Setup" (module)
- ✅ "Frontend Setup & Configuration" (module)
- ✅ "Backend API" (module)
- ✅ "MCP Server" (module)

---

## 🔧 Javasolt megoldás

### 1. Migráció script

```python
# migration_script.py
"""
Migrate incorrect Features to ProjectElements
"""
from src.database.models import Feature, ProjectElement, FeatureElement, Todo
from src.services.database import get_db_session

def migrate_features_to_elements():
    db = get_db_session()
    
    # Features to migrate
    features_to_migrate = [
        "Database Setup",
        "Frontend Web Application", 
        "Backend API",
        "MCP Server"
    ]
    
    for feature_name in features_to_migrate:
        feature = db.query(Feature).filter(Feature.name == feature_name).first()
        if not feature:
            continue
        
        # Create ProjectElement
        element = ProjectElement(
            project_id=feature.project_id,
            type="module",
            title=feature.name,
            description=feature.description,
            status=feature.status,
        )
        db.add(element)
        db.flush()
        
        # Migrate todos
        todos = db.query(Todo).filter(Todo.feature_id == feature.id).all()
        for todo in todos:
            todo.element_id = element.id
            todo.feature_id = None  # Remove feature link
        
        # Migrate linked elements (if any)
        feature_elements = db.query(FeatureElement).filter(
            FeatureElement.feature_id == feature.id
        ).all()
        # These should become children of the new element
        
        # Delete old feature
        db.delete(feature)
    
    db.commit()
```

### 2. Manuális javítás

1. **Létrehozni ProjectElement-eket** a feature-ök helyett
2. **Todo-k átvitele** element-ekhez
3. **Feature-ök törlése** vagy átnevezése funkcionalitásokra

---

## 📋 Checklist

- [ ] Azonosítani az összes technikai feature-t
- [ ] Létrehozni megfelelő ProjectElement-eket
- [ ] Todo-k átvitele
- [ ] Feature-ök törlése vagy átnevezése
- [ ] Dokumentáció frissítése

---

## 💡 Jövőbeli szabályok

### Feature létrehozás előtt kérdezd meg:
1. **Ez egy funkcionalitás, amit a felhasználó használ?** → Feature
2. **Ez egy technikai komponens/modul?** → ProjectElement

### Példák:

**Feature (funkcionalitás):**
- "User can login"
- "User can create projects"
- "Real-time notifications"

**ProjectElement (technikai):**
- "Database schema"
- "API endpoints"
- "Frontend components"
