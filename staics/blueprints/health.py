from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz():
    import os
    return jsonify({"name": "S.T.A.I.C.S.", "node": os.uname().nodename, "status": "ok"})


@bp.get("/__routes")
def routes():
    from flask import current_app as app
    rules = []
    for r in app.url_map.iter_rules():
        methods = sorted([m for m in r.methods if m not in ("HEAD", "OPTIONS")])
        rules.append({"rule": str(r), "methods": methods})
    return jsonify(rules)
