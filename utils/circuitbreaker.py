from collections import defaultdict
from datetime import datetime



class CircuitBreaker:
    """Implements circuit breaker pattern to prevent repeated failures"""
    
    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = defaultdict(int)
        self.last_failure_time = defaultdict(float)
        self.is_open = defaultdict(bool)

    def record_failure(self, operation_key: str):
        """Record a failure for an operation"""
        current_time = datetime.now().timestamp()
        if current_time - self.last_failure_time[operation_key] > self.reset_timeout:
            self.failures[operation_key] = 1
        else:
            self.failures[operation_key] += 1
        
        self.last_failure_time[operation_key] = current_time
        if self.failures[operation_key] >= self.failure_threshold:
            self.is_open[operation_key] = True

    def record_success(self, operation_key: str):
        """Record a success for an operation"""
        self.failures[operation_key] = 0
        self.is_open[operation_key] = False

    def can_proceed(self, operation_key: str) -> bool:
        """Check if an operation can proceed"""
        if not self.is_open[operation_key]:
            return True
        
        if datetime.now().timestamp() - self.last_failure_time[operation_key] > self.reset_timeout:
            self.is_open[operation_key] = False
            self.failures[operation_key] = 0
            return True
        
        return False
