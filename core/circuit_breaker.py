"""
Circuit Breaker Pattern for Fault Tolerance
"""

import time
import threading
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 2           # Successes before closing
    timeout: float = 60.0                # Seconds before trying half-open
    window_size: int = 10                # Sliding window size
    excluded_exceptions: tuple = ()      # Exceptions to not count as failures
    on_open: Optional[Callable] = None   # Callback when opening
    on_close: Optional[Callable] = None  # Callback when closing


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.last_state_change = time.time()

        # Metrics
        self.call_count = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []

        # Sliding window for error rate calculation
        self.call_results = deque(maxlen=self.config.window_size)

        # Thread safety
        self._lock = threading.RLock()

        logger.info(f"CircuitBreaker '{name}' initialized")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker
        """
        with self._lock:
            self.call_count += 1

            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

            try:
                # Execute the function
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except Exception as e:
                # Check if exception should be handled
                if not self._should_handle_exception(e):
                    raise

                self._on_failure(e)
                raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Async version of call
        """
        with self._lock:
            self.call_count += 1

            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result

            except Exception as e:
                if not self._should_handle_exception(e):
                    raise

                self._on_failure(e)
                raise

    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.total_successes += 1
            self.last_success_time = time.time()
            self.call_results.append(True)

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            else:
                self.failure_count = 0

    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        with self._lock:
            self.total_failures += 1
            self.last_failure_time = time.time()
            self.call_results.append(False)

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure: {exception}"
            )

            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset from open state"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.config.timeout
        )

    def _should_handle_exception(self, exception: Exception) -> bool:
        """Check if exception should be handled by circuit breaker"""
        return not isinstance(exception, self.config.excluded_exceptions)

    def _transition_to_open(self):
        """Transition to open state"""
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        self.state_changes.append((self.state, self.last_state_change))

        logger.error(f"Circuit breaker '{self.name}' opened")

        if self.config.on_open:
            try:
                self.config.on_open(self)
            except Exception as e:
                logger.error(f"Error in on_open callback: {e}")

    def _transition_to_closed(self):
        """Transition to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.state_changes.append((self.state, self.last_state_change))

        logger.info(f"Circuit breaker '{self.name}' closed")

        if self.config.on_close:
            try:
                self.config.on_close(self)
            except Exception as e:
                logger.error(f"Error in on_close callback: {e}")

    def _transition_to_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = time.time()
        self.state_changes.append((self.state, self.last_state_change))

        logger.info(f"Circuit breaker '{self.name}' half-opened")

    def reset(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self._transition_to_closed()

    def get_state(self) -> Dict[str, Any]:
        """Get current state and metrics"""
        with self._lock:
            error_rate = self._calculate_error_rate()

            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'call_count': self.call_count,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'error_rate': error_rate,
                'last_failure_time': self.last_failure_time,
                'last_success_time': self.last_success_time,
                'last_state_change': self.last_state_change,
                'uptime': time.time() - self.last_state_change
            }

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if not self.call_results:
            return 0.0

        failures = sum(1 for result in self.call_results if not result)
        return failures / len(self.call_results)


class CircuitOpenError(Exception):
    """Exception raised when circuit is open"""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers
    """

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        name: str,
        config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)

    def remove(self, name: str):
        """Remove circuit breaker"""
        with self._lock:
            if name in self.breakers:
                del self.breakers[name]

    def get_all_states(self) -> Dict[str, Dict]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self.breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()


# Global registry
_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str = None,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    success_threshold: int = 2
):
    """
    Decorator for adding circuit breaker to functions
    """
    def decorator(func):
        breaker_name = name or f"{func.__module__}.{func.__name__}"

        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout=timeout,
            success_threshold=success_threshold
        )

        breaker = _registry.get_or_create(breaker_name, config)

        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


class RetryPolicy:
    """
    Retry policy for failed operations
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            import random
            delay *= (0.5 + random.random())

        return delay


def with_retry(
    policy: RetryPolicy = None,
    circuit_breaker_name: str = None,
    on_retry: Callable = None
):
    """
    Decorator for adding retry logic with circuit breaker
    """
    if policy is None:
        policy = RetryPolicy()

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(policy.max_retries + 1):
                try:
                    # Use circuit breaker if specified
                    if circuit_breaker_name:
                        breaker = _registry.get_or_create(circuit_breaker_name)
                        return breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except CircuitOpenError:
                    # Don't retry if circuit is open
                    raise

                except Exception as e:
                    last_exception = e

                    if attempt < policy.max_retries:
                        delay = policy.calculate_delay(attempt)

                        logger.warning(
                            f"Retry {attempt + 1}/{policy.max_retries} "
                            f"for {func.__name__} after {delay:.2f}s: {e}"
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}: {e}"
                        )

            raise last_exception

        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(policy.max_retries + 1):
                try:
                    if circuit_breaker_name:
                        breaker = _registry.get_or_create(circuit_breaker_name)
                        return await breaker.call_async(func, *args, **kwargs)
                    else:
                        return await func(*args, **kwargs)

                except CircuitOpenError:
                    raise

                except Exception as e:
                    last_exception = e

                    if attempt < policy.max_retries:
                        delay = policy.calculate_delay(attempt)

                        logger.warning(
                            f"Retry {attempt + 1}/{policy.max_retries} "
                            f"for {func.__name__} after {delay:.2f}s: {e}"
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        import asyncio
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All retries exhausted for {func.__name__}: {e}"
                        )

            raise last_exception

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


class BulkheadIsolation:
    """
    Bulkhead pattern for resource isolation
    """

    def __init__(self, name: str, max_concurrent: int = 10, max_queue: int = 100):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self.semaphore = threading.Semaphore(max_concurrent)
        self.queue_size = 0
        self.queue_lock = threading.Lock()
        self.rejected_count = 0
        self.executed_count = 0

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead isolation"""
        with self.queue_lock:
            if self.queue_size >= self.max_queue:
                self.rejected_count += 1
                raise BulkheadRejectedError(
                    f"Bulkhead '{self.name}' queue is full"
                )
            self.queue_size += 1

        try:
            acquired = self.semaphore.acquire(timeout=30)
            if not acquired:
                raise BulkheadRejectedError(
                    f"Bulkhead '{self.name}' timeout acquiring semaphore"
                )

            try:
                result = func(*args, **kwargs)
                self.executed_count += 1
                return result
            finally:
                self.semaphore.release()

        finally:
            with self.queue_lock:
                self.queue_size -= 1

    def get_stats(self) -> Dict:
        """Get bulkhead statistics"""
        return {
            'name': self.name,
            'max_concurrent': self.max_concurrent,
            'max_queue': self.max_queue,
            'current_queue': self.queue_size,
            'executed': self.executed_count,
            'rejected': self.rejected_count
        }


class BulkheadRejectedError(Exception):
    """Exception raised when bulkhead rejects execution"""
    pass


# Export main functions
def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get circuit breaker by name"""
    return _registry.get(name)


def get_all_circuit_breakers() -> Dict[str, Dict]:
    """Get all circuit breaker states"""
    return _registry.get_all_states()


def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    _registry.reset_all()