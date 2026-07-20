import pytest

@pytest.mark.asyncio
async def test_circuit_breaker():
    from app.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState
    
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    
    async def failing_func():
        raise ValueError("Failed")
        
    # First failure
    with pytest.raises(ValueError):
        await cb.call(failing_func)
        
    assert cb.state == CircuitState.CLOSED
    
    # Second failure triggers OPEN
    with pytest.raises(ValueError):
        await cb.call(failing_func)
        
    assert cb.state == CircuitState.OPEN
    
    # Fast fail
    with pytest.raises(Exception, match="Circuit Breaker OPEN for failing_func"):
        await cb.call(failing_func)
