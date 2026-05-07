"""Read-only MQTT poll for a Bambu Lab P-series printer.

Pattern extracted from the source workspace's ``Scripts/printer_status.py``
(commit 4a8bb90). We connect over TLS-insecure on port 8883, authenticate
with ``bblp`` + access_code, subscribe to ``device/+/report``, wait a few
seconds for the printer to push a report, and return the parsed payload.

This module is **read-only** — it never publishes commands.
"""
from __future__ import annotations

import json
import ssl
import time
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None  # type: ignore


def parse_ams_data(ams_data: dict) -> list[dict]:
    """Parse AMS tray data into a flat list of spool dicts."""
    spools: list[dict] = []
    for ams_unit in ams_data.get("ams", []) or []:
        ams_id = ams_unit.get("id", "0")
        for tray in ams_unit.get("tray", []) or []:
            try:
                slot_label = f"A{int(ams_id) * 4 + int(tray.get('id', 0)) + 1}"
            except (TypeError, ValueError):
                slot_label = "A?"
            spools.append({
                "slot": slot_label,
                "ams_id": ams_id,
                "tray_id": tray.get("id"),
                "type": tray.get("tray_type", "") or "",
                "sub_brand": tray.get("tray_sub_brands", "") or "",
                "color": tray.get("tray_color", "") or "",
                "remain": tray.get("remain", -1),
                "temp_min": tray.get("nozzle_temp_min", ""),
                "temp_max": tray.get("nozzle_temp_max", ""),
            })
    return spools


def query_printer(
    printer_ip: str,
    access_code: str,
    serial: str = "",
    timeout: float = 8.0,
) -> dict[str, Any] | None:
    """Connect to the printer and wait for one ``device/+/report`` message.

    Returns a dict with keys: ``nozzle_diameter`` (str like "0.4"),
    ``nozzle_type`` (e.g. "HS01"), ``spools`` (list from parse_ams_data),
    and ``raw`` (full payload), or ``None`` on timeout / connection failure.
    """
    if mqtt is None:
        return None

    received: dict[str, Any] = {"data": None, "connected": False, "error": None}

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            received["connected"] = True
            client.subscribe("device/+/report")
        else:
            received["error"] = f"connect rc={rc}"

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except Exception:
            return
        # Need the full print payload (includes ams + nozzle info)
        print_data = data.get("print", {})
        if print_data.get("ams") or "nozzle_diameter" in print_data:
            received["data"] = data
            try:
                client.disconnect()
            except Exception:
                pass

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set("bblp", access_code)
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(printer_ip, 8883, 60)
        except Exception as exc:
            received["error"] = f"connect: {exc}"
            return None
        client.loop_start()
        start = time.time()
        while received["data"] is None and (time.time() - start) < timeout:
            time.sleep(0.2)
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
    except Exception as exc:
        received["error"] = str(exc)
        return None

    if received["data"] is None:
        return None

    print_data = received["data"].get("print", {}) or {}
    ams_data = print_data.get("ams", {}) or {}
    return {
        "nozzle_diameter": str(print_data.get("nozzle_diameter", "")) or None,
        "nozzle_type": print_data.get("nozzle_type") or None,
        "spools": parse_ams_data(ams_data),
        "raw": received["data"],
    }
