"""
Copy from pywebio.platform.fastapi
"""
import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from pywebio.platform.fastapi import (STATIC_PATH, Session, cdn_validation,
                                      get_free_port,
                                      open_webbrowser_on_server_started,
                                      start_remote_access_service,
                                      webio_routes)
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles


class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache"
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Minimal CORS middleware for mobile web clients on LAN.
    Handles OPTIONS preflight and adds CORS headers to all responses.
    """
    async def dispatch(self, request, call_next):
        # Handle OPTIONS preflight directly
        if request.method == "OPTIONS":
            from starlette.responses import Response
            response = Response(status_code=204)
        else:
            response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response


def asgi_app(
    applications,
    cdn=True,
    static_dir=None,
    debug=False,
    allowed_origins=None,
    check_origin=None,
    **starlette_settings
):
    debug = Session.debug = os.environ.get("PYWEBIO_DEBUG", debug)
    cdn = cdn_validation(cdn, "warn")
    if cdn is False:
        cdn = "pywebio_static"
    routes = webio_routes(
        applications,
        cdn=cdn,
        allowed_origins=allowed_origins,
        check_origin=check_origin,
    )
    if static_dir:
        routes.append(
            Mount("/static", app=StaticFiles(directory=static_dir), name="static")
        )
    routes.append(
        Mount(
            "/pywebio_static",
            app=StaticFiles(directory=STATIC_PATH),
            name="pywebio_static",
        )
    )
    # Mount ALAS REST API under /api
    try:
        from module.api.router import api_router
        routes.append(Mount("/api", app=api_router))
    except Exception as e:
        import logging
        logging.getLogger("alas.api").warning(f"Failed to mount API router: {e}")
    middleware = [Middleware(HeaderMiddleware), Middleware(CORSMiddleware)]
    # Starlette 1.0+ removed on_startup/on_shutdown, use lifespan instead
    on_startup = starlette_settings.pop("on_startup", None)
    on_shutdown = starlette_settings.pop("on_shutdown", None)

    @asynccontextmanager
    async def lifespan(app):
        if on_startup:
            for func in on_startup:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
        yield
        if on_shutdown:
            for func in on_shutdown:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()

    return Starlette(
        routes=routes, middleware=middleware, debug=debug,
        lifespan=lifespan, **starlette_settings
    )


def start_server(
    applications,
    port=0,
    host="",
    cdn=True,
    static_dir=None,
    remote_access=False,
    debug=False,
    allowed_origins=None,
    check_origin=None,
    auto_open_webbrowser=False,
    **uvicorn_settings
):

    app = asgi_app(
        applications,
        cdn=cdn,
        static_dir=static_dir,
        debug=debug,
        allowed_origins=allowed_origins,
        check_origin=check_origin,
    )

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(
            open_webbrowser_on_server_started("localhost", port)
        )

    if not host:
        host = "0.0.0.0"

    if port == 0:
        port = get_free_port()

    if remote_access:
        start_remote_access_service(local_port=port)

    uvicorn.run(app, host=host, port=port, **uvicorn_settings)
