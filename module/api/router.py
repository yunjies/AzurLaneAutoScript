"""
ALAS REST API Router

All endpoints are mounted under /api via a Starlette Router.
Routes are merged into a single /instances mount to avoid conflicts.
"""
from starlette.routing import Mount, Router

from module.api.config_api import config_routes
from module.api.status_api import status_routes
from module.api.task_api import task_routes

# Merge all routes under one /instances mount
all_instance_routes = status_routes + config_routes + task_routes

api_router = Router([
    Mount("/instances", routes=all_instance_routes),
])
