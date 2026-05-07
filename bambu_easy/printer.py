"""Printer config loading and live status query (read-only)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ._engine.mqtt_poll import query_printer

CONFIG_FILENAME = "printer_config.json"
TEMPLATE_FILENAME = "printer_config.template.json"


class PrinterConfigError(Exception):
    """Raised when printer_config.json is missing, unreadable, or invalid."""


def repo_root() -> Path:
    """Return the directory containing printer_config.json (CWD-first, then package parent)."""
    cwd_cfg = Path.cwd() / CONFIG_FILENAME
    if cwd_cfg.exists():
        return Path.cwd()
    pkg_parent = Path(__file__).resolve().parent.parent
    return pkg_parent


def config_path() -> Path:
    return repo_root() / CONFIG_FILENAME


def load_config(path: str | os.PathLike | None = None) -> dict[str, str]:
    p = Path(path) if path else config_path()
    if not p.exists():
        raise PrinterConfigError(
            f"{p} not found.\n"
            f"Run setup.sh, or copy {TEMPLATE_FILENAME} to {CONFIG_FILENAME} "
            "and fill in printer_ip, access_code, and serial from Bambu Studio "
            "(Device → Settings → LAN Mode)."
        )
    try:
        cfg = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise PrinterConfigError(f"{p} is not valid JSON: {exc}") from exc
    missing = [k for k in ("printer_ip", "access_code") if not cfg.get(k)]
    if missing:
        raise PrinterConfigError(
            f"{p} is missing required keys: {', '.join(missing)}"
        )
    return cfg


def query(config: dict[str, str] | None = None, timeout: float = 8.0) -> dict[str, Any] | None:
    """Query the printer; return parsed dict or None on offline/timeout."""
    if config is None:
        try:
            config = load_config()
        except PrinterConfigError:
            return None
    return query_printer(
        printer_ip=config["printer_ip"],
        access_code=config["access_code"],
        serial=config.get("serial", ""),
        timeout=timeout,
    )
