"""
Status API endpoints.

GET /api/instances           → list all instances with status
GET /api/instances/{name}     → single instance status + tasks
GET /api/instances/{name}/log → recent log lines
GET /api/instances/{name}/screenshot → PNG screenshot
"""
import io
from datetime import datetime

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

from module.api.utils import api_response, list_instances, get_instance_manager, read_instance_config, _resolve_path
from module.config.utils import filepath_config, read_file


async def list_all_instances(request):
    """
    GET /api/instances
    Return all instances with their current state.
    """
    try:
        names = list_instances()
        result = []
        for name in names:
            mgr = get_instance_manager(name)
            state_map = {1: "running", 2: "idle", 3: "error", 4: "updating"}
            result.append({
                "name": name,
                "alive": mgr.alive,
                "state": state_map.get(mgr.state, "unknown"),
                "state_code": mgr.state,
            })
        return api_response(data=result)
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def get_instance_status(request):
    """
    GET /api/instances/{name}
    Return detailed status of a single instance.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        mgr = get_instance_manager(name)
        state_map = {1: "running", 2: "idle", 3: "error", 4: "updating"}

        # Read config to get next scheduled task info
        config = read_instance_config(name)
        scheduler = config.get("Scheduler", {})

        data = {
            "name": name,
            "alive": mgr.alive,
            "state": state_map.get(mgr.state, "unknown"),
            "state_code": mgr.state,
            "command": scheduler.get("Command", "Unknown"),
            "enable": scheduler.get("Enable", False),
            "next_run": scheduler.get("NextRun", "2000-01-01 00:00:00"),
        }
        return api_response(data=data)
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def get_log(request):
    """
    GET /api/instances/{name}/log?limit=100&offset=0
    Return recent log renderables as plain text lines.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        mgr = get_instance_manager(name)
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))

        from rich.console import Console
        console = Console(no_color=True)
        lines = []
        total = len(mgr.renderables)
        for r in mgr.renderables[offset:offset + limit]:
            with console.capture() as capture:
                console.print(r)
            lines.append(capture.get().rstrip("\n"))

        return api_response(data={
            "lines": lines,
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def get_screenshot(request):
    """
    GET /api/instances/{name}/screenshot
    Return a PNG screenshot of the connected device.

    Strategy: read serial from config, use adbutils to capture screen.
    This works even if ALAS is not currently running.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        config = read_instance_config(name)
        serial = config.get("Emulator", {}).get("Serial", "")
        if not serial:
            return api_response(error="No emulator serial configured", status_code=400)

        import adbutils
        adb = adbutils.adb.device(serial)
        img = adb.screenshot()

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        return api_response(error=str(e), status_code=500)


status_routes = [
    Route("/", endpoint=list_all_instances, methods=["GET"]),
    Route("/{name}", endpoint=get_instance_status, methods=["GET"]),
    Route("/{name}/log", endpoint=get_log, methods=["GET"]),
    Route("/{name}/screenshot", endpoint=get_screenshot, methods=["GET"]),
]
