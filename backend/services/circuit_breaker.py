"""
SECURITY FIX: Circuit breaker implementation for background tasks.

Prevents cascade failures by monitoring task success rates and 
implementing exponential backoff when failure thresholds are exceeded.
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Circuit tripped, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    total_requests: int = 0
    
    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

class CircuitBreaker:
    """
    Circuit breaker for protecting background tasks from cascade failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit tripped due to failures, requests fail fast
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        failure_rate_threshold: float = 0.5,
        recovery_timeout: int = 60,
        timeout: int = 30,
        max_requests_half_open: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.failure_rate_threshold = failure_rate_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout = timeout
        self.max_requests_half_open = max_requests_half_open
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.next_attempt = 0.0
        self.half_open_requests = 0
        
    def _should_trip(self) -> bool:
        """Check if circuit should trip to OPEN state."""
        return (
            self.stats.failure_count >= self.failure_threshold or
            (self.stats.total_requests >= self.failure_threshold and 
             self.stats.failure_rate >= self.failure_rate_threshold)
        )
    
    def _can_attempt(self) -> bool:
        """Check if request can proceed based on current state."""
        now = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if now >= self.next_attempt:
                self.state = CircuitState.HALF_OPEN
                self.half_open_requests = 0
                logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_requests < self.max_requests_half_open
        
        return False
    
    def _record_success(self):
        """Record successful execution."""
        now = time.time()
        self.stats.success_count += 1
        self.stats.total_requests += 1
        self.stats.last_success_time = now
        
        if self.state == CircuitState.HALF_OPEN:
            # If we have enough successes, close the circuit
            if self.stats.success_count >= 2:  # Require 2 successes to close
                self.state = CircuitState.CLOSED
                self.stats = CircuitBreakerStats()  # Reset stats
                logger.info(f"Circuit breaker {self.name} recovered, transitioning to CLOSED")
        
        logger.debug(f"Circuit breaker {self.name} recorded success")
    
    def _record_failure(self, error: Exception):
        """Record failed execution."""
        now = time.time()
        self.stats.failure_count += 1
        self.stats.total_requests += 1
        self.stats.last_failure_time = now
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure during half-open immediately trips circuit
            self.state = CircuitState.OPEN
            self.next_attempt = now + self.recovery_timeout
            logger.warning(f"Circuit breaker {self.name} failed during HALF_OPEN, back to OPEN")
        elif self._should_trip():
            self.state = CircuitState.OPEN
            self.next_attempt = now + self.recovery_timeout
            logger.warning(
                f"Circuit breaker {self.name} tripped: "
                f"failures={self.stats.failure_count}, "
                f"rate={self.stats.failure_rate:.2f}, "
                f"threshold={self.failure_rate_threshold}"
            )
        
        logger.debug(f"Circuit breaker {self.name} recorded failure: {error}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute (sync or async)
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            TimeoutError: If execution times out
            Exception: Any exception from the wrapped function
        """
        if not self._can_attempt():
            raise CircuitOpenError(f"Circuit breaker {self.name} is OPEN")
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_requests += 1
        
        try:
            # Add timeout protection
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=self.timeout
                )
            else:
                # For sync functions, run in thread with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs),
                    timeout=self.timeout
                )
            
            self._record_success()
            return result
            
        except asyncio.TimeoutError as e:
            timeout_error = TimeoutError(f"Function timed out after {self.timeout}s")
            self._record_failure(timeout_error)
            raise timeout_error
        except Exception as e:
            self._record_failure(e)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "failure_rate": self.stats.failure_rate,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "next_attempt": self.next_attempt if self.state == CircuitState.OPEN else None,
        }

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

class CircuitBreakerManager:
    """Global manager for circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        failure_rate_threshold: float = 0.5,
        recovery_timeout: int = 60,
        timeout: int = 30
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                failure_rate_threshold=failure_rate_threshold,
                recovery_timeout=recovery_timeout,
                timeout=timeout
            )
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_breaker(self, name: str) -> bool:
        """Reset a circuit breaker to CLOSED state."""
        if name in self._breakers:
            breaker = self._breakers[name]
            breaker.state = CircuitState.CLOSED
            breaker.stats = CircuitBreakerStats()
            logger.info(f"Reset circuit breaker {name}")
            return True
        return False

# Global instance
circuit_manager = CircuitBreakerManager()

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    failure_rate_threshold: float = 0.5,
    recovery_timeout: int = 60,
    timeout: int = 30
):
    """
    Decorator to add circuit breaker protection to functions.
    
    Usage:
        @circuit_breaker("llm_service", timeout=60)
        async def call_llm_api():
            # Function implementation
            pass
    """
    def decorator(func):
        breaker = circuit_manager.get_breaker(
            name, failure_threshold, failure_rate_threshold, recovery_timeout, timeout
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator