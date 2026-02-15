import os

from flask import Blueprint, jsonify
from ..jwtutil import jwt_required

bp = Blueprint("models", __name__)


def _walk(base):
    res = []
    for root, dirs, files in os.walk(base):
        for f in files:
            try:
                p = os.path.join(root, f)
                st = os.stat(p)
                res.append({"path": p.replace(base + "/", ""), "bytes": st.st_size})
            except Exception:
                pass
    return res


@bp.get("/api/models/inventory")
@jwt_required
def inv():
    base = os.environ.get("MODELS_DIR", "/models")
    if not os.path.isdir(base):
        return jsonify({"ok": False, "error": "MODELS_DIR missing", "dir": base, "files": []})
    return jsonify({"ok": True, "dir": base, "files": _walk(base)})
