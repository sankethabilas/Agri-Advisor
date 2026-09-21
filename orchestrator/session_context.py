"""
Session Context Manager for Agri-Advisor Orchestrator (Subtask T-06.5).
Provides thread-safe, multi-turn state tracking keyed by user_id and session_id.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class ConversationTurn:
    turn_id: int
    query: str
    answer: str
    intent: str
    timestamp: str
    language: str = "en"
    agents_consulted: List[str] = field(default_factory=list)


@dataclass
class UserSession:
    session_id: str
    user_id: str
    created_at: str
    updated_at: str
    language: str = "en"
    active_crop: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    growth_stage: Optional[str] = None
    confirmed_diseases: List[str] = field(default_factory=list)
    history: List[ConversationTurn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "language": self.language,
            "active_crop": self.active_crop,
            "location": self.location,
            "growth_stage": self.growth_stage,
            "confirmed_diseases": self.confirmed_diseases,
            "turn_count": len(self.history),
            "history": [turn.__dict__ for turn in self.history],
        }


class SessionManager:
    """Thread-safe in-memory session manager for conversational context."""

    def __init__(self, max_turns_per_session: int = 20) -> None:
        self._sessions_by_user: Dict[str, UserSession] = {}
        self._sessions_by_id: Dict[str, UserSession] = {}
        self._lock = threading.RLock()
        self.max_turns_per_session = max_turns_per_session

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        crop_context: Optional[str] = None,
        language: str = "en",
    ) -> UserSession:
        with self._lock:
            session = None
            if session_id and session_id in self._sessions_by_id:
                session = self._sessions_by_id[session_id]
            elif user_id in self._sessions_by_user:
                session = self._sessions_by_user[user_id]

            now = self._now_iso()
            if session is None:
                new_session_id = session_id or f"sess-{uuid.uuid4().hex[:12]}"
                session = UserSession(
                    session_id=new_session_id,
                    user_id=user_id,
                    created_at=now,
                    updated_at=now,
                    language=language,
                    active_crop=crop_context,
                    location=location,
                )
                self._sessions_by_user[user_id] = session
                self._sessions_by_id[session.session_id] = session
            else:
                session.updated_at = now
                if crop_context:
                    session.active_crop = crop_context
                if location:
                    session.location = location
                if language:
                    session.language = language

            return session

    def add_turn(
        self,
        user_id: str,
        query: str,
        answer: str,
        intent: str,
        language: str = "en",
        agents_consulted: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> ConversationTurn:
        with self._lock:
            session = self.get_or_create_session(user_id=user_id, session_id=session_id, language=language)
            now = self._now_iso()
            turn = ConversationTurn(
                turn_id=len(session.history) + 1,
                query=query,
                answer=answer,
                intent=intent,
                timestamp=now,
                language=language,
                agents_consulted=agents_consulted or [],
            )
            session.history.append(turn)
            if len(session.history) > self.max_turns_per_session:
                session.history = session.history[-self.max_turns_per_session:]
            session.updated_at = now
            return turn

    def get_session(self, user_id: str) -> Optional[UserSession]:
        with self._lock:
            return self._sessions_by_user.get(user_id)

    def get_recent_history(self, user_id: str, limit: int = 5) -> List[ConversationTurn]:
        with self._lock:
            session = self._sessions_by_user.get(user_id)
            if not session:
                return []
            return session.history[-limit:]

    def clear_session(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self._sessions_by_user:
                session = self._sessions_by_user.pop(user_id)
                self._sessions_by_id.pop(session.session_id, None)
                return True
            return False

    def get_active_sessions_count(self) -> int:
        with self._lock:
            return len(self._sessions_by_user)


# Global singleton instance for orchestrator runtime
session_manager = SessionManager()
