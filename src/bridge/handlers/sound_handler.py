"""Sound Handler for SPACO MCP Bridge.

This module provides a handler for sound-related MCP requests.
"""

import json
import logging

class SoundHandler:
    """
    Handler for sound-related MCP requests.
    
    This class provides methods to handle sound generation, modification,
    and other sound-related requests from Claude Desktop.
    """
    
    def __init__(self, sc_interface=None):
        """
        Initialize a SoundHandler.
        
        Args:
            sc_interface: Interface to SuperCollider
        """
        self.sc_interface = sc_interface
        self.logger = logging.getLogger('sound_handler')
    
    async def handle_generate_sound(self, request):
        """
        Handle a request to generate a sound.
        
        Args:
            request (dict): The request
        
        Returns:
            dict: The response
        """
        self.logger.info(f"Handling generate_sound request: {request}")
        
        # Extract parameters from request
        instruction = request.get('instruction', '')
        parameters = request.get('parameters', {})
        
        # Validate request
        if not instruction:
            return {
                "success": False,
                "error": "Missing 'instruction' field in request"
            }
        
        # Generate SuperCollider code (this is a placeholder until later phases)
        code = self._generate_placeholder_code(instruction, parameters)
        
        # Execute code if SuperCollider interface is available
        execution_result = None
        if self.sc_interface:
            try:
                execution_result = await self.sc_interface.execute(code)
            except Exception as e:
                self.logger.error(f"Error executing code: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error executing code: {str(e)}",
                    "code": code
                }
        
        # Return the result
        return {
            "success": True,
            "code": code,
            "execution_result": execution_result
        }
    
    async def handle_stop_sound(self, request):
        """
        Handle a request to stop sound generation.
        
        Args:
            request (dict): The request
        
        Returns:
            dict: The response
        """
        self.logger.info("Handling stop_sound request")
        
        # Stop sound if SuperCollider interface is available
        if self.sc_interface:
            try:
                await self.sc_interface.stop_all()
                return {"success": True, "message": "All sounds stopped"}
            except Exception as e:
                self.logger.error(f"Error stopping sounds: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Error stopping sounds: {str(e)}"}
        else:
            return {"success": False, "error": "SuperCollider interface not available"}
    
    def _generate_placeholder_code(self, instruction, parameters):
        """
        Generate placeholder SuperCollider code.
        
        Args:
            instruction (str): The instruction
            parameters (dict): The parameters
        
        Returns:
            str: The SuperCollider code
        """
        # This is a simple placeholder implementation
        # In later phases, this will be replaced with the actual NLP -> code generation
        
        freq = parameters.get('frequency', 440)
        amp = parameters.get('amplitude', 0.5)
        duration = parameters.get('duration', 1)
        
        code = f"""
        // Generated from instruction: {instruction}
        s.waitForBoot({{
            {{
                var sig = SinOsc.ar({freq}, 0, {amp});
                var env = EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
                sig = sig * env;
                sig ! 2 // Stereo output
            }}.play;
        }});
        """
        
        return code
