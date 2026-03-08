"""Transport layer for MCP server (HTTP and stdio)."""

import asyncio
import logging
from typing import Optional

from mcp.server.streamable_http import StreamableHTTPServerTransport

from .config import Config


# Maintain a global StreamableHTTP transport instance
streamable_http_transport: Optional[StreamableHTTPServerTransport] = None
streamable_http_task: Optional[asyncio.Task] = None
streamable_http_lock = asyncio.Lock()


async def streamable_http_endpoint(scope, receive, send, mcp_server, config: Config):
    """Handle streamable-http MCP requests."""
    global streamable_http_transport, streamable_http_task
    
    # Verify API key if configured
    headers_dict = {k.lower().decode(): v.decode() for (k, v) in scope.get("headers", [])}
    provided_key = None
    # Check if authorization or x-api-key headers are present in the decoded headers_dict
    if "authorization" in headers_dict:
        auth_header = headers_dict.get("authorization", "").strip()
        # Extract token from "Bearer <token>" format (standard) or use direct token (fallback)
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()  # Remove "Bearer " prefix and any extra whitespace
        elif auth_header:
            # Support direct token in Authorization header for backward compatibility
            provided_key = auth_header
    elif "x-api-key" in headers_dict:
        provided_key = headers_dict.get("x-api-key", "").strip()
    
    if config.api_key and provided_key != config.api_key:
        # If the correct API key is not provided, return 401
        await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"Unauthorized"})
        logging.warning("Invalid API key provided, rejecting streamable-http connection")
        return
    
    # Create transport instance if it doesn't exist (with proper locking to avoid race conditions)
    async with streamable_http_lock:
        if streamable_http_transport is None:
            # Initialize the StreamableHTTPServerTransport
            # - mcp_session_id=None: No specific session ID, letting the transport manage session state
            # - is_json_response_enabled=False: Use SSE streaming for responses (MCP standard)
            streamable_http_transport = StreamableHTTPServerTransport(
                mcp_session_id=None,
                is_json_response_enabled=False
            )
            logging.info("Created new StreamableHTTPServerTransport instance")
            
            # Start the MCP server with the transport in the background
            async def run_mcp_server():
                try:
                    async with streamable_http_transport.connect() as (read_stream, write_stream):
                        init_opts = mcp_server.create_initialization_options()
                        logging.info("Starting MCP server with streamable-http transport")
                        await mcp_server.run(read_stream, write_stream, init_opts)
                except asyncio.CancelledError:
                    logging.info("MCP server task cancelled, shutting down gracefully")
                    raise
                except Exception as e:
                    logging.error(f"MCP server runtime error: {type(e).__name__}: {e}", exc_info=True)
            
            # Start the MCP server task and keep a reference to prevent garbage collection
            streamable_http_task = asyncio.create_task(run_mcp_server())
    
    # Handle the request through the StreamableHTTPServerTransport
    try:
        await streamable_http_transport.handle_request(scope, receive, send)
    except Exception as e:
        logging.error(f"Error handling streamable-http request: {type(e).__name__}: {e}")
        # Only attempt to send error response if we haven't started sending a response yet
        # Note: ASGI spec requires checking state internally; we catch and log any errors
        try:
            await send({"type": "http.response.start", "status": 500,
                        "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": str(e).encode('utf-8')})
        except Exception:
            # Response already started, can't send error response
            pass


async def create_asgi_app(mcp_server, config: Config):
    """
    Create ASGI application routing.
    
    Dispatch requests to the appropriate handler based on the path and method.
    """
    async def app(scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "").upper()
            if path == "/mcp" and method in ("GET", "POST", "OPTIONS"):
                # Streamable HTTP endpoint for MCP
                if method == "OPTIONS":
                    # Return allowed methods for CORS
                    headers = [
                        (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                        (b"access-control-allow-headers", b"Content-Type, Authorization, X-API-Key, MCP-Session-Id"),
                        (b"access-control-allow-origin", b"*")
                    ]
                    await send({"type": "http.response.start", "status": 204, "headers": headers})
                    await send({"type": "http.response.body", "body": b""})
                else:
                    await streamable_http_endpoint(scope, receive, send, mcp_server, config)
            else:
                # Route not found
                await send({"type": "http.response.start", "status": 404,
                            "headers": [(b"content-type", b"text/plain")]})
                await send({"type": "http.response.body", "body": b"Not Found"})
        else:
            # Non-HTTP event, do not process
            return
    
    return app
