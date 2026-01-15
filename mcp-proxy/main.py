"""MCP Proxy Service - Stable middleware for MCP connections.

This proxy sits between Cursor and the InTracker backend MCP server,
providing automatic reconnection and zero-downtime backend restarts.

Architecture:
    Cursor → MCP Proxy (always running) → Backend (restartable)
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Set
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp-proxy")

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
BACKEND_MCP_ENDPOINT = f"{BACKEND_URL}/mcp/sse"
BACKEND_MESSAGES_ENDPOINT = f"{BACKEND_URL}/mcp/messages"
PROXY_PORT = int(os.getenv("PROXY_PORT", "8001"))
MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "10"))
RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "2"))  # seconds

# Global state
active_connections: Dict[str, dict] = {}  # client_id -> connection_info
backend_health_status = {"healthy": False, "last_check": None}


class BackendConnectionManager:
    """Manages backend connections with automatic retry logic."""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def connect_with_retry_stream(
        self, 
        endpoint: str, 
        headers: dict,
        max_attempts: int = MAX_RECONNECT_ATTEMPTS,
        delay: int = RECONNECT_DELAY
    ):
        """Connect to backend with automatic retry on failure (streaming mode).
        
        Args:
            endpoint: Backend endpoint URL
            headers: Request headers (including API key)
            max_attempts: Maximum number of connection attempts
            delay: Delay between attempts in seconds
            
        Yields:
            bytes: SSE event data from backend stream
            
        Raises:
            HTTPException: If all connection attempts fail
        """
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 Connecting to backend (attempt {attempt}/{max_attempts}): {endpoint}")
                
                # Use streaming mode to avoid timeout on long-lived SSE connections
                async with self.client.stream(
                    "GET",
                    endpoint,
                    headers=headers,
                    timeout=60.0,  # 60s timeout for connection establishment (backend may be slow to respond)
                ) as response:
                    if response.status_code == 200:
                        logger.info(f"✅ Connected to backend successfully, starting stream...")
                        backend_health_status["healthy"] = True
                        backend_health_status["last_check"] = datetime.utcnow()
                        
                        # Stream data from backend
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                # IMPORTANT: Rewrite endpoint event to point to proxy, not backend
                                # The MCP SDK sends an "endpoint" event with the messages URL
                                # We need to rewrite it so Cursor sends messages to the proxy
                                try:
                                    chunk_str = chunk.decode('utf-8')
                                    if 'event: endpoint' in chunk_str or '"endpoint"' in chunk_str:
                                        # Replace backend URL with proxy URL in endpoint events
                                        chunk_str = chunk_str.replace('/mcp/messages/', f'http://localhost:{PROXY_PORT}/mcp/messages/')
                                        chunk_str = chunk_str.replace('http://intracker-backend:3000/mcp/messages/', f'http://localhost:{PROXY_PORT}/mcp/messages/')
                                        chunk = chunk_str.encode('utf-8')
                                except:
                                    pass  # If decode fails, just pass through original chunk
                                
                                yield chunk
                        
                        # Stream ended normally
                        logger.info(f"📭 Backend stream ended normally")
                        return
                    else:
                        logger.warning(f"⚠️  Backend returned status {response.status_code}")
                        last_error = f"Backend returned status {response.status_code}"
                    
            except Exception as e:
                logger.warning(f"❌ Connection attempt {attempt} failed: {e}")
                last_error = str(e)
                backend_health_status["healthy"] = False
                backend_health_status["last_check"] = datetime.utcnow()
            
            # Wait before next attempt (unless this is the last attempt)
            if attempt < max_attempts:
                logger.info(f"⏳ Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error(f"💥 Failed to connect to backend after {max_attempts} attempts")
        raise HTTPException(
            status_code=503,
            detail=f"Backend unavailable: {last_error}"
        )
    
    async def stream_from_backend(
        self,
        endpoint: str,
        headers: dict,
        client_id: str
    ):
        """Stream events from backend with automatic reconnection.
        
        Yields:
            bytes: SSE event data from backend
        """
        reconnect_count = 0
        
        while True:
            try:
                # Connect to backend and stream (with automatic retry)
                async for chunk in self.connect_with_retry_stream(endpoint, headers):
                    if chunk:
                        yield chunk
                        # Reset reconnect count on successful data
                        reconnect_count = 0
                
                # Stream ended - backend restarted or connection lost
                # Automatically reconnect to maintain client connection
                reconnect_count += 1
                logger.info(
                    f"📭 Backend stream ended for client {client_id}, "
                    f"reconnecting (attempt #{reconnect_count})..."
                )
                
                if reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"💥 Max reconnect attempts reached for client {client_id}")
                    raise HTTPException(
                        status_code=503,
                        detail="Backend connection lost and reconnection failed"
                    )
                
                # Wait before reconnecting
                await asyncio.sleep(RECONNECT_DELAY)
                # Continue while loop to reconnect
                
            except HTTPException as e:
                # Backend unavailable - propagate error
                logger.error(f"🚨 Backend unavailable for client {client_id}: {e.detail}")
                raise
                
            except Exception as e:
                # Connection lost - try to reconnect
                reconnect_count += 1
                logger.warning(
                    f"⚠️  Connection lost for client {client_id} "
                    f"(reconnect #{reconnect_count}): {e}"
                )
                
                if reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"💥 Max reconnect attempts reached for client {client_id}")
                    raise HTTPException(
                        status_code=503,
                        detail="Backend connection lost and reconnection failed"
                    )
                
                # Wait before reconnecting
                await asyncio.sleep(RECONNECT_DELAY)
                logger.info(f"🔄 Attempting to reconnect for client {client_id}...")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Initialize backend connection manager
backend_manager = BackendConnectionManager(BACKEND_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("🚀 MCP Proxy starting up...")
    logger.info(f"   Backend URL: {BACKEND_URL}")
    logger.info(f"   Proxy Port: {PROXY_PORT}")
    logger.info(f"   Max Reconnect Attempts: {MAX_RECONNECT_ATTEMPTS}")
    logger.info(f"   Reconnect Delay: {RECONNECT_DELAY}s")
    
    yield
    
    # Shutdown
    logger.info("🛑 MCP Proxy shutting down...")
    await backend_manager.close()
    logger.info(f"   Total clients served: {len(active_connections)}")


# Create FastAPI app
app = FastAPI(
    title="MCP Proxy",
    description="Stable middleware for MCP connections with automatic reconnection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for proxy and backend."""
    return {
        "status": "ok",
        "proxy": {
            "healthy": True,
            "active_connections": len(active_connections),
        },
        "backend": {
            "url": BACKEND_URL,
            "healthy": backend_health_status["healthy"],
            "last_check": backend_health_status["last_check"].isoformat() 
                         if backend_health_status["last_check"] else None,
        }
    }


@app.get("/mcp/sse")
@app.post("/mcp/sse")
async def mcp_sse_proxy(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Proxy SSE endpoint for MCP connections.
    
    Supports both GET (SSE) and POST (Streamable HTTP) methods.
    Cursor tries POST first (Streamable HTTP), then falls back to GET (SSE).
    
    This endpoint:
    1. Accepts connections from MCP clients (Cursor)
    2. Forwards connections to backend MCP server
    3. Automatically reconnects on backend restart
    4. Maintains client connection throughout
    """
    # Generate client ID
    client_id = f"client_{id(request)}_{datetime.utcnow().timestamp()}"
    
    logger.info(f"🆕 New client connection: {client_id}")
    
    # Validate API key
    if not x_api_key:
        logger.warning(f"⚠️  Client {client_id} missing API key")
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # Store connection info
    active_connections[client_id] = {
        "connected_at": datetime.utcnow(),
        "api_key": x_api_key[:12] + "...",  # Store prefix only
    }
    
    # Forward headers to backend
    backend_headers = {
        "X-API-Key": x_api_key,
        "User-Agent": request.headers.get("User-Agent", "MCP-Proxy/1.0"),
    }
    
    async def event_stream():
        """Stream events from backend to client with reconnection."""
        try:
            async for chunk in backend_manager.stream_from_backend(
                BACKEND_MCP_ENDPOINT,
                backend_headers,
                client_id
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Stream error for client {client_id}: {e}")
            # Send error event to client
            error_message = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield error_message.encode()
            
        finally:
            # Cleanup
            if client_id in active_connections:
                del active_connections[client_id]
            logger.info(f"🔌 Client disconnected: {client_id}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/mcp/messages/{path:path}")
async def mcp_messages_proxy(
    path: str,
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Proxy POST requests to backend MCP messages endpoint."""
    
    # Validate API key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # Forward to backend - IMPORTANT: Include query string!
    backend_url = f"{BACKEND_MESSAGES_ENDPOINT}/{path}"
    if request.url.query:
        backend_url = f"{backend_url}?{request.url.query}"
    
    backend_headers = {
        "X-API-Key": x_api_key,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
    }
    
    try:
        body = await request.body()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                backend_url,
                headers=backend_headers,
                content=body,
                timeout=30.0
            )
            
            # Handle empty response body (e.g., 202 Accepted with no content)
            response_content = {}
            if response.text:
                try:
                    response_content = response.json()
                except Exception:
                    # If JSON parsing fails, return empty dict (valid for 202 Accepted)
                    pass
            
            return JSONResponse(
                content=response_content,
                status_code=response.status_code
            )
            
    except Exception as e:
        logger.error(f"❌ Failed to forward POST request: {e}")
        raise HTTPException(status_code=503, detail=f"Backend unavailable: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "MCP Proxy",
        "version": "1.0.0",
        "status": "running",
        "backend_url": BACKEND_URL,
        "active_connections": len(active_connections),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PROXY_PORT,
        reload=False,  # Disable reload for stability
        log_level="info"
    )
