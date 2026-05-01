"""
Common utilities for the REST API layer.
"""
import json
import os
from starlette.responses import JSONResponse
from module.config.utils import filepath_config, read_file
from module.webui.process_manager import ProcessManager

# Resolve ALAS root directory once at import time
_ALAS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_path(relative_path: str) -> str:
    """Convert a relative path (like ./config/alas.json) to absolute using ALAS root."""
    if os.path.isabs(relative_path):
        return relative_path
    return os.path.normpath(os.path.join(_ALAS_ROOT, relative_path))


def api_response(data=None, error=None, status_code=200):
    """
    Standard JSON response wrapper.
    """
    body = {"success": error is None, "data": data}
    if error is not None:
        body["error"] = str(error)
    return JSONResponse(content=body, status_code=status_code)


def list_instances():
    """
    Return all config instance names found in ./config/
    """
    from module.config.utils import alas_instance
    return alas_instance()


def get_instance_manager(name: str):
    """
    Get or create a ProcessManager for a config instance.
    """
    return ProcessManager.get_manager(name)


def read_instance_config(name: str):
    """
    Read the raw JSON config for an instance.
    Uses absolute path to avoid CWD issues in subprocess.
    """
    path = _resolve_path(filepath_config(name))
    return read_file(path)


def write_instance_config(name: str, data: dict):
    """
    Write the raw JSON config for an instance.
    Uses absolute path to avoid CWD issues in subprocess.
    """
    from module.config.utils import write_file
    path = _resolve_path(filepath_config(name))
    write_file(path, data)
    return True
