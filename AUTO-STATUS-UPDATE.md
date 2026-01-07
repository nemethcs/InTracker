# Automatikus Element Státusz Frissítés

## 🎯 Cél

Automatikusan frissíteni az element státuszokat a todo számlálók alapján, hogy ne kelljen manuálisan állítani.

## ✅ Implementáció

### 1. Element Service - Új metódusok

**`update_element_status_by_todos(db, element_id)`**
- Számolja a todo-kat az element-hez
- Frissíti az element státuszát:
  - `done` → ha minden todo kész (done/total = 100%)
  - `in_progress` → ha van progress (done > 0 vagy in_progress > 0)
  - `todo` → ha nincs progress

**`update_parent_statuses(db, element_id)`**
- Rekurzívan frissíti a szülő elemek státuszát
- Számolja a gyerek elemek státuszát
- Frissíti a szülő státuszát:
  - `done` → ha minden gyerek done
  - `in_progress` → ha van done vagy in_progress gyerek
  - `todo` → ha minden gyerek todo

### 2. Todo Service - Automatikus hívások

**`create_todo()`**
- Todo létrehozása után automatikusan frissíti az element státuszát
- Frissíti a szülő elemek státuszát

**`update_todo()`**
- Todo státusz változásakor automatikusan frissíti az element státuszát
- Frissíti a szülő elemek státuszát

**`delete_todo()`**
- Todo törlése után automatikusan frissíti az element státuszát
- Frissíti a szülő elemek státuszát

## 🔄 Működés

1. **Todo státusz változik** (create/update/delete)
2. **Element státusz frissül** automatikusan (todo számlálók alapján)
3. **Szülő elemek státusza frissül** rekurzívan (gyerek elemek alapján)
4. **Nincs szükség manuális beavatkozásra**

## 📊 Példa

```
Todo: "Implement API endpoint" → done
  ↓
Element: "Projects API" → in_progress → done (ha minden todo kész)
  ↓
Parent: "API Layer" → in_progress → done (ha minden gyerek done)
  ↓
Parent: "Backend" → in_progress → done (ha minden gyerek done)
```

## ✅ Előnyök

- ✅ **Automatikus** - nincs szükség manuális beavatkozásra
- ✅ **Valós idejű** - todo változásakor azonnal frissül
- ✅ **Rekurzív** - szülő elemek is automatikusan frissülnek
- ✅ **Konzisztens** - mindig a todo számlálóknak megfelelő státusz
