import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OutputParser:
    """Parse Claude Code output into structured events."""
    
    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single line of output."""
        if not line.strip():
            return None
            
        # Try to parse as JSON first (if using --output-format json)
        try:
            data = json.loads(line)
            return self._process_json_event(data)
        except json.JSONDecodeError:
            # Fall back to plain text parsing
            return self._process_text_line(line)
            
    def _process_json_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON event from Claude Code."""
        event_type = data.get("type", "unknown")
        
        # Map Claude Code event types to our event types
        if event_type == "tool_use":
            return {
                "type": "tool_use",
                "tool": data.get("tool"),
                "parameters": data.get("parameters"),
                "content": data.get("content", "")
            }
        elif event_type == "message":
            return {
                "type": "message",
                "content": data.get("content", ""),
                "role": data.get("role", "assistant")
            }
        elif event_type == "file_operation":
            return {
                "type": "file_operation",
                "operation": data.get("operation"),
                "path": data.get("path"),
                "content": data.get("content", "")
            }
        elif event_type == "command_execution":
            return {
                "type": "command_execution",
                "command": data.get("command"),
                "output": data.get("output", ""),
                "exit_code": data.get("exit_code")
            }
        else:
            # Pass through unknown event types
            return {
                "type": event_type,
                "data": data
            }
            
    def _process_text_line(self, line: str) -> Dict[str, Any]:
        """Process a plain text line of output."""
        # Detect different types of output based on patterns
        
        # Status messages
        if line.startswith("["):
            return {
                "type": "status",
                "content": line
            }
            
        # File operations
        if any(keyword in line.lower() for keyword in ["creating", "writing", "editing", "reading"]):
            return {
                "type": "file_operation",
                "content": line
            }
            
        # Command execution
        if line.startswith("$") or line.startswith(">"):
            return {
                "type": "command",
                "content": line
            }
            
        # Error messages
        if any(keyword in line.lower() for keyword in ["error", "failed", "exception"]):
            return {
                "type": "error",
                "content": line
            }
            
        # Default to output
        return {
            "type": "output",
            "content": line
        }