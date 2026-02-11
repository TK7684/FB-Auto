"""
Error Data Models.

Data models for error handling and tracking.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorStatus(Enum):
    """Error resolution status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    service: str = ""
    operation: str = ""
    user_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    status: ErrorStatus = ErrorStatus.NEW
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""
    
    def acknowledge(self):
        """Mark error as acknowledged."""
        self.status = ErrorStatus.ACKNOWLEDGED
    
    def resolve(self, notes: str = ""):
        """Mark error as resolved."""
        self.status = ErrorStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolution_notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "service": self.service,
            "operation": self.operation,
            "user_id": self.user_id,
            "status": self.status.value,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class ErrorSummary:
    """Summary of errors over a time period."""
    start_time: datetime
    end_time: datetime
    total_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    errors_by_service: Dict[str, int] = field(default_factory=dict)
    most_common_error: Optional[str] = None
    error_rate: float = 0.0  # Errors per minute
    
    def add_error(self, record: ErrorRecord):
        """Add an error to the summary."""
        self.total_errors += 1
        
        # Count by type
        error_type = record.error_type
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        # Count by severity
        severity = record.severity.value
        self.errors_by_severity[severity] = self.errors_by_severity.get(severity, 0) + 1
        
        # Count by service
        service = record.service or "unknown"
        self.errors_by_service[service] = self.errors_by_service.get(service, 0) + 1
        
        # Update most common
        self.most_common_error = max(self.errors_by_type, key=self.errors_by_type.get)
    
    def calculate_rate(self, minutes: Optional[int] = None):
        """Calculate error rate."""
        if minutes is None:
            minutes = (self.end_time - self.start_time).total_seconds() / 60
        if minutes > 0:
            self.error_rate = self.total_errors / minutes
