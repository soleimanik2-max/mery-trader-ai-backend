from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEvent:
    event: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AuditService:
    """Audit trail for MERY TRADER AI operations."""

    def __init__(self):
        self.events: list[AuditEvent] = []

    def record(
        self,
        event: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        audit_event = AuditEvent(
            event=event,
            status=status,
            details=details or {},
        )

        self.events.append(audit_event)
        return audit_event

    def get_events(self) -> list[AuditEvent]:
        return self.events.copy()


audit_service = AuditService()
