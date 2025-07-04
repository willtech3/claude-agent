import pytest
import json
from datetime import datetime

from agent.event_parser import ClaudeOutputParser, EventType


class TestClaudeOutputParser:
    def test_parse_empty_line(self):
        parser = ClaudeOutputParser()
        result = parser.parse_line("")
        assert result is None
        
    def test_parse_plain_text_line(self):
        parser = ClaudeOutputParser()
        result = parser.parse_line("This is plain text output")
        
        assert result is not None
        assert result["type"] == EventType.OUTPUT
        assert result["text"] == "This is plain text output"
        assert "timestamp" in result
        
    def test_parse_message_start(self):
        parser = ClaudeOutputParser()
        line = '{"type": "message_start"}'
        result = parser.parse_line(line)
        
        assert result["type"] == EventType.PROGRESS
        assert result["status"] == "started"
        assert "message" in result
        
    def test_parse_tool_use_start(self):
        parser = ClaudeOutputParser()
        line = '{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Write", "id": "tool-123"}}'
        result = parser.parse_line(line)
        
        assert result["type"] == EventType.TOOL_USE
        assert result["tool"] == "Write"
        assert result["status"] == "started"
        assert parser.current_tool_use is not None
        assert parser.current_tool_use["tool_name"] == "Write"
        
    def test_parse_tool_use_complete(self):
        parser = ClaudeOutputParser()
        
        # Start tool use
        start_line = '{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Edit", "id": "tool-123"}}'
        parser.parse_line(start_line)
        
        # Complete tool use
        stop_line = '{"type": "content_block_stop"}'
        result = parser.parse_line(stop_line)
        
        assert result["type"] == EventType.TOOL_USE
        assert result["tool"] == "Edit"
        assert result["status"] == "completed"
        assert parser.current_tool_use is None
        
    def test_track_file_changes(self):
        parser = ClaudeOutputParser()
        
        # Write tool
        parser.parse_line('{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Write"}}')
        parser.current_tool_use["parameters"] = {"file_path": "/test/file1.py"}
        parser.parse_line('{"type": "content_block_stop"}')
        
        # Edit tool
        parser.parse_line('{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Edit"}}')
        parser.current_tool_use["parameters"] = {"file_path": "/test/file2.py"}
        parser.parse_line('{"type": "content_block_stop"}')
        
        assert len(parser.file_changes) == 2
        assert parser.file_changes[0]["action"] == "created"
        assert parser.file_changes[0]["path"] == "/test/file1.py"
        assert parser.file_changes[1]["action"] == "modified"
        assert parser.file_changes[1]["path"] == "/test/file2.py"
        
    def test_parse_completion(self):
        parser = ClaudeOutputParser()
        
        # Add some file changes first
        parser.file_changes = [{"action": "created", "path": "test.py"}]
        
        line = '{"type": "message_delta", "delta": {"stop_reason": "end_turn"}}'
        result = parser.parse_line(line)
        
        assert result["type"] == EventType.COMPLETION
        assert result["status"] == "completed"
        assert result["reason"] == "end_turn"
        assert result["file_changes"] == parser.file_changes
        
    def test_parse_error(self):
        parser = ClaudeOutputParser()
        line = '{"type": "error", "error": {"message": "API error", "code": "rate_limit"}}'
        result = parser.parse_line(line)
        
        assert result["type"] == EventType.ERROR
        assert result["error"]["message"] == "API error"
        assert result["error"]["code"] == "rate_limit"
        
    def test_parse_unknown_event(self):
        parser = ClaudeOutputParser()
        line = '{"type": "unknown_event", "data": "some data"}'
        result = parser.parse_line(line)
        
        assert result["type"] == EventType.OUTPUT
        assert "data" in result
        assert result["data"]["type"] == "unknown_event"
        
    def test_get_summary(self):
        parser = ClaudeOutputParser()
        parser.file_changes = [
            {"action": "created", "path": "file1.py"},
            {"action": "modified", "path": "file2.py"}
        ]
        
        summary = parser.get_summary()
        assert summary["files_changed"] == 2
        assert summary["changes"] == parser.file_changes
        
    def test_parse_content_block_delta(self):
        parser = ClaudeOutputParser()
        
        # Start tool use first
        parser.parse_line('{"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Write"}}')
        
        # Delta event (partial JSON)
        line = '{"type": "content_block_delta", "delta": {"type": "tool_use", "partial_json": "{\\"file"}}'
        result = parser.parse_line(line)
        
        # Should return None for delta events (they're accumulated internally)
        assert result is None
        
    def test_timestamp_format(self):
        parser = ClaudeOutputParser()
        timestamp = parser._get_timestamp()
        
        # Should be ISO format with Z suffix
        assert timestamp.endswith("Z")
        # Should be parseable
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert dt is not None