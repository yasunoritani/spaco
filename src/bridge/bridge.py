"""SPACO Bridge for connecting Claude Desktop with SuperCollider.

This module provides the main bridge component that connects
Claude Desktop with SuperCollider using the MCP protocol.
"""

import logging
import asyncio
from .mcp_server import MCPServer
from .handlers.sound_handler import SoundHandler

class SPACOBridge:
    """
    Main bridge connecting Claude Desktop with SuperCollider.
    
    This class sets up and manages the connection between Claude Desktop
    and SuperCollider, handling MCP requests and responses.
    """
    
    def __init__(self, host="localhost", port=8080, sc_interface=None):
        """
        Initialize a SPACOBridge.
        
        Args:
            host (str): Host for the MCP server
            port (int): Port for the MCP server
            sc_interface: Interface to SuperCollider
        """
        self.logger = self._setup_logger()
        self.mcp_server = MCPServer(host, port)
        self.sc_interface = sc_interface
        
        # Set up handlers
        self.sound_handler = SoundHandler(sc_interface)
        
        # Register handlers with the MCP server
        self._register_handlers()
    
    def _setup_logger(self):
        """Set up logger for the bridge."""
        logger = logging.getLogger('spaco_bridge')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def _register_handlers(self):
        """Register handlers with the MCP server."""
        # Sound-related handlers
        self.mcp_server.register_handler('generate_sound', self.sound_handler.handle_generate_sound)
        self.mcp_server.register_handler('stop_sound', self.sound_handler.handle_stop_sound)
    
    def start(self):
        """Start the bridge."""
        self.logger.info("Starting SPACO Bridge")
        try:
            self.mcp_server.start()
        except KeyboardInterrupt:
            self.logger.info("Stopping SPACO Bridge")
    
    async def start_async(self):
        """Start the bridge asynchronously."""
        self.logger.info("Starting SPACO Bridge asynchronously")
        return await self.mcp_server.start_async()
    
    def stop(self):
        """Stop the bridge."""
        self.logger.info("Stopping SPACO Bridge")
        # Additional cleanup if needed
