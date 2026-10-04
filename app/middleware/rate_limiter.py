import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.config import REDIS_URL

# how many requests allowed per window
MAX_REQUESTS = 5

# time window in seconds
TIME_WINDOW = 60


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        # connect to redis
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    async def dispatch(self, request: Request, call_next):

        # only apply rate limit to /chat endpoint
        if request.url.path != "/chat":
            return await call_next(request)

        # read thread_id from header (avoids consuming the request body)
        # Streamlit sends this as X-Thread-ID header
        thread_id = request.headers.get("x-thread-id", None)

        # fallback to IP if header not found
        if thread_id:
            key = f"ratelimit:thread:{thread_id}"
        else:
            client_ip = request.client.host
            key = f"ratelimit:ip:{client_ip}"

        # increment the counter for this session
        count = self.redis_client.incr(key)

        # if this is the first request, set expiry
        if count == 1:
            self.redis_client.expire(key, TIME_WINDOW)

        # if user exceeded the limit, block them
        if count > MAX_REQUESTS:
            seconds_left = self.redis_client.ttl(key)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests! Please slow down.",
                    "retry_after_seconds": seconds_left
                }
            )
        
        # everything is fine, pass the request through
        return await call_next(request)
