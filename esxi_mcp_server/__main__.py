"""Main entry point for running ESXi MCP Server as a module."""

import os
import argparse
import logging
import anyio
import uvicorn

from mcp.server import stdio

from . import load_config, VMwareManager, ToolHandlers, create_mcp_server, register_handlers
from .transport import create_asgi_app


def setup_logging(config):
    """Configure logging based on configuration."""
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        filename=config.log_file if config.log_file else None
    )
    if not config.log_file:
        # If no log file is specified, output logs to the console
        logging.getLogger().addHandler(logging.StreamHandler())


def main():
    """Main entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MCP VMware ESXi Management Server")
    parser.add_argument("--config", "-c", help="Configuration file path (JSON or YAML)", default=None)
    parser.add_argument("--transport", "-t", choices=["stdio", "http"], default="http",
                        help="Transport mode: 'stdio' for stdin/stdout communication (default: http)")
    args = parser.parse_args()
    
    # Load configuration
    config_path = args.config or os.environ.get("MCP_CONFIG_FILE")
    config = load_config(config_path)
    
    # Initialize logging
    setup_logging(config)
    
    logging.info("Starting VMware ESXi Management MCP Server...")
    
    # Create VMware Manager instance and connect
    manager = VMwareManager(config)
    
    # If an API key is configured, prompt that authentication is required before invoking sensitive operations
    if config.api_key:
        logging.info("API key authentication is enabled. Clients must call the authenticate tool to verify the key before invoking sensitive operations")
    
    # Create tool handlers and MCP server
    tool_handlers = ToolHandlers(manager, config)
    mcp_server = create_mcp_server()
    register_handlers(mcp_server, tool_handlers)
    
    # Start MCP server with the selected transport
    if args.transport == "stdio":
        # Run with stdio transport (stdin/stdout communication)
        logging.info("Starting MCP server with stdio transport")
        
        async def run_stdio():
            async with stdio.stdio_server() as (read_stream, write_stream):
                init_opts = mcp_server.create_initialization_options()
                await mcp_server.run(read_stream, write_stream, init_opts)
        
        anyio.run(run_stdio)
    else:
        # Run with HTTP transport (default)
        logging.info("Starting MCP server with HTTP transport on 0.0.0.0:8080")
        
        # Create ASGI app
        import asyncio
        app = asyncio.run(create_asgi_app(mcp_server, config))
        uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
