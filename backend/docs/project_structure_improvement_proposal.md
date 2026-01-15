# Projekt Struktúra Javítási Javaslat

## Jelenlegi Problémák

### 1. Project Elements (Structure)
- **Túl komplex**: 6 típus (module, component, milestone, technical_block, decision_point)
- **Nehéz navigálni**: Hierarchikus fa struktúra, de nem egyértelmű a használat
- **Kötelező, de nehézkes**: Todo-khoz kötelezően kell element, de nem egyértelmű melyiket válasszuk
- **Frontend integráció gyenge**: Accordion-ban van, de nem túl használható
- **Nem egyértelmű a kapcsolat**: Feature-ök és elemek közötti kapcsolat nem világos

### 2. Documents
- **Túl sok típus**: 6 típus (architecture, adr, domain, constraints, runbook, ai_instructions)
- **Nehéz megtalálni**: Linkelhető elemekhez vagy todo-khoz, de nem egyértelmű
- **Nincs jó integráció**: Nem része a workflow-nak, nehéz elérni
- **Frontend integráció hiányos**: Nehéz megtalálni a releváns dokumentumokat

## Javasolt Megoldások

### Opció A: Radikális Egyszerűsítés (AJÁNLOTT)

#### 1. Project Elements eltávolítása
- **Todo-khoz automatikus "default" element**: Minden todo-hoz automatikusan létrehozunk egy "default" element-et a projekt szintjén
- **Feature-ök közvetlenül a projekthez**: Feature-ök nem kellenek elemekhez linkelni
- **Egyszerűbb workflow**: Feature → Todo (közvetlenül, element nélkül)

**Előnyök:**
- ✅ Sokkal egyszerűbb használat
- ✅ Nincs felesleges komplexitás
- ✅ Feature + Todo már jól működik, ez csak egyszerűsíti

**Hátrányok:**
- ❌ Már létező projektek migrálása szükséges
- ❌ Elveszítjük a hierarchikus struktúrát (de lehet, hogy nem is kell)

#### 2. Documents egyszerűsítése
- **Feature-hez kötött dokumentumok**: Dokumentumok automatikusan feature-hez linkelődnek
- **3 típus**: `architecture`, `adr`, `notes` (egyszerűsített)
- **Feature Detail oldalon látható**: Dokumentumok közvetlenül a feature oldalon

**Előnyök:**
- ✅ Könnyen megtalálható
- ✅ Integrálva a workflow-ba
- ✅ Kevesebb típus, egyszerűbb

**Hátrányok:**
- ❌ Már létező dokumentumok migrálása szükséges

---

### Opció B: Fokozatos Egyszerűsítés

#### 1. Project Elements egyszerűsítése
- **Csak "Module" típus**: Eltávolítjuk a többi típust, csak "module" marad
- **Opcionális**: Element csak akkor kell, ha valóban szükséges (pl. nagy projekteknél)
- **Automatikus létrehozás**: Feature létrehozásakor automatikusan létrehozunk egy "default" element-et

**Előnyök:**
- ✅ Egyszerűbb, de megtartjuk a hierarchiát
- ✅ Visszafelé kompatibilis
- ✅ Opcionális használat

**Hátrányok:**
- ❌ Még mindig komplex lehet
- ❌ Nem oldja meg teljesen a problémát

#### 2. Documents javítása
- **Feature-hez kötött**: Dokumentumok automatikusan feature-hez linkelődnek
- **4 típus**: `architecture`, `adr`, `runbook`, `notes`
- **Feature Detail oldalon**: Dokumentumok közvetlenül láthatók

**Előnyök:**
- ✅ Jobb integráció
- ✅ Könnyen megtalálható

**Hátrányok:**
- ❌ Még mindig több típus, mint kellene

---

### Opció C: Hibrid Megoldás (KOMPROMISSZUM)

#### 1. Project Elements automatikus kezelése
- **Automatikus element létrehozás**: Feature létrehozásakor automatikusan létrehozunk egy "default" element-et
- **Todo-khoz automatikus element**: Todo létrehozásakor automatikusan a feature-hez tartozó element-et használjuk
- **Opcionális manuális kezelés**: Nagy projekteknél lehet manuálisan is kezelni

**Előnyök:**
- ✅ Visszafelé kompatibilis
- ✅ Egyszerű használat (automatikus)
- ✅ Rugalmas (manuális is lehet)

**Hátrányok:**
- ❌ Még mindig van element struktúra (de automatikus)

#### 2. Documents feature-hez kötése
- **Feature-hez automatikus linkelés**: Dokumentumok automatikusan a feature-hez linkelődnek
- **3 típus**: `architecture`, `adr`, `notes`
- **Feature Detail oldalon**: Dokumentumok közvetlenül láthatók

**Előnyök:**
- ✅ Könnyen megtalálható
- ✅ Integrálva a workflow-ba
- ✅ Egyszerűbb

---

## Ajánlás: Opció A (Radikális Egyszerűsítés)

### Miért?
1. **Feature + Todo már jól működik**: Az element struktúra csak komplexitást ad
2. **Egyszerűbb = jobb**: Kevesebb koncepció, könnyebb használat
3. **Automatizálható**: Todo-khoz automatikusan lehet "default" element-et használni

### Implementációs Terv

#### 1. Project Elements eltávolítása
- **Backend**: 
  - Todo-khoz automatikus "default" element létrehozása projekt szintjén
  - Feature-ök közvetlenül a projekthez (nincs element linkelés)
  - Migration: Meglévő elemeket "default" element-ekké konvertáljuk
- **Frontend**: 
  - Element Tree eltávolítása
  - Todo létrehozás egyszerűsítése (nincs element választás)

#### 2. Documents feature-hez kötése
- **Backend**: 
  - Dokumentumok automatikusan feature-hez linkelődnek
  - 3 típus: `architecture`, `adr`, `notes`
  - Migration: Meglévő dokumentumokat feature-hez linkeljük
- **Frontend**: 
  - Dokumentumok a Feature Detail oldalon
  - Könnyű hozzáadás/szerkesztés

### Migration Stratégia

1. **Phase 1**: Új mezők hozzáadása (backward compatible)
2. **Phase 2**: Automatikus migrálás meglévő adatokhoz
3. **Phase 3**: Deprecate régi mezők
4. **Phase 4**: Régi mezők eltávolítása

---

## Alternatív Javaslat: "Smart Defaults" Megközelítés

Ha nem akarjuk teljesen eltávolítani az elemeket, akkor:

1. **Automatikus element létrehozás**: Feature létrehozásakor automatikusan létrehozunk egy "default" element-et
2. **Todo-khoz automatikus element**: Todo létrehozásakor automatikusan a feature-hez tartozó element-et használjuk
3. **Opcionális manuális kezelés**: Csak akkor kell manuálisan kezelni, ha valóban szükséges

Ez a megközelítés:
- ✅ Visszafelé kompatibilis
- ✅ Egyszerű használat (automatikus)
- ✅ Rugalmas (manuális is lehet)
- ✅ Nem törli az elemeket, csak automatikussá teszi

---

## Összefoglalás

**Ajánlás**: Opció A (Radikális Egyszerűsítés) vagy "Smart Defaults" megközelítés

**Főbb változtatások**:
1. Project Elements automatikus kezelése vagy eltávolítása
2. Documents feature-hez kötése
3. Egyszerűbb, használhatóbb workflow

**Előnyök**:
- ✅ Sokkal egyszerűbb használat
- ✅ Feature + Todo már jól működik, ez csak egyszerűsíti
- ✅ Dokumentumok könnyen megtalálhatók
- ✅ Integrálva a workflow-ba
