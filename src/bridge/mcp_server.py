"""MCP Server for SPACO.

This module provides a server for handling MCP requests from Claude Desktop.
"""

import json
import logging
import asyncio
from aiohttp import web

class MCPServer:
    """
    Server for handling MCP requests from Claude Desktop.
    
    This class provides a server that accepts MCP requests from Claude Desktop,
    processes them, and returns responses.
    """
    
    def __init__(self, host="localhost", port=8080):
        """
        Initialize an MCPServer.
        
        Args:
            host (str): Host to listen on
            port (int): Port to listen on
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.handlers = {}
        self.logger = self._setup_logger()
        
        # Set up routes
        self.app.router.add_post('/mcp', self.handle_mcp_request)
        self.app.router.add_get('/status', self.handle_status)
    
    def _setup_logger(self):
        """Set up logger for the server."""
        logger = logging.getLogger('mcp_server')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def register_handler(self, action_type, handler):
        """
        Register a handler for an action type.
        
        Args:
            action_type (str): The action type to handle
            handler (callable): The handler function
        """
        self.handlers[action_type] = handler
        self.logger.info(f"Registered handler for action type: {action_type}")
    
    async def handle_mcp_request(self, request):
        """
        Handle an MCP request.
        
        Args:
            request: The web request
        
        Returns:
            web.Response: The response
        """
        try:
            # Parse request body as JSON
            body = await request.json()
            self.logger.info(f"Received MCP request: {body}")
            
            # Check if the request is valid
            if 'action' not in body:
                return self._error_response("Missing 'action' field in request")
            
            action = body['action']
            
            # Check if there's a handler for this action
            if action not in self.handlers:
                return self._error_response(f"No handler for action: {action}")
            
            # Call the handler
            handler = self.handlers[action]
            result = await handler(body)
            
            # Return the result
            return web.json_response({
                "status": "success",
                "result": result
            })
            
        except json.JSONDecodeError:
            return self._error_response("Invalid JSON in request body")
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return self._error_response(f"Internal server error: {str(e)}")
    
    async def handle_status(self, request):
        """
        Handle a status request.
        
        Args:
            request: The web request
        
        Returns:
            web.Response: The response
        """
        return web.json_response({
            "status": "running",
            "handlers": list(self.handlers.keys())
        })
    
    def _error_response(self, message):
        """
        Create an error response.
        
        Args:
            message (str): The error message
        
        Returns:
            web.Response: The error response
        """
        self.logger.error(message)
        return web.json_response({
            "status": "error",
            "message": message
        }, status=400)
    
    def start(self):
        """Start the server."""
        self.logger.info(f"Starting MCP server on {self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port)
    
    async def start_async(self):
        """Start the server asynchronously."""
        self.logger.info(f"Starting MCP server on {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        return runner
