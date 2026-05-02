"""
ALAS MCP Tools — synchronous wrappers around existing API functions.

All functions here are plain sync Python so they can be called directly
from MCP tool handlers (which run in a sync context by default).
"""
import base64
import io
import json
from typing import Any, Dict, List, Optional

from module.api.utils import list_instances, get_instance_manager, read_instance_config, write_instance_config
from module.config.utils import filepath_args, read_file
from module.api.config_api import _resolve_path


def _state_name(code: int) -> str:
    return {1: "running", 2: "idle", 3: "error", 4: "updating"}.get(code, "unknown")


def _get_instance_or_error(name: str) -> tuple:
    """Validate instance name and return (name, manager)."""
    names = list_instances()
    if name not in names:
        raise ValueError(f"Instance '{name}' not found. Available: {names}")
    return name, get_instance_manager(name)


def alas_get_instances() -> str:
    """List all ALAS instances with their current status."""
    names = list_instances()
    result = []
    for name in names:
        mgr = get_instance_manager(name)
        result.append({
            "name": name,
            "alive": mgr.alive,
            "state": _state_name(mgr.state),
            "state_code": mgr.state,
        })
    return json.dumps(result, ensure_ascii=False, indent=2)


def alas_get_instance(name: str) -> str:
    """Get detailed status of a single ALAS instance."""
    name, mgr = _get_instance_or_error(name)
    config = read_instance_config(name)
    scheduler = config.get("Scheduler", {})
    data = {
        "name": name,
        "alive": mgr.alive,
        "state": _state_name(mgr.state),
        "state_code": mgr.state,
        "command": scheduler.get("Command", "Unknown"),
        "enable": scheduler.get("Enable", False),
        "next_run": scheduler.get("NextRun", "2000-01-01 00:00:00"),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def alas_start_instance(name: str) -> str:
    """Start the scheduler loop for an instance."""
    name, mgr = _get_instance_or_error(name)
    if mgr.alive:
        return json.dumps({"started": False, "reason": "already_running", "instance": name})
    from module.submodule.utils import get_config_mod
    func = get_config_mod(name)
    mgr.start(func=func)
    return json.dumps({"started": True, "instance": name})


def alas_stop_instance(name: str) -> str:
    """Stop the scheduler loop for an instance."""
    name, mgr = _get_instance_or_error(name)
    if not mgr.alive:
        return json.dumps({"stopped": False, "reason": "not_running", "instance": name})
    mgr.stop()
    return json.dumps({"stopped": True, "instance": name})


def alas_run_task(name: str, command: str) -> str:
    """Run a specific task command once (not the full scheduler loop)."""
    name, mgr = _get_instance_or_error(name)
    if mgr.alive:
        return json.dumps({"error": "Instance is already running", "instance": name})
    mgr.start(func=command)
    return json.dumps({"run": True, "instance": name, "command": command})


def alas_reload_config(name: str) -> str:
    """Reload config from disk and refresh the in-memory config object."""
    name, _ = _get_instance_or_error(name)
    from module.submodule.submodule import load_config
    cfg = load_config(name)
    cfg.load()
    return json.dumps({"reloaded": True, "instance": name})


def alas_get_config(name: str) -> str:
    """Return the full JSON config of an instance."""
    name, _ = _get_instance_or_error(name)
    config = read_instance_config(name)
    return json.dumps(config, ensure_ascii=False, indent=2)


def alas_update_config(name: str, updates: str) -> str:
    """Merge JSON updates into the instance config file.

    Args:
        updates: A JSON string with partial config to merge.
                 Example: '{"Scheduler": {"Enable": true}}'
    """
    name, _ = _get_instance_or_error(name)
    patch = json.loads(updates)
    if not isinstance(patch, dict):
        raise ValueError("updates must be a JSON object")

    current = read_instance_config(name)
    if not isinstance(current, dict):
        current = {}

    def deep_merge(base: dict, update: dict):
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(current, patch)
    write_instance_config(name, current)
    return json.dumps({"updated": True, "instance": name})


def alas_get_config_args(name: str) -> str:
    """Return the argument schema (args.json) for the instance's module."""
    name, _ = _get_instance_or_error(name)
    from module.submodule.utils import get_config_mod
    mod = get_config_mod(name)
    args = read_file(_resolve_path(filepath_args("args", mod)))
    return json.dumps(args, ensure_ascii=False, indent=2)


def alas_get_log(name: str, limit: int = 100, offset: int = 0) -> str:
    """Return recent log lines as plain text."""
    name, mgr = _get_instance_or_error(name)
    from rich.console import Console
    console = Console(no_color=True)
    lines = []
    total = len(mgr.renderables)
    for r in mgr.renderables[offset:offset + limit]:
        with console.capture() as capture:
            console.print(r)
        lines.append(capture.get().rstrip("\n"))
    return json.dumps({
        "lines": lines,
        "total": total,
        "limit": limit,
        "offset": offset,
    }, ensure_ascii=False, indent=2)


def alas_get_screenshot(name: str) -> str:
    """Return a base64-encoded PNG screenshot of the connected device."""
    name, _ = _get_instance_or_error(name)
    config = read_instance_config(name)
    serial = config.get("Emulator", {}).get("Serial", "")
    if not serial:
        raise ValueError("No emulator serial configured")

    import adbutils
    adb = adbutils.adb.device(serial)
    img = adb.screenshot()

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return json.dumps({
        "image_base64": b64,
        "format": "png",
        "serial": serial,
    }, ensure_ascii=False, indent=2)


# Tool schema definitions for MCP server registration
TOOL_SCHEMAS = [
    {
        "name": "alas_get_instances",
        "description": "List all ALAS instances with their current status (alive, state, etc.)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "alas_get_instance",
        "description": "Get detailed status of a single ALAS instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name, e.g. 'alas'"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_start_instance",
        "description": "Start the scheduler loop for an ALAS instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_stop_instance",
        "description": "Stop the scheduler loop for an ALAS instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_run_task",
        "description": "Run a specific task command once (not the full scheduler loop). Common commands: Main, Commission, Research, Dorm, Guild, Gacha, Reward, Exercise, Daily, Hard, Event, WarArchives, Raid, MaritimeEscort, Sos, Coalition, Main2, Event2, Main3, Event3",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
                "command": {"type": "string", "description": "Task command to run, e.g. 'Main' or 'Commission'"},
            },
            "required": ["name", "command"],
        },
    },
    {
        "name": "alas_reload_config",
        "description": "Reload config from disk for an instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_get_config",
        "description": "Get the full JSON config of an instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_update_config",
        "description": "Merge JSON updates into an instance config (deep merge). Example updates: '{\"Scheduler\":{\"Enable\":true}}' or '{\"Main\":{\"Command\":\"Main\"}}'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
                "updates": {"type": "string", "description": "JSON string with partial config to merge"},
            },
            "required": ["name", "updates"],
        },
    },
    {
        "name": "alas_get_config_args",
        "description": "Get the argument schema (args.json) for the instance's module",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_get_log",
        "description": "Get recent log lines of an instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
                "limit": {"type": "integer", "description": "Max lines to return (default 100)", "default": 100},
                "offset": {"type": "integer", "description": "Line offset (default 0)", "default": 0},
            },
            "required": ["name"],
        },
    },
    {
        "name": "alas_get_screenshot",
        "description": "Capture a screenshot of the connected Android device (returns base64 PNG)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Instance name"},
            },
            "required": ["name"],
        },
    },
]


# Map tool name -> callable
TOOL_MAP = {
    "alas_get_instances": alas_get_instances,
    "alas_get_instance": alas_get_instance,
    "alas_start_instance": alas_start_instance,
    "alas_stop_instance": alas_stop_instance,
    "alas_run_task": alas_run_task,
    "alas_reload_config": alas_reload_config,
    "alas_get_config": alas_get_config,
    "alas_update_config": alas_update_config,
    "alas_get_config_args": alas_get_config_args,
    "alas_get_log": alas_get_log,
    "alas_get_screenshot": alas_get_screenshot,
}
