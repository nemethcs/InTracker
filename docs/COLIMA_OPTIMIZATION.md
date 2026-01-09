# Colima Memória Optimalizálás

## Probléma
A Colima VM alapértelmezetten 8GB memóriát foglalt le, ami túl sok volt a fejlesztési környezethez.

## Megoldás
A Colima VM memórialimit-jét 2GB-ra csökkentettük.

## Végrehajtás

### 1. Colima leállítása
```bash
colima stop
```

### 2. Colima újraindítása 2GB memóriával
```bash
colima start --memory 2 --cpu 2
```

### 3. Ellenőrzés
```bash
colima list
# Eredmény: MEMORY: 2GiB (korábban: 8GiB)
```

## Eredmények

### Memóriahasználat
- **Előtte**: 8GB RAM foglalva a Colima VM-hez
- **Utána**: 2GB RAM foglalva a Colima VM-hez
- **Megtakarítás**: 6GB RAM

### Konténerek memóriahasználata
- Backend: ~172MB / 512MB limit (34%)
- PostgreSQL: ~56MB / 512MB limit (11%)
- Redis: ~15MB / 128MB limit (12%)

### Teljes memóriahasználat
- Colima VM: 2GB
- Konténerek: ~244MB
- **Összesen**: ~2.25GB (korábban: ~8.25GB)

## Megjegyzések

- A 2GB memória elegendő a fejlesztési környezethez
- Ha több memóriára van szükség, növelhető: `colima stop && colima start --memory 4 --cpu 2`
- A CPU-k száma is csökkenthető/növelhető: `--cpu 1` vagy `--cpu 4`
- A változtatások a `~/.colima/default/colima.yaml` fájlban tárolódnak

## További optimalizálási lehetőségek

1. **CPU csökkentése**: Ha nincs szükség 2 CPU-ra, csökkenthető 1-re
2. **Disk méret csökkentése**: Ha nincs szükség 100GB-ra, csökkenthető
3. **Konténerek memórialimit-ek**: A `docker-compose.yml`-ben már be vannak állítva
