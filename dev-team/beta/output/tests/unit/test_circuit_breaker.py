"""
Unit tests for Circuit Breaker.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from services.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    get_facebook_circuit,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit(self):
        """Create a test circuit breaker."""
        return CircuitBreaker(
            name="test_circuit",
            failure_threshold=3,
            recovery_timeout=1,  # 1 second for testing
            half_open_max_calls=2,
            success_threshold=1
        )
    
    @pytest.mark.asyncio
    async def test_circuit_starts_closed(self, circuit):
        """Circuit should start in CLOSED state."""
        assert circuit.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_successful_call_increments_success(self, circuit):
        """Successful call should work normally."""
        async def success_func():
            return "success"
        
        result = await circuit.call(success_func)
        assert result == "success"
        assert circuit.metrics.success_count == 1
    
    @pytest.mark.asyncio
    async def test_failure_opens_circuit(self, circuit):
        """Multiple failures should open circuit."""
        async def fail_func():
            raise ValueError("Test error")
        
        # Should fail 3 times then open
        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)
        
        assert circuit.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_open_circuit_raises_error(self, circuit):
        """Calls to open circuit should raise CircuitBreakerOpenError."""
        # Force open
        circuit.force_open()
        
        async def any_func():
            return "result"
        
        with pytest.raises(CircuitBreakerOpenError):
            await circuit.call(any_func)
    
    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, circuit):
        """Circuit should enter half-open after timeout."""
        # Open the circuit
        circuit.force_open()
        circuit._last_failure_time = datetime.now() - timedelta(seconds=2)
        
        async def any_func():
            return "result"
        
        # Should transition to half-open and allow call
        result = await circuit.call(any_func)
        assert result == "success"
        assert circuit.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_success_in_half_open_closes_circuit(self, circuit):
        """Success in half-open should close circuit."""
        circuit._transition_to_half_open()
        
        async def success_func():
            return "success"
        
        result = await circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self, circuit):
        """Failure in half-open should reopen circuit."""
        circuit._transition_to_half_open()
        
        async def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await circuit.call(fail_func)
        
        assert circuit.state == CircuitState.OPEN


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""
    
    def test_registry_creates_new_circuit(self):
        """Registry should create new circuit if not exists."""
        registry = CircuitBreakerRegistry()
        circuit = registry.get_or_create("test", failure_threshold=5)
        
        assert circuit.name == "test"
        assert circuit.failure_threshold == 5
    
    def test_registry_returns_existing_circuit(self):
        """Registry should return existing circuit."""
        registry = CircuitBreakerRegistry()
        circuit1 = registry.get_or_create("test", failure_threshold=5)
        circuit2 = registry.get_or_create("test", failure_threshold=10)
        
        assert circuit1 is circuit2
        assert circuit2.failure_threshold == 5  # Original value preserved
    
    def test_get_facebook_circuit(self):
        """Should get preconfigured Facebook circuit."""
        circuit = get_facebook_circuit("messages")
        assert circuit.name == "facebook_messages"
        
        circuit = get_facebook_circuit("comments")
        assert circuit.name == "facebook_comments"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
