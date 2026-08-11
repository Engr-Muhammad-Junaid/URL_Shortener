from slowapi import Limiter
from slowapi.util import get_remote_address

# get_remote_address extracts the caller's IP address
# This is how we track "who" is making requests
limiter = Limiter(key_func=get_remote_address)
