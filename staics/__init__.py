import json, os, time, pathlib, pkgutil, importlib
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter


def _client_ip():
    return request.headers.get("X-Real-IP") or request.remote_addr or "0.0.0.0"


def _json_logger(app: Flask):
    @app.after_request
    def _log(resp):
        try:
            app.logger.info(json.dumps({
                "ts": int(time.time()),
                "event": "req",
                "ip": _client_ip(),
                "method": request.method,
                "path": request.path,
                "status": resp.status_code,
            }))
        except Exception:
            pass
        return resp


def _register_all_blueprints(app: Flask):
    pkg_name = "staics.blueprints"
    base = pathlib.Path(__file__).with_name("blueprints")
    if not base.exists():
        return
    for modinfo in pkgutil.iter_modules([str(base)]):
        name = modinfo.name
        try:
            mod = importlib.import_module(f"{pkg_name}.{name}")
            bp = getattr(mod, "bp", None)
            if bp:
                if bp.name in app.blueprints:
                    app.logger.warning("Skipping duplicate blueprint %s", bp.name)
                else:
                    app.register_blueprint(bp)
        except Exception as e:
            app.logger.exception("Failed loading blueprint %s: %s", name, e)


def create_app() -> Flask:
    from dotenv import load_dotenv
    base_dir = pathlib.Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env")

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    limiter = Limiter(key_func=_client_ip, default_limits=["500 per minute"])
    limiter.init_app(app)

    @app.get("/healthz")
    def healthz():
        return jsonify({"name": "S.T.A.I.C.S.", "node": os.uname().nodename, "status": "ok"})

    @app.get("/__routes")
    def routes():
        rules = []
        for r in app.url_map.iter_rules():
            rules.append({"rule": str(r), "methods": sorted([m for m in r.methods if m not in ("HEAD", "OPTIONS")])})
        return jsonify(rules)

    _json_logger(app)
    _register_all_blueprints(app)
    return app
