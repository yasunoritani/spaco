"""Response Generator for SPACO MCP Bridge.

This module provides functionality for generating responses to
MCP requests from Claude Desktop.
"""

import json
import logging

class ResponseGenerator:
    """
    Generates responses to MCP requests from Claude Desktop.
    
    This class provides methods for formatting and sending responses
    back to Claude Desktop using the MCP protocol.
    """
    
    def __init__(self):
        """Initialize a ResponseGenerator."""
        self.logger = logging.getLogger('response_generator')
    
    def generate_success_response(self, result, context=None):
        """
        Generate a success response.
        
        Args:
            result: The result to include in the response
            context (dict, optional): Additional context information
        
        Returns:
            dict: The MCP response
        """
        response = {
            "status": "success",
            "result": result
        }
        
        if context:
            response["context"] = context
        
        self.logger.debug(f"Generated success response: {response}")
        return response
    
    def generate_error_response(self, message, error_code=None, context=None):
        """
        Generate an error response.
        
        Args:
            message (str): The error message
            error_code (str, optional): An error code
            context (dict, optional): Additional context information
        
        Returns:
            dict: The MCP response
        """
        response = {
            "status": "error",
            "message": message
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if context:
            response["context"] = context
        
        self.logger.warning(f"Generated error response: {response}")
        return response
    
    def generate_progress_response(self, progress, message=None, context=None):
        """
        Generate a progress response.
        
        Args:
            progress (float): The progress percentage (0-100)
            message (str, optional): A progress message
            context (dict, optional): Additional context information
        
        Returns:
            dict: The MCP response
        """
        response = {
            "status": "progress",
            "progress": progress
        }
        
        if message:
            response["message"] = message
        
        if context:
            response["context"] = context
        
        self.logger.debug(f"Generated progress response: {response}")
        return response
    
    def format_code_for_claude(self, code, language="supercollider"):
        """
        Format code for display in Claude Desktop.
        
        Args:
            code (str): The code to format
            language (str, optional): The programming language
        
        Returns:
            str: The formatted code
        """
        return f"```{language}\n{code}\n```"
    
    def format_audio_response(self, audio_url, description=None):
        """
        Format an audio response for Claude Desktop.
        
        Args:
            audio_url (str): URL to the generated audio
            description (str, optional): Description of the audio
        
        Returns:
            dict: The formatted audio response
        """
        response = {
            "type": "audio",
            "url": audio_url
        }
        
        if description:
            response["description"] = description
        
        return response
