from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets


@dataclass
class AuthResult:
    authenticated: bool
    token: str | None
    reason: str


class AuthService:
    """Authentication service for MERY TRADER AI Backend."""

    def __init__(self):
        self._tokens: dict[str, datetime] = {}

    def create_token(self, user_id: str) -> AuthResult:
        if not user_id.strip():
            return AuthResult(
                authenticated=False,
                token=None,
                reason="User ID is required",
            )

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        self._tokens[token_hash] = datetime.now(timezone.utc) + timedelta(
            hours=12
        )

        return AuthResult(
            authenticated=True,
            token=token,
            reason="Authentication successful",
        )

    def verify_token(self, token: str) -> AuthResult:
        if not token.strip():
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Token is required",
            )

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = self._tokens.get(token_hash)

        if expires_at is None:
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Invalid token",
            )

        if datetime.now(timezone.utc) >= expires_at:
            del self._tokens[token_hash]
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Token expired",
            )

        return AuthResult(
            authenticated=True,
            token=token,
            reason="Authentication verified",
        )


auth_service = AuthService()
