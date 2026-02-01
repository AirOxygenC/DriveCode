import time
from functools import wraps

class RateLimiter:
    """
    Rate limiter to prevent exceeding Gemini API limits.
    Limit: 12 requests per minute (to stay safely under 15/min limit)
    """
    def __init__(self, max_requests=12, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times = []
    
    def wait_if_needed(self):
        """
        Check if we need to wait before making another request.
        Implements sliding window rate limiting.
        """
        current_time = time.time()
        
        # Remove requests older than time_window
        self.request_times = [t for t in self.request_times if current_time - t < self.time_window]
        
        if len(self.request_times) >= self.max_requests:
            # Calculate how long to wait
            oldest_request = self.request_times[0]
            wait_time = self.time_window - (current_time - oldest_request)
            if wait_time > 0:
                print(f"⏳ Rate limit: waiting {wait_time:.1f}s before next Gemini request...")
                time.sleep(wait_time + 0.1)  # Add small buffer
        
        # Record this request
        self.request_times.append(time.time())

# Global rate limiter instance
gemini_rate_limiter = RateLimiter(max_requests=12, time_window=60)

def rate_limited(func):
    """
    Decorator to apply rate limiting to Gemini API calls.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gemini_rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper
