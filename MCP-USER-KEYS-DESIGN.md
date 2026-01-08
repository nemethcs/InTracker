# User-Specific MCP API Keys Design

## Cél

Minden felhasználónak saját MCP API kulcsot generálni, amely:
1. **Tartalmazza a user_id-t** (verifikálható módon)
2. **Automatikusan szűr** az MCP toolokban a user hozzáférési jogai alapján
3. **Biztonságos** és visszavonható

## Működés

### 1. MCP API Kulcs Generálás

**Formátum opciók:**

#### Opció A: JWT-alapú kulcs
```
mcp_<user_id>_<jwt_token>
```
- A JWT tartalmazza a user_id-t és lejárati időt
- Verifikálható és biztonságos
- Lejárat kezelhető

#### Opció B: Hash-alapú kulcs
```
mcp_<user_id>_<secure_random_hash>
```
- Egyszerűbb, nincs lejárat
- Hash tárolása az adatbázisban
- Gyorsabb verifikáció

**Ajánlás: Opció B (Hash-alapú)**, mert:
- Egyszerűbb implementáció
- Nincs lejárat kezelés
- Gyorsabb verifikáció
- Könnyebb visszavonás (törlés az adatbázisból)

### 2. Adatmodell

```python
class McpApiKey(Base):
    """MCP API Key model."""
    __tablename__ = "mcp_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String, unique=True, nullable=False, index=True)  # Hashed key for verification
    key_prefix = Column(String, nullable=False)  # First part of key for quick lookup (mcp_<user_id>_)
    name = Column(String, nullable=True)  # Optional name for the key (e.g., "Cursor Dev", "Cursor Prod")
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    # Relationships
    user = relationship("User", back_populates="mcp_api_keys")
```

**Kulcs formátum:**
```
mcp_<user_id>_<32_char_random_token>
```

Példa:
```
mcp_a1b2c3d4-e5f6-7890-abcd-ef1234567890_AbCdEfGhIjKlMnOpQrStUvWxYz123456
```

### 3. Kulcs Generálás

```python
import secrets
import hashlib

def generate_mcp_key(user_id: UUID, name: Optional[str] = None) -> tuple[str, str]:
    """Generate MCP API key for user.
    
    Returns:
        tuple: (full_key, key_hash)
    """
    # Generate random token
    token = secrets.token_urlsafe(32)  # 32 bytes = ~43 chars base64
    
    # Build key
    key = f"mcp_{user_id}_{token}"
    
    # Hash for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    # Store in database
    mcp_key = McpApiKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=f"mcp_{user_id}_",
        name=name,
        is_active=True,
    )
    db.add(mcp_key)
    db.commit()
    
    return key, key_hash
```

### 4. Kulcs Verifikáció

```python
def verify_mcp_key(key: str) -> Optional[UUID]:
    """Verify MCP API key and return user_id if valid.
    
    Returns:
        UUID: user_id if key is valid, None otherwise
    """
    # Parse key format: mcp_<user_id>_<token>
    if not key.startswith("mcp_"):
        return None
    
    parts = key.split("_", 2)
    if len(parts) != 3:
        return None
    
    try:
        user_id = UUID(parts[1])
    except ValueError:
        return None
    
    # Hash the key
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    # Look up in database
    db = SessionLocal()
    try:
        mcp_key = db.query(McpApiKey).filter(
            McpApiKey.key_hash == key_hash,
            McpApiKey.user_id == user_id,
            McpApiKey.is_active == True,
        ).first()
        
        if not mcp_key:
            return None
        
        # Check expiration
        if mcp_key.expires_at and mcp_key.expires_at < datetime.utcnow():
            return None
        
        # Update last_used_at
        mcp_key.last_used_at = datetime.utcnow()
        db.commit()
        
        return user_id
    finally:
        db.close()
```

### 5. MCP Server Integráció

Az MCP server stdio protokollt használ, nem HTTP-t. A kulcsot kétféleképpen lehet átadni:

#### Opció A: Environment Variable
```bash
export MCP_API_KEY="mcp_<user_id>_<token>"
```

#### Opció B: MCP Connection Init
Az MCP protokoll támogatja az initialization paramétereket. A kulcsot itt lehet átadni.

**Ajánlás: Opció A (Environment Variable)**, mert:
- Egyszerűbb
- Cursor könnyen beállíthatja
- Nincs protokoll módosítás szükséges

**MCP Server módosítás:**

```python
# backend/src/mcp/server.py
import os
from src.mcp.services.auth import verify_mcp_key, get_user_from_key

# Get API key from environment
MCP_API_KEY = os.getenv("MCP_API_KEY")
USER_ID = None

if MCP_API_KEY:
    USER_ID = verify_mcp_key(MCP_API_KEY)
    if not USER_ID:
        raise ValueError("Invalid MCP API key")

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls with user context."""
    if not USER_ID:
        return [TextContent(type="text", text=json.dumps({"error": "MCP API key required"}))]
    
    # Add user_id to all tool calls
    arguments["_user_id"] = str(USER_ID)
    
    # ... existing tool handlers ...
```

### 6. Tool Handler Módosítások

Minden tool handler automatikusan kapja a `_user_id` paramétert és szűr a user hozzáférési jogai alapján:

```python
async def handle_list_projects(status: Optional[str] = None, _user_id: Optional[str] = None) -> dict:
    """Handle list projects tool call with user filtering."""
    if not _user_id:
        return {"error": "User context required"}
    
    db = SessionLocal()
    try:
        user_id = UUID(_user_id)
        
        # Use ProjectService to get user's projects
        projects, total = ProjectService.get_user_projects(
            db=db,
            user_id=user_id,
            status=status,
        )
        
        # Also include projects from teams user is member of
        from src.database.models import TeamMember, UserProject
        from sqlalchemy import and_
        
        # Get user's teams
        user_teams = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == user_id
        ).subquery()
        
        # Get projects from team members
        team_projects = db.query(UserProject.project_id).join(
            user_teams,  # This would need TeamProject junction table
            # For now, we'll use UserProject - if user is in same team as project owner
        ).distinct()
        
        # Combine results
        # ... implementation ...
        
        return {
            "projects": [...],
            "count": total,
        }
    finally:
        db.close()
```

### 7. Hozzáférés Ellenőrzés

Minden tool handler ellenőrzi a user hozzáférési jogait:

```python
def check_user_project_access(db: Session, user_id: UUID, project_id: UUID) -> bool:
    """Check if user has access to project."""
    # Check UserProject relationship
    user_project = db.query(UserProject).filter(
        UserProject.user_id == user_id,
        UserProject.project_id == project_id,
    ).first()
    
    if user_project:
        return True
    
    # Check if user is admin
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == "admin":
        return True
    
    # Check if user is member of team that has access to project
    # (if TeamProject junction table exists in future)
    
    return False
```

### 8. API Endpointok

#### Generate MCP Key
```python
@router.post("/users/{user_id}/mcp-keys")
async def create_mcp_key(
    user_id: UUID,
    name: Optional[str] = None,
    expires_in_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate MCP API key for user. User can only create keys for themselves."""
    if current_user["user_id"] != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot create keys for other users")
    
    key, key_hash = generate_mcp_key(user_id, name, expires_in_days)
    
    return {
        "key": key,  # Show only once!
        "key_id": str(mcp_key.id),
        "name": name,
        "created_at": mcp_key.created_at.isoformat(),
        "expires_at": mcp_key.expires_at.isoformat() if mcp_key.expires_at else None,
        "warning": "Store this key securely. It will not be shown again.",
    }
```

#### List MCP Keys
```python
@router.get("/users/{user_id}/mcp-keys")
async def list_mcp_keys(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List MCP API keys for user."""
    if current_user["user_id"] != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot view keys for other users")
    
    keys = db.query(McpApiKey).filter(McpApiKey.user_id == user_id).all()
    
    return {
        "keys": [
            {
                "id": str(k.id),
                "name": k.name,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            }
            for k in keys
        ]
    }
```

#### Revoke MCP Key
```python
@router.delete("/users/{user_id}/mcp-keys/{key_id}")
async def revoke_mcp_key(
    user_id: UUID,
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke MCP API key."""
    if current_user["user_id"] != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot revoke keys for other users")
    
    mcp_key = db.query(McpApiKey).filter(
        McpApiKey.id == key_id,
        McpApiKey.user_id == user_id,
    ).first()
    
    if not mcp_key:
        raise HTTPException(status_code=404, detail="Key not found")
    
    mcp_key.is_active = False
    db.commit()
    
    return {"message": "Key revoked successfully"}
```

## Implementációs Lépések

1. **Adatmodell létrehozása**
   - `McpApiKey` model
   - Alembic migráció

2. **Service réteg**
   - `McpKeyService` létrehozása
   - `generate_mcp_key()`
   - `verify_mcp_key()`

3. **MCP Server módosítás**
   - Environment variable olvasás
   - Kulcs verifikáció
   - User context átadása tool handler-eknek

4. **Tool Handler módosítások**
   - User context automatikus injektálása
   - Hozzáférés ellenőrzés minden tool-ban
   - User-alapú szűrés

5. **API Endpointok**
   - Generate key endpoint
   - List keys endpoint
   - Revoke key endpoint

6. **Frontend**
   - MCP keys kezelő UI
   - Key generálás és megjelenítés
   - Key törlés/revoke

## Biztonsági Megfontolások

1. **Kulcs tárolás**: Hash-elt formában az adatbázisban
2. **Kulcs megjelenítés**: Csak egyszer, generáláskor
3. **Kulcs visszavonás**: `is_active = False` beállítása
4. **Lejárat**: Opcionális `expires_at` mező
5. **Használat követés**: `last_used_at` mező
6. **Rate limiting**: Lehetőség későbbi hozzáadásra

## Cursor Integráció

A Cursor-ban az MCP API kulcsot environment variable-ként kell beállítani:

```bash
# .env vagy Cursor settings
MCP_API_KEY="mcp_<user_id>_<token>"
```

Vagy Cursor settings-ben:
```json
{
  "mcp": {
    "intracker": {
      "apiKey": "mcp_<user_id>_<token>"
    }
  }
}
```
