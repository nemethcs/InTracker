# InTracker

AI-first projektmenedzsment rendszer - kontextusmegőrzésre és fejlesztő-AI együttműködésre épül.

## 🚀 Gyors Start

### Előfeltételek
- Docker és Docker Compose
- Python 3.11+
- pip vagy poetry

### Első Lépések

1. **Environment változók beállítása:**
```bash
# Backend .env fájl
cd backend
cp .env.example .env
# Állítsd be a DATABASE_URL-t: postgresql://intracker:intracker_dev@localhost:5433/intracker
```

2. **Docker környezet indítása:**
```bash
docker-compose up -d postgres redis
```

3. **Backend dependencies telepítése:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Database migration (Alembic):**
```bash
cd backend
alembic upgrade head
```

5. **Backend indítása:**
```bash
cd backend
uvicorn src.main:app --reload --port 3000
```

6. **API dokumentáció:**
- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

## 📁 Projekt Struktúra

```
InTracker/
├── prisma/              # Prisma schema (reference, SQLAlchemy models használjuk)
├── backend/             # Python/FastAPI Backend
│   ├── src/
│   │   ├── api/         # API routes, controllers, schemas
│   │   ├── services/    # Business logic
│   │   ├── database/    # SQLAlchemy models
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── mcp-server/          # Python MCP Server (később)
├── docker-compose.yml   # Docker környezet
└── docs/                # Dokumentáció
```

## 📚 Dokumentáció

- **`start.md`** - Alap koncepció
- **`architecture.md`** - Rendszerarchitektúra
- **`user-guide.md`** - Felhasználói útmutató
- **`azure-deployment-guide.md`** - Azure deployment
- **`mvp-roadmap.md`** - MVP fejlesztési roadmap
- **`.cursorrules`** - Fejlesztési szabályok

## ✅ Todo Listák

- **`todos-database.md`** - Database fejlesztés
- **`todos-backend.md`** - Backend fejlesztés
- **`todos-mcp.md`** - MCP Server fejlesztés

## 🛠️ Fejlesztés

### Docker Parancsok

```bash
# Indítás
docker-compose up -d

# Leállítás
docker-compose down

# Logok
docker-compose logs -f [service]

# Teljes reset
docker-compose down -v && docker-compose up -d
```

### Backend Parancsok

```bash
cd backend

# Virtual environment aktiválás
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies telepítés
pip install -r requirements.txt

# Alembic migration
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1

# Backend indítás
uvicorn src.main:app --reload --port 3000

# API dokumentáció
# Swagger: http://localhost:3000/docs
# ReDoc: http://localhost:3000/redoc
```

## 📝 Következő Lépések

1. ✅ Prisma schema létrehozva (reference)
2. ✅ Docker környezet indítása
3. ✅ SQLAlchemy models létrehozva
4. ✅ Backend API alapstruktúra (FastAPI)
5. ✅ Authentication (JWT, password hashing)
6. ⏳ Alembic migrations
7. ⏳ További API endpoints (Projects, Features, Todos)
8. ⏳ MCP Server (Python)

Lásd: `mvp-roadmap.md` részletes tervért.

## 🔗 Hasznos Linkek

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Alembic Docs](https://alembic.sqlalchemy.org)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Architecture](architecture.md)
