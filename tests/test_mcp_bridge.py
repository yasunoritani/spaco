"""Tests for MCP Bridge.

This module contains tests for the MCP Bridge component.
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.bridge.mcp_server import MCPServer
from src.bridge.bridge import SPACOBridge
from src.bridge.handlers.sound_handler import SoundHandler
from src.bridge.response_generator import ResponseGenerator

class TestMCPServer(unittest.TestCase):
    """Tests for MCPServer class."""
    
    def setUp(self):
        """Set up the test case."""
        self.server = MCPServer(host="localhost", port=8080)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.server.host, "localhost")
        self.assertEqual(self.server.port, 8080)
        self.assertIsInstance(self.server.app, web.Application)
        self.assertEqual(self.server.handlers, {})
    
    def test_register_handler(self):
        """Test registering a handler."""
        handler = Mock()
        self.server.register_handler("test_action", handler)
        self.assertEqual(self.server.handlers["test_action"], handler)
    
    @patch('aiohttp.web.json_response')
    def test_error_response(self, mock_json_response):
        """Test error response generation."""
        self.server._error_response("Test error")
        mock_json_response.assert_called_once_with({
            "status": "error",
            "message": "Test error"
        }, status=400)


class TestSoundHandler(unittest.TestCase):
    """Tests for SoundHandler class."""
    
    def setUp(self):
        """Set up the test case."""
        self.sc_interface = Mock()
        self.handler = SoundHandler(self.sc_interface)
    
    @patch('logging.Logger.info')
    async def test_handle_generate_sound(self, mock_logger):
        """Test handling a generate_sound request."""
        request = {
            "instruction": "Generate a 440Hz sine wave",
            "parameters": {
                "frequency": 440,
                "amplitude": 0.5,
                "duration": 1
            }
        }
        
        self.sc_interface.execute = Mock(return_value={"stdout": "", "stderr": ""})
        
        result = await self.handler.handle_generate_sound(request)
        
        self.assertTrue(result["success"])
        self.assertIn("code", result)
        self.sc_interface.execute.assert_called_once()
    
    async def test_handle_generate_sound_missing_instruction(self):
        """Test handling a generate_sound request with a missing instruction."""
        request = {
            "parameters": {
                "frequency": 440
            }
        }
        
        result = await self.handler.handle_generate_sound(request)
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Missing 'instruction' field in request")
    
    async def test_handle_stop_sound(self):
        """Test handling a stop_sound request."""
        request = {}
        
        self.sc_interface.stop_all = Mock()
        
        result = await self.handler.handle_stop_sound(request)
        
        self.assertTrue(result["success"])
        self.sc_interface.stop_all.assert_called_once()
    
    def test_generate_placeholder_code(self):
        """Test generating placeholder code."""
        instruction = "Generate a 440Hz sine wave"
        parameters = {
            "frequency": 440,
            "amplitude": 0.5,
            "duration": 1
        }
        
        code = self.handler._generate_placeholder_code(instruction, parameters)
        
        self.assertIn("SinOsc.ar(440", code)
        self.assertIn("0.5", code)
        self.assertIn("Generated from instruction", code)


class TestResponseGenerator(unittest.TestCase):
    """Tests for ResponseGenerator class."""
    
    def setUp(self):
        """Set up the test case."""
        self.generator = ResponseGenerator()
    
    def test_generate_success_response(self):
        """Test generating a success response."""
        result = {"data": "test"}
        response = self.generator.generate_success_response(result)
        
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["result"], result)
    
    def test_generate_error_response(self):
        """Test generating an error response."""
        message = "Test error"
        response = self.generator.generate_error_response(message, error_code="E001")
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        self.assertEqual(response["error_code"], "E001")
    
    def test_generate_progress_response(self):
        """Test generating a progress response."""
        progress = 50.5
        message = "Halfway there"
        response = self.generator.generate_progress_response(progress, message)
        
        self.assertEqual(response["status"], "progress")
        self.assertEqual(response["progress"], progress)
        self.assertEqual(response["message"], message)
    
    def test_format_code_for_claude(self):
        """Test formatting code for Claude Desktop."""
        code = "var sig = SinOsc.ar(440);"
        formatted = self.generator.format_code_for_claude(code)
        
        self.assertEqual(formatted, "```supercollider\nvar sig = SinOsc.ar(440);\n```")


class TestMCPServerIntegration(AioHTTPTestCase):
    """Integration tests for MCPServer class."""
    
    async def get_application(self):
        """Get the application for testing."""
        server = MCPServer(host="localhost", port=8080)
        
        async def mock_handler(request):
            return {"result": "ok"}
        
        server.register_handler("test_action", mock_handler)
        return server.app
    
    @unittest_run_loop
    async def test_handle_mcp_request_valid(self):
        """Test handling a valid MCP request."""
        request_data = {
            "action": "test_action",
            "data": "test"
        }
        
        resp = await self.client.post('/mcp', json=request_data)
        self.assertEqual(resp.status, 200)
        
        data = await resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"]["result"], "ok")
    
    @unittest_run_loop
    async def test_handle_mcp_request_invalid_action(self):
        """Test handling an MCP request with an invalid action."""
        request_data = {
            "action": "invalid_action",
            "data": "test"
        }
        
        resp = await self.client.post('/mcp', json=request_data)
        self.assertEqual(resp.status, 400)
        
        data = await resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("No handler for action", data["message"])
    
    @unittest_run_loop
    async def test_handle_mcp_request_missing_action(self):
        """Test handling an MCP request with a missing action."""
        request_data = {
            "data": "test"
        }
        
        resp = await self.client.post('/mcp', json=request_data)
        self.assertEqual(resp.status, 400)
        
        data = await resp.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Missing 'action' field in request")
    
    @unittest_run_loop
    async def test_handle_status(self):
        """Test handling a status request."""
        resp = await self.client.get('/status')
        self.assertEqual(resp.status, 200)
        
        data = await resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("test_action", data["handlers"])


if __name__ == "__main__":
    unittest.main()
