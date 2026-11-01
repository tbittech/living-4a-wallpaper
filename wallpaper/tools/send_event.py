"""Manda eventos a mano al servidor del wallpaper (pruebas).

    python wallpaper/tools/send_event.py tool_call --tool Bash
    python wallpaper/tools/send_event.py request_start --source codex --port 8775
    python wallpaper/tools/send_event.py --state          (muestra el snapshot)
"""

import argparse
import json
import time
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("type", nargs="?", help="session_start, request_start, tool_call, tool_result, turn_end, session_end...")
    ap.add_argument("--source", default="claude")
    ap.add_argument("--session", default="manual")
    ap.add_argument("--tool")
    ap.add_argument("--status", type=int)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--state", action="store_true", help="mostrar GET /state")
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    if args.state or not args.type:
        print(json.dumps(json.load(urllib.request.urlopen(f"{base}/state", timeout=2)), indent=2))
        return
    ev = {"source": args.source, "session": args.session, "type": args.type, "ts": int(time.time() * 1000)}
    if args.tool:
        ev["tool"] = args.tool
    if args.status:
        ev["status"] = args.status
    req = urllib.request.Request(f"{base}/event", json.dumps(ev).encode(), {"Content-Type": "application/json"})
    print(urllib.request.urlopen(req, timeout=2).read().decode())


if __name__ == "__main__":
    main()
