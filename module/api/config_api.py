"""
Config API endpoints.

GET  /api/instances/{name}/config
POST /api/instances/{name}/config
GET  /api/instances/{name}/config/args
"""
from starlette.requests import Request
from starlette.routing import Route

from module.api.utils import api_response, read_instance_config, write_instance_config, list_instances, _resolve_path
from module.config.utils import filepath_args, read_file


async def get_config(request):
    """
    GET /api/instances/{name}/config
    Return the full JSON config of an instance.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        config = read_instance_config(name)
        return api_response(data=config)
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def update_config(request):
    """
    POST /api/instances/{name}/config
    Merge posted JSON into the instance config file.
    Body: application/json — partial or full config object.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return api_response(error="Request body must be a JSON object", status_code=400)

        current = read_instance_config(name)
        if not isinstance(current, dict):
            current = {}

        def deep_merge(base, update):
            for key, value in update.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(current, body)
        write_instance_config(name, current)
        return api_response(data={"updated": True, "instance": name})
    except Exception as e:
        return api_response(error=str(e), status_code=500)


async def get_config_args(request):
    """
    GET /api/instances/{name}/config/args
    Return the argument schema (args.json) for the instance's module.
    """
    name = request.path_params["name"]
    if name not in list_instances():
        return api_response(error=f"Instance '{name}' not found", status_code=404)
    try:
        from module.submodule.utils import get_config_mod
        mod = get_config_mod(name)
        args = read_file(_resolve_path(filepath_args("args", mod)))
        return api_response(data=args)
    except Exception as e:
        return api_response(error=str(e), status_code=500)


config_routes = [
    Route("/{name}/config", endpoint=get_config, methods=["GET"]),
    Route("/{name}/config", endpoint=update_config, methods=["POST"]),
    Route("/{name}/config/args", endpoint=get_config_args, methods=["GET"]),
]
