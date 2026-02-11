"""
Circuit Breaker Pattern Implementation.

Prevents cascade failures by stopping requests to failing services,
then gradually allowing test requests to check for recovery.
"""

from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
import asyncio
import threading
from loguru import logger


class CircuitState(Enum):
    """
    Circuit breaker states.
    
    CLOSED - Normal operation, requests pass through
    OPEN - Failure threshold reached, requests fail fast
    HALF_OPEN - Testing if service has recovered
    """
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker monitoring."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)
    total_calls: int = 0
    rejected_calls: int = 0
    
    def record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.total_calls += 1
    
    def record_success(self):
        """Record a success."""
        self.success_count += 1
        self.last_success_time = datetime.now()
        self.total_calls += 1
    
    def record_rejection(self):
        """Record a rejected call (circuit open)."""
        self.rejected_calls += 1
    
    def record_transition(self, from_state: CircuitState, to_state: CircuitState):
        """Record a state transition."""
        self.state_transitions.append({
            "from": from_state.name,
            "to": to_state.name,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_calls == 0:
            return 0.0
        return self.failure_count / self.total_calls


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, circuit_name: str, message: Optional[str] = None):
        self.circuit_name = circuit_name
        self.message = message or f"Circuit '{circuit_name}' is OPEN"
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascade failures.
    
    Pattern:
    - CLOSED: Normal operation, track failures
    - OPEN: After threshold failures, reject immediately
    - HALF_OPEN: After timeout, allow test requests
    
    Usage:
        circuit = CircuitBreaker('facebook_api')
        
        try:
            result = await circuit.call(api_function, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit is open, fail fast
            return fallback_response
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        expected_exception: Optional[type] = Exception,
        on_state_change: Optional[Callable] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit name for identification
            failure_threshold: Failures to open circuit
            recovery_timeout: Seconds before half-open
            half_open_max_calls: Test calls in half-open state
            success_threshold: Successes to close circuit
            expected_exception: Exception type to count as failure
            on_state_change: Callback when state changes
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception or Exception
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()
        self._metrics = CircuitMetrics()
        
        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state
    
    @property
    def metrics(self) -> CircuitMetrics:
        """Get circuit metrics."""
        return self._metrics
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments for function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from func
        """
        with self._lock:
            # Check state and transition if needed
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self._metrics.record_rejection()
                    remaining = self._get_remaining_timeout()
                    raise CircuitBreakerOpenError(
                        self.name,
                        f"Circuit is OPEN. Retry after {remaining}s"
                    )
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._metrics.record_rejection()
                    raise CircuitBreakerOpenError(
                        self.name,
                        "Half-open call limit reached"
                    )
                self._half_open_calls += 1
        
        # Execute the function (outside lock)
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self._metrics.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
            else:
                # In closed state, reset failure count on success
                self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._metrics.record_failure()
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open immediately opens circuit
                self._transition_to_open()
            elif self._failure_count >= self.failure_threshold:
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try reset."""
        if not self._last_failure_time:
            return True
        return datetime.now() >= self._last_failure_time + self.recovery_timeout
    
    def _get_remaining_timeout(self) -> int:
        """Get seconds remaining until reset attempt."""
        if not self._last_failure_time:
            return 0
        remaining = (self._last_failure_time + self.recovery_timeout) - datetime.now()
        return max(0, int(remaining.total_seconds()))
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        old_state = self._state
        self._state = CircuitState.OPEN
        self._metrics.record_transition(old_state, CircuitState.OPEN)
        logger.warning(f"Circuit '{self.name}' OPENED after {self._failure_count} failures")
        
        if self.on_state_change:
            try:
                self.on_state_change(self.name, old_state, CircuitState.OPEN)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        old_state = self._state
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0
        self._metrics.record_transition(old_state, CircuitState.HALF_OPEN)
        logger.info(f"Circuit '{self.name}' entering HALF-OPEN state")
        
        if self.on_state_change:
            try:
                self.on_state_change(self.name, old_state, CircuitState.HALF_OPEN)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        old_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._metrics.record_transition(old_state, CircuitState.CLOSED)
        logger.info(f"Circuit '{self.name}' CLOSED (healthy)")
        
        if self.on_state_change:
            try:
                self.on_state_change(self.name, old_state, CircuitState.CLOSED)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get circuit state as dictionary for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.name,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "half_open_calls": self._half_open_calls,
                "half_open_max": self.half_open_max_calls,
                "recovery_timeout_seconds": self.recovery_timeout.total_seconds(),
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "metrics": {
                    "total_calls": self._metrics.total_calls,
                    "rejected_calls": self._metrics.rejected_calls,
                    "failure_rate": self._metrics.get_failure_rate(),
                    "transitions": self._metrics.state_transitions[-5:]  # Last 5
                }
            }
    
    def force_open(self):
        """Force circuit to OPEN state (for testing/emergencies)."""
        with self._lock:
            self._transition_to_open()
    
    def force_close(self):
        """Force circuit to CLOSED state (for testing/recovery)."""
        with self._lock:
            self._transition_to_closed()


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Provides centralized access to all circuits in the system.
    """
    
    def __init__(self):
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def register(self, circuit: CircuitBreaker) -> CircuitBreaker:
        """Register a circuit breaker."""
        with self._lock:
            self._circuits[circuit.name] = circuit
        return circuit
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit by name."""
        with self._lock:
            return self._circuits.get(name)
    
    def get_or_create(
        self,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """Get existing circuit or create new one."""
        with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(name, **kwargs)
            return self._circuits[name]
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuits."""
        with self._lock:
            return {
                name: circuit.get_state_dict()
                for name, circuit in self._circuits.items()
            }
    
    def reset_all(self):
        """Reset all circuits to CLOSED state."""
        with self._lock:
            for circuit in self._circuits.values():
                circuit.force_close()


# Global registry
_circuit_registry: Optional[CircuitBreakerRegistry] = None


def get_circuit_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _circuit_registry
    if _circuit_registry is None:
        _circuit_registry = CircuitBreakerRegistry()
    return _circuit_registry


# Pre-configured circuits for Facebook API
CIRCUIT_BREAKER_CONFIG = {
    "messages": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "half_open_max_calls": 3,
        "success_threshold": 2,
    },
    "comments": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "half_open_max_calls": 2,
        "success_threshold": 2,
    },
    "private_replies": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "half_open_max_calls": 2,
        "success_threshold": 2,
    },
    "insights": {
        "failure_threshold": 10,
        "recovery_timeout": 60,
        "half_open_max_calls": 3,
        "success_threshold": 2,
    },
}


def get_facebook_circuit(api_type: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker for Facebook API type.
    
    Args:
        api_type: Type of API (messages, comments, private_replies, insights)
        
    Returns:
        Configured CircuitBreaker
    """
    registry = get_circuit_registry()
    config = CIRCUIT_BREAKER_CONFIG.get(api_type, CIRCUIT_BREAKER_CONFIG["messages"])
    return registry.get_or_create(f"facebook_{api_type}", **config)
