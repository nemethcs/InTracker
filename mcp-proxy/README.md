# MCP Proxy Service

Stable middleware for MCP (Model Context Protocol) connections with automatic reconnection.

## Architecture

```
Cursor Desktop
    ↓ SSE/HTTP
MCP Proxy (always running)
    ↓ SSE/HTTP (with auto-reconnect)
Backend MCP Server (restartable)
```

## Features

- ✅ **Automatic Reconnection**: Reconnects to backend on restart without client disconnect
- ✅ **Zero-Downtime**: Backend can restart while Cursor connection stays active
- ✅ **Connection Pooling**: Manages multiple client connections
- ✅ **Health Monitoring**: Health check endpoints for proxy and backend
- ✅ **Retry Logic**: Configurable retry attempts and delays
- ✅ **Logging**: Detailed connection and error logging

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   cd mcp-proxy
   pip install -r requirements.txt
   ```

2. **Configure environment** (create `.env` file):
   ```bash
   BACKEND_URL=http://localhost:3000
   PROXY_PORT=8001
   MAX_RECONNECT_ATTEMPTS=10
   RECONNECT_DELAY=2
   ```

3. **Run proxy**:
   ```bash
   python main.py
   ```

4. **Update Cursor config** (`~/.cursor/mcp.json`):
   ```json
   {
     "mcpServers": {
       "intracker": {
         "url": "http://localhost:8001/mcp/sse",
         "headers": {
           "X-API-Key": "your_api_key"
         }
       }
     }
   }
   ```

### Docker

1. **Build image**:
   ```bash
   docker build -t intracker-mcp-proxy:latest .
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name mcp-proxy \
     -p 8001:8001 \
     -e BACKEND_URL=http://backend:3000 \
     intracker-mcp-proxy:latest
   ```

### Docker Compose

See `docker-compose.yml` in project root for full configuration.

## Endpoints

### `GET /health`
Health check for proxy and backend status.

**Response**:
```json
{
  "status": "ok",
  "proxy": {
    "healthy": true,
    "active_connections": 3
  },
  "backend": {
    "url": "http://backend:3000",
    "healthy": true,
    "last_check": "2026-01-15T10:30:00"
  }
}
```

### `GET /mcp/sse`
SSE endpoint for MCP connections (proxied to backend).

**Headers**:
- `X-API-Key`: InTracker MCP API key

### `POST /mcp/messages/{path}`
POST endpoint for MCP messages (proxied to backend).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:3000` | Backend MCP server URL |
| `PROXY_PORT` | `8001` | Proxy service port |
| `MAX_RECONNECT_ATTEMPTS` | `10` | Max backend reconnection attempts |
| `RECONNECT_DELAY` | `2` | Delay between reconnect attempts (seconds) |

## How It Works

### Normal Operation

```
1. Cursor connects to proxy (/mcp/sse)
2. Proxy connects to backend
3. Events stream bidirectionally
4. Everything works normally
```

### Backend Restart Scenario

```
1. Cursor → Proxy (connection alive)
2. Backend restarts (connection lost)
3. Proxy detects disconnect
4. Proxy waits RECONNECT_DELAY seconds
5. Proxy attempts to reconnect (retry logic)
6. Backend comes back online
7. Proxy reconnects successfully
8. Events resume streaming
9. ✅ Cursor never disconnected!
```

### Connection Flow

```python
# Pseudo-code of proxy logic
async def stream_from_backend():
    reconnect_count = 0
    
    while True:
        try:
            # Connect to backend with retry
            response = await connect_with_retry(backend_url)
            
            # Stream events
            async for chunk in response:
                yield chunk  # Forward to Cursor
            
            break  # Stream ended normally
            
        except ConnectionError:
            # Backend disconnected
            reconnect_count += 1
            
            if reconnect_count < MAX_ATTEMPTS:
                await sleep(RECONNECT_DELAY)
                continue  # Retry
            else:
                raise  # Give up
```

## Monitoring

### Logs

```bash
# View proxy logs
docker logs -f mcp-proxy

# Example output:
🚀 MCP Proxy starting up...
🆕 New client connection: client_12345
✅ Connected to backend successfully
🔄 Backend stream ended
⚠️  Connection lost (reconnect #1)
🔄 Attempting to reconnect...
✅ Connected to backend successfully
```

### Health Check

```bash
# Check proxy health
curl http://localhost:8001/health

# Check backend connectivity
curl http://localhost:8001/health | jq '.backend'
```

## Troubleshooting

### Proxy can't connect to backend

**Symptom**: `503 Backend unavailable`

**Solutions**:
1. Check backend is running: `curl http://localhost:3000/health`
2. Check network connectivity (Docker network for containers)
3. Verify `BACKEND_URL` environment variable

### Cursor can't connect to proxy

**Symptom**: MCP shows "Disconnected"

**Solutions**:
1. Check proxy is running: `curl http://localhost:8001/health`
2. Verify Cursor config URL: `http://localhost:8001/mcp/sse`
3. Check API key is correct

### Reconnection not working

**Symptom**: Connection dies on backend restart

**Solutions**:
1. Check `MAX_RECONNECT_ATTEMPTS` is sufficient
2. Increase `RECONNECT_DELAY` if backend takes time to start
3. Check logs for reconnection attempts

## Development

### Run tests

```bash
# TODO: Add tests
pytest tests/
```

### Code structure

```
mcp-proxy/
├── main.py              # Main proxy service
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker image
├── .env.example        # Environment template
└── README.md          # This file
```

## Production Deployment

### Azure Container App

1. **Build and push image**:
   ```bash
   az acr build \
     --registry intrackeracr \
     --image intracker-mcp-proxy:latest \
     --file Dockerfile .
   ```

2. **Deploy container app**:
   ```bash
   az containerapp create \
     --name mcp-proxy \
     --resource-group intracker-rg \
     --environment intracker-env \
     --image intrackeracr.azurecr.io/intracker-mcp-proxy:latest \
     --target-port 8001 \
     --ingress external \
     --min-replicas 1 \
     --max-replicas 3 \
     --env-vars \
       BACKEND_URL=http://intracker-backend:3000 \
       MAX_RECONNECT_ATTEMPTS=10 \
       RECONNECT_DELAY=2
   ```

3. **Update Cursor config** for production:
   ```json
   {
     "mcpServers": {
       "intracker_prod": {
         "url": "https://mcp-proxy.kesmarki.com/mcp/sse",
         "headers": {
           "X-API-Key": "your_production_api_key"
         }
       }
     }
   }
   ```

## License

MIT License - see LICENSE file in project root.
