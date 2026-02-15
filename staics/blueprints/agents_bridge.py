import os, subprocess, yaml, json
from flask import Blueprint, jsonify, request
from ..jwtutil import jwt_required
from .logs_stream import log_exec_start, log_exec_line

bp = Blueprint("agents", __name__)
AGENTS_YAML = os.environ.get("AGENTS_YAML", os.path.join(os.path.dirname(__file__), "..", "agents.yml"))


def _load():
    try:
        with open(AGENTS_YAML, "r") as f:
            y = yaml.safe_load(f) or {}
        return y.get("agents") or []
    except Exception:
        return []


@bp.get("/api/agents")
@jwt_required
def list_agents():
    agents = _load()
    return jsonify({"agents": [{"name": a.get("name"), "desc": a.get("desc", ""), "cmd": a.get("cmd")} for a in agents]})


@bp.post("/api/agents/run")
@jwt_required
def run_agent():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    args = data.get("args") or []
    agents = _load()
    spec = next((a for a in agents if a.get("name") == name), None)
    if not spec:
        return jsonify({"ok": False, "error": "unknown agent"}), 404
    cmd = spec.get("cmd")
    if not cmd:
        return jsonify({"ok": False, "error": "no cmd"}), 400
    log_exec_start(getattr(request, "user", "api"), f"agent:{name}", args)
    try:
        p = subprocess.Popen(cmd + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out_lines = []
        for line in iter(p.stdout.readline, ''):
            line = line.rstrip("\n")
            out_lines.append(line)
            log_exec_line(json.dumps({"agent": name, "line": line}))
        p.wait(timeout=120)
        return jsonify({"ok": p.returncode == 0, "rc": p.returncode, "output": "\n".join(out_lines)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
