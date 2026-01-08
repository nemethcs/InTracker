# Azure MCP Server Csatlakozás - Útmutató

## Áttekintés

Az InTracker MCP szerver a **backend Container App-ben** van integrálva, nem külön szolgáltatásként. A Cursor HTTP/SSE transport-tal csatlakozik az Azure-beli MCP szerverhez.

## Architektúra

```
┌─────────────┐
│   Cursor    │
│  (Local)    │
└──────┬──────┘
       │ HTTPS/SSE
       │ + API Key (X-API-Key header)
       ↓
┌─────────────────────────────────────────┐
│  Azure Container Apps                   │
│  intracker-api                          │
│  https://intracker-api.kesmarki.com     │
│  └── /mcp/sse (MCP SSE endpoint)       │
│  └── /mcp/health (Health check)         │
└──────┬──────────────────────────────────┘
       │
       ├──→ PostgreSQL (Azure Database)
       ├──→ Redis (Azure Cache)
       └──→ GitHub API
```

## MCP Endpoint Információk

### Production URL
```
https://intracker-api.kesmarki.com/mcp/sse
```

### Health Check
```
https://intracker-api.kesmarki.com/mcp/health
```

## Cursor MCP Konfiguráció

### 1. MCP API Key lekérése

**Opció A: Azure Key Vault-ból (Ajánlott)**

```bash
# Azure CLI-vel
az keyvault secret show \
  --vault-name "intracker-kv" \
  --name "mcp-api-key" \
  --query "value" \
  -o tsv
```

**Opció B: Container App environment változóból**

```bash
# Azure CLI-vel
az containerapp show \
  --name "intracker-api" \
  --resource-group "intracker-rg-poland" \
  --query "properties.template.containers[0].env[?name=='MCP_API_KEY'].value" \
  -o tsv
```

**Opció C: Azure Portal-ban**

Key Vault:
1. Nyisd meg az `intracker-kv` Key Vault-ot
2. Secrets → `mcp-api-key`
3. Kattints a "Show Secret Value" gombra

Container App:
1. Nyisd meg az `intracker-api` Container App-et
2. Settings → Environment variables
3. Keress rá: `MCP_API_KEY`

### 2. Cursor MCP Konfiguráció

Frissítsd a `~/.cursor/mcp.json` fájlt:

```json
{
  "mcpServers": {
    "intracker": {
      "url": "https://intracker-api.kesmarki.com/mcp/sse",
      "headers": {
        "X-API-Key": "YOUR_MCP_API_KEY_HERE"
      }
    }
  }
}
```

**⚠️ FONTOS:**
- Cseréld le a `YOUR_MCP_API_KEY_HERE`-t a tényleges API kulcsra
- **NE commitold** a kulcsot a git-be!
- Használj environment változót vagy Key Vault-ot

### 3. Environment változó használata (Ajánlott)

Ha nem akarod a kulcsot közvetlenül a konfigurációba írni:

```json
{
  "mcpServers": {
    "intracker": {
      "url": "https://intracker-api.kesmarki.com/mcp/sse",
      "headers": {
        "X-API-Key": "${MCP_API_KEY}"
      }
    }
  }
}
```

És állítsd be az environment változót:

```bash
# macOS/Linux
export MCP_API_KEY="your_key_here"

# Windows (PowerShell)
$env:MCP_API_KEY="your_key_here"
```

## Tesztelés

### 1. Health Check

```bash
curl https://intracker-api.kesmarki.com/mcp/health
```

Válasz:
```json
{
  "status": "ok",
  "service": "intracker-mcp-server"
}
```

### 2. API Key ellenőrzés

```bash
curl -H "X-API-Key: YOUR_MCP_API_KEY" \
  https://intracker-api.kesmarki.com/mcp/health
```

### 3. Cursor-ban ellenőrzés

1. Nyisd meg a Cursor-t
2. Nyisd meg a Command Palette-t: `Cmd+Shift+P` (macOS) vagy `Ctrl+Shift+P` (Windows/Linux)
3. Keress rá: **"MCP"** vagy **"Model Context Protocol"**
4. Nézd meg a **"MCP Servers"** listát
5. Az **"intracker"** szervernak **"Connected"** státuszban kell lennie

### 4. MCP Tools tesztelése

A Cursor AI-ben próbáld ki:

```
"Kérlek, listázd az InTracker projekteket"
"Mutasd meg a GitHub Integration Test feature-t"
"Hozz létre egy új todo-t a GitHub Integration Test feature-hez"
```

## Troubleshooting

### Hiba: "Connection refused" vagy "Connection timeout"

**Ok:** A Container App nem elérhető vagy a port nincs nyitva.

**Megoldás:**
1. Ellenőrizd a Container App állapotát:
   ```bash
   az containerapp show \
     --name "intracker-api" \
     --resource-group "intracker-rg-poland" \
     --query "properties.runningStatus" \
     -o tsv
   ```

2. Ellenőrizd a logokat:
   ```bash
   az containerapp logs show \
     --name "intracker-api" \
     --resource-group "intracker-rg-poland" \
     --tail 50 \
     --type console
   ```

3. Teszteld a health endpoint-ot:
   ```bash
   curl https://intracker-api.kesmarki.com/mcp/health
   ```

### Hiba: "401 Unauthorized"

**Ok:** Az API kulcs helytelen vagy hiányzik.

**Megoldás:**
1. Ellenőrizd, hogy az `X-API-Key` header be van-e állítva
2. Ellenőrizd az API kulcsot Azure-ban:
   ```bash
   az containerapp show \
     --name "intracker-api" \
     --resource-group "intracker-rg-poland" \
     --query "properties.template.containers[0].env[?name=='MCP_API_KEY'].value" \
     -o tsv
   ```
3. Frissítsd a `~/.cursor/mcp.json` fájlt a helyes kulccsal
4. Indítsd újra a Cursor-t

### Hiba: "MCP Server not found"

**Ok:** A konfigurációs fájl helytelen vagy hiányzik.

**Megoldás:**
1. Ellenőrizd a `~/.cursor/mcp.json` fájl elérési útját
2. Ellenőrizd, hogy a `url` helyes-e
3. Indítsd újra a Cursor-t

### Hiba: "Database connection failed"

**Ok:** Az Azure PostgreSQL nem elérhető a Container App-ből.

**Megoldás:**
1. Ellenőrizd a firewall szabályokat:
   ```bash
   az postgres flexible-server firewall-rule list \
     --resource-group "intracker-rg-poland" \
     --name "intracker-db" \
     --output table
   ```

2. Ellenőrizd, hogy az "AllowAzureServices" szabály létezik-e (0.0.0.0 - 0.0.0.0)

## Security Best Practices

1. **API Key Management:**
   - Használj Azure Key Vault-ot a kulcs tárolásához
   - Rotálj rendszeresen a kulcsokat
   - **NE commitold** a kulcsokat a git-be

2. **HTTPS:**
   - Mindig használj HTTPS-t (Azure automatikusan biztosít SSL-t)
   - A custom domain (`intracker-api.kesmarki.com`) SSL-t használ

3. **Rate Limiting:**
   - Implementálj rate limiting-et (jövőbeli fejlesztés)
   - Használj Azure Application Gateway-t

4. **Monitoring:**
   - Használj Azure Application Insights-t
   - Figyeld a kapcsolati hibákat
   - Állíts be alert-eket

## Lokális vs Azure

### Lokális fejlesztés
```json
{
  "mcpServers": {
    "intracker": {
      "url": "http://localhost:3000/mcp/sse",
      "headers": {
        "X-API-Key": "test"
      }
    }
  }
}
```

### Azure Production
```json
{
  "mcpServers": {
    "intracker": {
      "url": "https://intracker-api.kesmarki.com/mcp/sse",
      "headers": {
        "X-API-Key": "${MCP_API_KEY}"
      }
    }
  }
}
```

## További Információk

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [InTracker Architecture](./architecture.md)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
