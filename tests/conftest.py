import httpx
from httpx import ASGITransport

# Wrap AsyncClient to accept an `app=` keyword for ASGI testing compatibility
_OriginalAsyncClient = httpx.AsyncClient

class _AsyncClientShim(_OriginalAsyncClient):
    def __init__(self, *args, app=None, **kwargs):
        if app is not None and 'transport' not in kwargs:
            kwargs['transport'] = ASGITransport(app=app)
        super().__init__(*args, **kwargs)

# Apply shim into httpx module so `from httpx import AsyncClient` picks it up
httpx.AsyncClient = _AsyncClientShim
__all__ = ['httpx']
