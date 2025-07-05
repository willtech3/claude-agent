import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage Claude Code sessions and configurations."""
    
    def __init__(self, sessions_dir: str = "/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
    def create_session(self, task_id: str, config: Optional[Dict[str, Any]] = None) -> Path:
        """Create a new session directory."""
        session_path = self.sessions_dir / task_id
        session_path.mkdir(exist_ok=True)
        
        # Create session config
        if config:
            config_path = session_path / "config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
        logger.info(f"Created session at {session_path}")
        return session_path
        
    def get_session(self, task_id: str) -> Optional[Path]:
        """Get existing session path."""
        session_path = self.sessions_dir / task_id
        if session_path.exists():
            return session_path
        return None
        
    def cleanup_session(self, task_id: str) -> None:
        """Clean up session directory."""
        session_path = self.sessions_dir / task_id
        if session_path.exists():
            import shutil
            shutil.rmtree(session_path)
            logger.info(f"Cleaned up session {task_id}")