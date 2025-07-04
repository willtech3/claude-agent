import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum
import structlog

logger = structlog.get_logger()


class EventType(str, Enum):
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    ERROR = "error"
    PROGRESS = "progress"
    COMPLETION = "completion"
    OUTPUT = "output"


class ClaudeOutputParser:
    def __init__(self):
        self.buffer = ""
        self.file_changes: List[Dict[str, Any]] = []
        self.current_tool_use: Optional[Dict[str, Any]] = None
        
    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        line = line.strip()
        if not line:
            return None
            
        try:
            # Try to parse as JSON (stream-json format)
            event = json.loads(line)
            return self._process_json_event(event)
        except json.JSONDecodeError:
            # Not JSON, treat as plain output
            return {
                "type": EventType.OUTPUT,
                "text": line,
                "timestamp": self._get_timestamp()
            }
            
    def _process_json_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type", "")
        
        if event_type == "message_start":
            return {
                "type": EventType.PROGRESS,
                "status": "started",
                "message": "Claude is processing your request",
                "timestamp": self._get_timestamp()
            }
            
        elif event_type == "content_block_start":
            content_block = event.get("content_block", {})
            if content_block.get("type") == "tool_use":
                self.current_tool_use = {
                    "tool_name": content_block.get("name", ""),
                    "tool_id": content_block.get("id", ""),
                    "parameters": {}
                }
                return {
                    "type": EventType.TOOL_USE,
                    "tool": self.current_tool_use["tool_name"],
                    "status": "started",
                    "timestamp": self._get_timestamp()
                }
                
        elif event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "tool_use" and self.current_tool_use:
                # Accumulate tool parameters
                if "partial_json" in delta:
                    # Handle partial JSON updates
                    pass
                    
        elif event_type == "content_block_stop":
            if self.current_tool_use:
                tool_event = {
                    "type": EventType.TOOL_USE,
                    "tool": self.current_tool_use["tool_name"],
                    "status": "completed",
                    "timestamp": self._get_timestamp()
                }
                
                # Track file changes
                if self.current_tool_use["tool_name"] in ["Write", "Edit", "MultiEdit"]:
                    self._track_file_change(self.current_tool_use)
                    
                self.current_tool_use = None
                return tool_event
                
        elif event_type == "message_delta":
            delta = event.get("delta", {})
            if delta.get("stop_reason"):
                return {
                    "type": EventType.COMPLETION,
                    "status": "completed",
                    "reason": delta["stop_reason"],
                    "file_changes": self.file_changes,
                    "timestamp": self._get_timestamp()
                }
                
        elif event_type == "error":
            return {
                "type": EventType.ERROR,
                "error": event.get("error", {}),
                "timestamp": self._get_timestamp()
            }
            
        # Default to output for unhandled events
        return {
            "type": EventType.OUTPUT,
            "data": event,
            "timestamp": self._get_timestamp()
        }
        
    def _track_file_change(self, tool_use: Dict[str, Any]):
        tool_name = tool_use["tool_name"]
        params = tool_use.get("parameters", {})
        
        if tool_name == "Write":
            self.file_changes.append({
                "action": "created",
                "path": params.get("file_path", ""),
                "tool": tool_name
            })
        elif tool_name in ["Edit", "MultiEdit"]:
            self.file_changes.append({
                "action": "modified",
                "path": params.get("file_path", ""),
                "tool": tool_name
            })
            
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
        
    def get_summary(self) -> Dict[str, Any]:
        return {
            "files_changed": len(self.file_changes),
            "changes": self.file_changes
        }