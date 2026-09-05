from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from database import SessionLocal
from models import AuthToken


@dataclass
class AuthResult:
    authenticated: bool
    token: str | None
    reason: str
    user_id: str | None = None
    role: str | None = None


class AuthService:
    """Persistent authentication and authorization service for MERY TRADER AI."""

    TOKEN_LIFETIME_HOURS = 12

    ROLES = {
        "USER": {
            "READ_MARKET",
            "ANALYZE_MARKET",
        },
        "TRADER": {
            "READ_MARKET",
            "ANALYZE_MARKET",
            "CALCULATE_RISK",
            "MANAGE_ORDERS",
        },
        "ADMIN": {
            "READ_MARKET",
            "ANALYZE_MARKET",
            "CALCULATE_RISK",
            "MANAGE_ORDERS",
            "SYSTEM_ADMIN",
        },
    }

    def create_token(
        self,
        user_id: str,
        role: str = "USER",
    ) -> AuthResult:

        user_id = user_id.strip()
        role = role.upper().strip()

        if not user_id:
            return AuthResult(
                authenticated=False,
                token=None,
                reason="User ID is required",
            )

        if role not in self.ROLES:
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Invalid role",
            )

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=self.TOKEN_LIFETIME_HOURS)
        )

        db = SessionLocal()

        try:
            auth_token = AuthToken(
                token_hash=token_hash,
                user_id=user_id,
                role=role,
                expires_at=expires_at,
            )

            db.add(auth_token)
            db.commit()

        except Exception:
            db.rollback()

            return AuthResult(
                authenticated=False,
                token=None,
                reason="Authentication storage failed",
            )

        finally:
            db.close()

        return AuthResult(
            authenticated=True,
            token=token,
            reason="Authentication successful",
            user_id=user_id,
            role=role,
        )

    def verify_token(
        self,
        token: str,
    ) -> AuthResult:

        token = token.strip()

        if not token:
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Token is required",
            )

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        db = SessionLocal()

        try:
            session = (
                db.query(AuthToken)
                .filter(
                    AuthToken.token_hash == token_hash
                )
                .first()
            )

            if session is None:
                return AuthResult(
                    authenticated=False,
                    token=None,
                    reason="Invalid token",
                )

            expires_at = session.expires_at

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            if datetime.now(timezone.utc) >= expires_at:
                db.delete(session)
                db.commit()

                return AuthResult(
                    authenticated=False,
                    token=None,
                    reason="Token expired",
                )

            return AuthResult(
                authenticated=True,
                token=token,
                reason="Authentication verified",
                user_id=session.user_id,
                role=session.role,
            )

        finally:
            db.close()

    def authorize(
        self,
        token: str,
        permission: str,
    ) -> AuthResult:

        result = self.verify_token(token)

        if not result.authenticated:
            return result

        role = result.role

        if role is None:
            return AuthResult(
                authenticated=False,
                token=None,
                reason="Role information unavailable",
            )

        permissions = self.ROLES.get(role, set())

        if permission not in permissions:
            return AuthResult(
                authenticated=False,
                token=token,
                reason=f"Permission denied: {permission}",
                user_id=result.user_id,
                role=role,
            )

        return AuthResult(
            authenticated=True,
            token=token,
            reason="Authorization successful",
            user_id=result.user_id,
            role=role,
        )


auth_service = AuthService()