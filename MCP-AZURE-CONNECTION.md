# InTracker MCP Server - Azure Connection Guide

## Áttekintés

Az InTracker MCP szerver HTTP/SSE transport-tal működik, ami lehetővé teszi a távoli kapcsolatot Azure-ból. A Cursor egy API kulccsal csatlakozik az Azure-beli MCP szerverhez.

## Architektúra

```
┌─────────────┐
│   Cursor    │
│  (Local)    │
└──────┬──────┘
       │ HTTP/SSE
       │ + API Key
       ↓
┌─────────────────────────┐
│  Azure App Service      │
│  MCP HTTP Server        │
│  (Port 3001)            │
└──────┬──────────────────┘
       │
       ├──→ PostgreSQL (Azure Database)
       ├──→ Redis (Azure Cache)
       └──→ GitHub API
```

## Lokális Tesztelés (Docker)

### 1. MCP Server indítása

```bash
docker-compose up -d mcp-server
```

A szerver a `http://localhost:3001` címen fut.

### 2. Cursor MCP Konfiguráció

Frissítsd a `~/.cursor/mcp.json` fájlt:

```json
{
  "mcpServers": {
    "intracker": {
      "url": "http://localhost:3001/mcp/sse",
      "headers": {
        "X-API-Key": "test"
      }
    }
  }
}
```

**Fontos:** A `test` API kulcs csak lokális teszteléshez. Azure-ban erős kulcsot használj!

### 3. Health Check

```bash
curl http://localhost:3001/health
```

Válasz:
```json
{
  "status": "ok",
  "service": "intracker-mcp-server"
}
```

## Azure Deployment

### 1. Environment Variables

Azure App Service-ben állítsd be:

```bash
DATABASE_URL=postgresql://user:pass@azure-postgres:5432/intracker
REDIS_HOST=azure-redis.redis.cache.windows.net
REDIS_PORT=6380
REDIS_DB=0
REDIS_SSL=true
GITHUB_TOKEN=ghp_your_token
MCP_API_KEY=your_strong_secret_key_here
MCP_HTTP_PORT=3001
MCP_HTTP_HOST=0.0.0.0
```

### 2. Cursor MCP Konfiguráció (Azure)

Frissítsd a `~/.cursor/mcp.json` fájlt:

```json
{
  "mcpServers": {
    "intracker": {
      "url": "https://your-app.azurewebsites.net/mcp/sse",
      "headers": {
        "X-API-Key": "your_strong_secret_key_here"
      }
    }
  }
}
```

### 3. API Key Biztonság

**NE tedd a kulcsot a konfigurációba!** Használd a Cursor environment változókat vagy Key Vault-ot:

```json
{
  "mcpServers": {
    "intracker": {
      "url": "https://your-app.azurewebsites.net/mcp/sse",
      "headers": {
        "X-API-Key": "${MCP_API_KEY}"
      }
    }
  }
}
```

## Connection String Formátum

### Lokális (Docker)
```
http://localhost:3001/mcp/sse
```

### Azure (Production)
```
https://intracker-mcp.azurewebsites.net/mcp/sse
```

### Azure (Staging)
```
https://intracker-mcp-staging.azurewebsites.net/mcp/sse
```

## API Key Generálás

Erős API kulcs generálása:

```bash
# Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

## Troubleshooting

### Kapcsolat megszakad

1. **Ellenőrizd a health endpoint-ot:**
   ```bash
   curl https://your-app.azurewebsites.net/health
   ```

2. **Ellenőrizd az API kulcsot:**
   ```bash
   curl -H "X-API-Key: your_key" https://your-app.azurewebsites.net/health
   ```

3. **Nézd meg a logokat:**
   ```bash
   az webapp log tail --name your-app --resource-group your-rg
   ```

### 401 Unauthorized

- Ellenőrizd, hogy az API kulcs helyes-e
- Ellenőrizd, hogy a `X-API-Key` header be van-e állítva
- Azure-ban ellenőrizd az environment változókat

### Connection Timeout

- Ellenőrizd a firewall szabályokat
- Ellenőrizd, hogy a port (3001) nyitva van-e
- Azure-ban ellenőrizd a Network Security Groups-ot

## Security Best Practices

1. **API Key Management:**
   - Használj Azure Key Vault-ot
   - Rotálj rendszeresen a kulcsokat
   - Ne commitold a kulcsokat a git-be

2. **HTTPS:**
   - Mindig használj HTTPS-t production-ban
   - Azure App Service automatikusan biztosít SSL-t

3. **Rate Limiting:**
   - Implementálj rate limiting-et (jövőbeli fejlesztés)
   - Használj Azure Application Gateway-t

4. **Monitoring:**
   - Használj Azure Application Insights-t
   - Figyeld a kapcsolati hibákat
   - Állíts be alert-eket

## Migration Path

### Fázis 1: Lokális Tesztelés (Most)
- Docker-ben fut
- `http://localhost:3001`
- API key: `test`

### Fázis 2: Azure Staging
- Azure App Service (staging slot)
- `https://intracker-mcp-staging.azurewebsites.net`
- Erős API key

### Fázis 3: Azure Production
- Azure App Service (production slot)
- `https://intracker-mcp.azurewebsites.net`
- Production API key (Key Vault-ból)

## További Információk

- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [InTracker Architecture](./architecture.md)
