import os, subprocess
from flask import Blueprint, jsonify, request
from ..jwtutil import jwt_required

bp = Blueprint("optimize", __name__)


def _scan():
    suggestions = []
    try:
        sw = open("/proc/sys/vm/swappiness", "r").read().strip()
        sw = int(sw)
        if sw > 10:
            suggestions.append({"type": "set_swappiness", "current": sw, "suggested": 10, "why": "reduce swap aggressiveness"})
    except Exception:
        pass
    return suggestions


@bp.get("/api/optimize/scan")
@jwt_required
def scan():
    return jsonify({"ok": True, "suggestions": _scan()})


@bp.post("/api/optimize/apply")
@jwt_required
def apply():
    data = request.get_json(silent=True) or {}
    actions = data.get("actions") or []
    cmds = []
    for a in actions:
        if a.get("type") == "set_swappiness":
            val = int(a.get("value", 10))
            cmds.append(f"sysctl -w vm.swappiness={val}")
            cmds.append(
                f"sed -i -E 's/^vm\\.swappiness=.*/vm.swappiness={val}/' /etc/sysctl.conf || echo 'vm.swappiness={val}' >> /etc/sysctl.conf"
            )
    if os.environ.get("ALLOW_OPTIMIZE_APPLY", "0") in ("1", "true", "yes"):
        outs = []
        for c in cmds:
            try:
                out = subprocess.check_output(["bash", "-lc", c], stderr=subprocess.STDOUT, timeout=10).decode()
                outs.append(out.strip())
            except Exception as e:
                outs.append(str(e))
        return jsonify({"ok": True, "ran": cmds, "output": outs})
    else:
        return jsonify({"ok": False, "dry_run": True, "run_these_with_sudo": cmds})
