"""
Update API — REST endpoints for ALAS self-update.

Endpoints:
  GET  /api/update/check   -> {"has_update": bool, "current": sha, "remote": sha}
  POST /api/update/run      -> {"success": bool, "message": str}
"""

import asyncio
import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from module.webui.updater import updater

logger = logging.getLogger("alas.api.update")


def _do_check_update():
    """Run in executor to avoid blocking the event loop."""
    try:
        has_update = updater._check_update()
        # Try to get SHAs for display
        local_sha = ""
        remote_sha = ""
        try:
            local_sha = updater.get_commit("", n=1, short_sha1=True)[0]
        except Exception:
            pass
        if has_update:
            try:
                remote_sha = updater.get_commit("..origin/" + updater.Branch, n=1, short_sha1=True)[0]
            except Exception:
                pass
        return {
            "has_update": bool(has_update),
            "local_sha": local_sha,
            "remote_sha": remote_sha,
        }
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
        return {"has_update": False, "error": str(e)}


async def check_update(request: Request) -> JSONResponse:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _do_check_update)
    return JSONResponse(result)


def _do_run_update():
    """Run git pull + pip install in executor."""
    try:
        success = updater.update()
        return {"success": success, "message": "Update done, restarting..." if success else "Update failed"}
    except Exception as e:
        logger.exception(e)
        return {"success": False, "message": str(e)}


async def run_update(request: Request) -> JSONResponse:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _do_run_update)
    status = 200 if result["success"] else 500
    return JSONResponse(result, status_code=status)
