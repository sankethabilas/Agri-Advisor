"""Authentication and request safety controls for the orchestrator API."""

from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import unicodedata
from typing import Deque, Dict, Iterator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from orchestrator.config import PROJECT_ROOT, settings

logger = logging.getLogger("agri_advisor.security")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "30"))
PASSWORD_ITERATIONS = 310_000
DATABASE_PATH = Path(os.getenv("AUTH_DATABASE_PATH", PROJECT_ROOT / "data" / "users.sqlite3"))
_DEV_SECRET = secrets.token_urlsafe(48)
if os.getenv("APP_ENV", "development").lower() == "production" and not settings.jwt_secret_key:
    raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
if not settings.jwt_secret_key:
    logger.warning("JWT_SECRET_KEY is unset; using an ephemeral development-only signing key.")
JWT_SECRET = settings.jwt_secret_key or _DEV_SECRET

_INJECTION_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bignore\s+(?:all\s+)?(?:previous|prior|the)\s+instructions\b",
    r"\bdisregard\s+(?:all\s+)?(?:previous|prior|the)\s+instructions\b",
    r"\b(?:reveal|print|show|repeat|output)\s+(?:the\s+)?(?:system|developer)\s+prompt\b",
    r"\b(?:act|respond|behave)\s+as\s+(?:an?\s+)?(?:system|developer|unrestricted)\b",
    r"\b(?:bypass|override|disable)\s+(?:all\s+)?(?:safety|security)(?:\s+(?:guardrails|controls|restrictions))?\b",
    r"\bforget\s+(?:all\s+)?(?:your\s+)?(?:rules|instructions|guidelines)\b",
    r"\b(?:system|developer)\s*:\s*(?:new\s+)?(?:policy|instructions?)\b",
    r"\b(?:as\s+)?dan\b",
    r"\bdo\s+not\s+follow\s+(?:the\s+)?(?:previous|prior|earlier)\s+instructions\b",
    r"\bdo\s+anything\s+now\b",
))
_ANSI_ESCAPE = re.compile(r"\x1B(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1B\\))")
_SECRET_OUTPUT_PATTERNS = re.compile(
    r"(?i)(?:\b(?:sk|gsk|key)-[A-Za-z0-9_-]{12,}\b|\bBearer\s+[A-Za-z0-9._~-]{20,}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
_UNSAFE_OUTPUT_LINE = re.compile(
    r"(?i)^.*(?:ignore all (?:previous|prior) instructions|system prompt|developer prompt).*$"
)
_bearer = HTTPBearer(auto_error=False)


class UserStore:
    """Small SQLite account store using salted PBKDF2 password hashes."""

    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS users ("
                "username TEXT PRIMARY KEY COLLATE NOCASE, "
                "password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, "
                "created_at TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)

    def create_user(self, username: str, password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = self._hash_password(password, salt)
        try:
            with self._connection() as connection:
                connection.execute(
                    "INSERT INTO users (username, password_salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (username, salt.hex(), password_hash.hex(), datetime.now(timezone.utc).isoformat()),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    def authenticate(self, username: str, password: str) -> bool:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT password_salt, password_hash FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
        if row is None:
            self._hash_password(password, b"agri-advisor-dummy-salt")
            return False
        expected = bytes.fromhex(row[1])
        actual = self._hash_password(password, bytes.fromhex(row[0]))
        return hmac.compare_digest(actual, expected)


user_store = UserStore()


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES)}
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="A valid bearer token is required.")
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise JWTError("Missing token subject")
        return subject
    except JWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired bearer token.") from error


def sanitize_text(value: str, max_length: int, preserve_lines: bool = False) -> str:
    """Remove terminal escapes and Unicode control/format characters, preserving scripts."""
    value = _ANSI_ESCAPE.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))
    cleaned = "".join(
        char if unicodedata.category(char)[0] != "C" else ("\n" if preserve_lines and char == "\n" else " " if char == "\t" else "")
        for char in value
    )
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
    if not preserve_lines:
        cleaned = re.sub(r"\s+", " ", cleaned)
    else:
        cleaned = "\n".join(line.strip() for line in cleaned.splitlines())
    cleaned = cleaned.strip()
    return cleaned[:max_length]


def find_prompt_injection(value: str) -> Optional[str]:
    normalized = re.sub(r"\s+", " ", value).strip()
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(0)
    return None


def filter_generated_output(value: str) -> str:
    value = sanitize_text(value, max_length=20_000, preserve_lines=True)
    safe_lines = []
    for line in value.splitlines():
        if _UNSAFE_OUTPUT_LINE.match(line):
            logger.warning("Filtered unsafe generated response content.")
            continue
        safe_lines.append(line)
    result = "\n".join(safe_lines)
    if _SECRET_OUTPUT_PATTERNS.search(result):
        logger.warning("Redacted secret-like content from generated response.")
        result = _SECRET_OUTPUT_PATTERNS.sub("[redacted]", result)
    return result


class UserRateLimiter:
    """Thread-safe, per-subject sliding-window request limiter."""

    def __init__(self, limit: int = 30, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, subject: str, now: Optional[float] = None) -> int:
        current = now if now is not None else time.monotonic()
        cutoff = current - self.window_seconds
        with self._lock:
            events = self._events[subject]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(events[0] + self.window_seconds - current + 0.999))
                return retry_after
            events.append(current)
        return 0


user_rate_limiter = UserRateLimiter(
    limit=int(os.getenv("RATE_LIMIT_REQUESTS", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)