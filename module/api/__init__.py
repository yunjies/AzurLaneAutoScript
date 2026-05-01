"""
ALAS REST API Module

Provides HTTP endpoints for external control of ALAS instances.
Mounted at /api under the existing Starlette ASGI app.

Design principles:
- Zero business logic duplication: API layer delegates to existing ALAS internals
- Read-only safe: GET endpoints never mutate state
- Configurable CORS: allow mobile web clients on LAN
"""

__version__ = "0.1.0"
