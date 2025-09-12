import os, bcrypt
from flask import Blueprint, request, jsonify
from ..jwtutil import issue_token

bp = Blueprint("auth", __name__)


def _env(k, d=None):
    return os.environ.get(k, d)


@bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").encode()

    admin_user = _env("ADMIN_USER", "admin")
    pw_hash = _env("ADMIN_PASSWORD_BCRYPT", "")
    if not (username == admin_user and pw_hash and bcrypt.checkpw(password, pw_hash.encode())):
        return jsonify({"status": "error", "error": "bad credentials"}), 401

    token = issue_token(username, int(_env("JWT_TTL", "86400")))
    return jsonify({"status": "success", "token": token})
