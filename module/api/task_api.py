"""
Task control API endpoints.

POST /api/instances/{name}/start  → start the scheduler
POST /api/instances/{name}/stop   → stop the scheduler
POST /api/instances/{name}/run    → run a specific task once
POST /api/instances/{name}/reload → reload config from disk
"""
from starlette.requests import Request
from starlette.routing import Route

from module.api.utils import api_response, list_instances, get_instance_manager


async def start_instance(request):
    """
    POST /api/instances/{name}/start
    Start the scheduler loop for an instance.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        mgr = get_instance_manager(name)
        if mgr.alive:
            return api_response(data={"started": False, "reason": "already_running"})
        from module.submodule.utils import get_config_mod
        func = get_config_mod(name)
        mgr.start(func=func)
        return api_response(data={"started": True, "instance": name})
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def stop_instance(request):
    """
    POST /api/instances/{name}/stop
    Stop the scheduler loop for an instance.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        mgr = get_instance_manager(name)
        if not mgr.alive:
            return api_response(data={"stopped": False, "reason": "not_running"})
        mgr.stop()
        return api_response(data={"stopped": True, "instance": name})
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def run_task_once(request):
    """
    POST /api/instances/{name}/run
    Run a specific task command once (not the full scheduler loop).
    Body: {"command": "Main"}
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        body = await request.json()
        command = body.get("command", "")
        if not command:
            return api_response(error="Missing 'command' in body", status_code=400)

        mgr = get_instance_manager(name)
        if mgr.alive:
            return api_response(error="Instance is already running", status_code=409)

        mgr.start(func=command)
        return api_response(data={"run": True, "instance": name, "command": command})
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def reload_config(request):
    """
    POST /api/instances/{name}/reload
    Reload config from disk and refresh the in-memory AzurLaneConfig object.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        from module.submodule.submodule import load_config
        cfg = load_config(name)
        cfg.load()
        return api_response(data={"reloaded": True, "instance": name})
    except Exception as e:
        return api_response(error=str(e), status_code=500)


task_routes = [
    Route("/{name}/start", endpoint=start_instance, methods=["POST"]),
    Route("/{name}/stop", endpoint=stop_instance, methods=["POST"]),
    Route("/{name}/run", endpoint=run_task_once, methods=["POST"]),
    Route("/{name}/reload", endpoint=reload_config, methods=["POST"]),
]
