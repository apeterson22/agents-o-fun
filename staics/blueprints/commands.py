import platform, subprocess, json
from flask import Blueprint, jsonify, request
from ..jwtutil import jwt_required
from .logs_stream import log_exec_start, log_exec_line

bp = Blueprint("commands", __name__)


def _os():
    sys = platform.system().lower()
    if "linux" in sys:
        return "linux"
    if "darwin" in sys:
        return "mac"
    if "windows" in sys or "cygwin" in sys:
        return "windows"
    return "linux"


_COMMANDS = {
    "echo": {"title": "Echo", "schema": {"args": [{"name": "text", "type": "string", "required": True}]}} ,
    "uptime": {"title": "Uptime", "schema": {"args": []}},
    "sys.network_status": {"title": "Network status", "schema": {"args": []}},
    "sys.open_terminal": {"title": "Open terminal", "schema": {"args": []}},
    "sys.textpad": {"title": "Open text editor", "schema": {"args": [{"name": "file", "type": "string", "required": False}]}}
}


@bp.get("/api/commands")
@jwt_required
def list_commands():
    cmds = [{"id": k, "title": v["title"], "schema": v["schema"]} for k, v in _COMMANDS.items()]
    return jsonify({"commands": cmds, "os": _os()})


def _launch_terminal():
    osname = _os()
    if osname == "linux":
        for cand in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm", "alacritty", "wezterm"):
            if subprocess.call(["bash", "-lc", f"command -v {cand} >/dev/null 2>&1"]) == 0:
                subprocess.Popen([cand])
                return True
        return False
    if osname == "mac":
        subprocess.Popen(["open", "-a", "Terminal"])
        return True
    if osname == "windows":
        subprocess.Popen(["cmd", "/c", "start"], shell=True)
        return True
    return False


def _open_textpad(path=None):
    osname = _os()
    path = path or ""
    if osname == "linux":
        subprocess.Popen(["xdg-open", path or "."])
    elif osname == "mac":
        subprocess.Popen(["open", path or "."])
    else:
        subprocess.Popen(["cmd", "/c", "start", path or "."], shell=True)
    return True


def _shell(cmd):
    out = subprocess.check_output(["bash", "-lc", cmd], stderr=subprocess.STDOUT, timeout=15)
    return out.decode(errors="ignore")


@bp.post("/api/run")
@jwt_required
def run_cmd():
    data = request.get_json(silent=True) or {}
    cmd = data.get("id") or data.get("cmd") or ""
    args = data.get("args") or []
    log_exec_start(getattr(request, "user", "api"), cmd, args)
    try:
        if cmd == "echo":
            txt = str(args[0]) if args else ""
            log_exec_line(json.dumps({"echo": txt}))
            return jsonify({"ok": True, "output": txt})
        elif cmd == "uptime":
            out = _shell("uptime; uname -a")
            for line in out.splitlines():
                log_exec_line(line)
            return jsonify({"ok": True, "output": out})
        elif cmd == "sys.network_status":
            out = _shell("ip -br a || ifconfig -a || true")
            for line in out.splitlines():
                log_exec_line(line)
            return jsonify({"ok": True, "output": out})
        elif cmd == "sys.open_terminal":
            ok = _launch_terminal()
            return jsonify({"ok": ok})
        elif cmd == "sys.textpad":
            target = args[0] if args else ""
            ok = _open_textpad(target)
            return jsonify({"ok": ok})
        else:
            return jsonify({"ok": False, "error": "unknown command"}), 400
    except subprocess.CalledProcessError as e:
        return jsonify({"ok": False, "error": e.output.decode(errors="ignore")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@bp.post("/run")
@jwt_required
def run_compat():
    return run_cmd()
