import time
from collections import defaultdict

# In-memory store: { ip_address: [timestamp1, timestamp2, ...] }
_rate_limits = defaultdict(list)

MAX_REQUESTS_PER_HOUR = 10
MAX_REQUESTS_PER_DAY = 50

def check_rate_limit(ip_address: str) -> bool:
    now = time.time()
    
    # Clean up old records (> 24 hours)
    _rate_limits[ip_address] = [t for t in _rate_limits[ip_address] if now - t < 86400]
    
    timestamps = _rate_limits[ip_address]
    
    # Check daily limit
    if len(timestamps) >= MAX_REQUESTS_PER_DAY:
        return False
        
    # Check hourly limit
    hourly_count = sum(1 for t in timestamps if now - t < 3600)
    if hourly_count >= MAX_REQUESTS_PER_HOUR:
        return False
        
    # Add new request
    _rate_limits[ip_address].append(now)
    return True
