# Project Structure vs Features - Magyarázat

## 🏗️ Project Structure (ProjectElement)

### Mi ez?
A **Project Structure** a projekt **hierarchikus technikai struktúrája** (fa struktúra).

### Adatok forrása:
- **Backend endpoint:** `GET /elements/project/{project_id}/tree`
- **Adatbázis tábla:** `project_elements`
- **Service:** `element_service.build_element_tree()`

### Jellemzők:
1. **Hierarchikus fa struktúra** (parent-child kapcsolatok)
   - Van `parent_id` mező
   - Egy elemnek lehetnek gyerekei
   - Példa: "Frontend Setup" → "UI Components" → "Button Component"

2. **Típusok (type):**
   - `milestone` - Mérföldkövek
   - `module` - Modulok (pl. "Frontend Setup & Configuration")
   - `component` - Komponensek
   - `task` - Feladatok
   - `technical_block` - Technikai blokkok
   - `decision_point` - Döntési pontok

3. **Kapcsolatok:**
   - **Todo-k:** Minden elemhez tartozhatnak todo-k (`todos` tábla, `element_id`)
   - **Feature-k:** Egy elem több feature-hez is kapcsolódhat (`feature_elements` tábla)

4. **Példa a képen:**
   ```
   - Database Constraints & Triggers (milestone, done, 4/4 todos)
   - Frontend Setup & Configuration (module, todo, 23/29 todos, 1 feature)
   - UI Components & Layout (module, todo, 3/3 todos, 1 feature)
   ```

---

## 🎯 Features

### Mi ez?
A **Features** a projekt **funkcionalitásai/feature-jei**, amik **több elemet összekapcsolnak**.

### Adatok forrása:
- **Backend endpoint:** `GET /features/project/{project_id}`
- **Adatbázis tábla:** `features`
- **Service:** `feature_service.get_features_by_project()`

### Jellemzők:
1. **Nincs hierarchia** - egyszerű lista
   - Nincs parent-child kapcsolat
   - Minden feature egy projekthez tartozik

2. **Progress tracking:**
   - `progress_percentage` - Százalékos haladás
   - `total_todos` - Összes todo száma
   - `completed_todos` - Kész todo-k száma
   - Automatikusan számolódik a hozzá tartozó todo-k alapján

3. **Kapcsolatok:**
   - **Element-ek:** Egy feature több elemet is tartalmazhat (`feature_elements` tábla)
   - **Todo-k:** Közvetlenül is tartozhatnak todo-k egy feature-hez (`todos` tábla, `feature_id`)

4. **Példa a képen:**
   ```
   - Frontend Web Application (todo, 88%, 22/25 todos)
   - Database Setup (done, 100%, 4/4 todos)
   - Cursor MCP Integráció Fejlesztés (todo, 66%, 4/6 todos)
   ```

---

## 🔗 Kapcsolat közöttük

### FeatureElement tábla
Ez a **kapcsolótábla**, ami összeköti a Feature-öket és az Element-eket:

```sql
feature_elements
├── feature_id → features.id
└── element_id → project_elements.id
```

### Példa:
- **Feature:** "Frontend Web Application"
- **Element-ek:** 
  - "Frontend Setup & Configuration" (module)
  - "UI Components & Layout" (module)
  - "State Management & API Integration" (module)

Ezek az elemek **több feature-hez is tartozhatnak**!

---

## 📊 Adatfolyam a képen

### Project Structure rész:
```
GET /elements/project/{id}/tree
  ↓
project_elements tábla (hierarchikus)
  ↓
ElementTree komponens
  ↓
Megjelenítés: 
  - Ikon (milestone ✓, module 📁)
  - Cím + leírás
  - Progress (done/total todos)
  - Feature számláló (hány feature-hez tartozik)
  - Status badge
```

### Features rész:
```
GET /features/project/{id}
  ↓
features tábla
  ↓
FeatureCard komponens
  ↓
Megjelenítés:
  - Feature név + leírás
  - Progress bar (százalék)
  - Todo számláló (completed/total)
  - Status badge
```

---

## ❓ Gyakori kérdések

### 1. Miért van "feature" típus az Element-ekben is?
- Ez egy **régi elnevezés**, ami összezavaró lehet
- Az Element `type` mezője csak a **technikai kategóriát** jelöli
- A **Feature** egy **külön entitás**, ami több elemet összekapcsol

### 2. Mi a különbség a Project Structure és Features között?
- **Project Structure:** Technikai hierarchia (MIT építünk)
- **Features:** Funkcionalitások (MIT csinálunk)

### 3. Hogyan kapcsolódnak össze?
- Egy **Feature** több **Element**-et tartalmazhat
- Egy **Element** több **Feature**-höz is tartozhat
- A kapcsolat a `feature_elements` táblán keresztül történik

### 4. Miért van két külön rész a képen?
- **Project Structure:** A projekt technikai felépítése (struktúra)
- **Features:** A projekt funkcionalitásai (amit a felhasználó lát)

---

## 💡 Javaslat a jobb érthetőséghez

1. **Project Structure** → **"Technical Structure"** vagy **"Project Architecture"**
2. **Features** → **"Functionalities"** vagy **"User Features"**
3. Az Element `type` mezőben ne legyen "feature", hanem csak technikai típusok

---

## ⚠️ Ismert problémák

### 1. Rossz Feature-ök
A jelenlegi adatbázisban vannak olyan Feature-ök, amik valójában ProjectElement-ek kellene legyenek:
- "Database Setup" → ProjectElement (module)
- "Frontend Web Application" → ProjectElement (module)
- "Backend API" → ProjectElement (module)
- "MCP Server" → ProjectElement (module)

**Megoldás:** Lásd `FEATURE-VS-ELEMENT-CLEANUP.md`

### 2. Project Structure todo-k és kapcsolatok
A Project Structure-ban most már:
- ✅ Todo számlálók láthatók (done/total)
- ✅ Feature számlálók láthatók
- ✅ Linked feature nevek tooltip-ben
- ✅ Element kattintásra detail dialog megnyílik todo-kkal és kapcsolatokkal
