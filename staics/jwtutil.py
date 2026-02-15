import os, time, functools, jwt
from flask import request, jsonify


def _env(k, d=None):
    return os.environ.get(k, d)


def _secret() -> str:
    s = _env("JWT_SECRET") or _env("SECRET_KEY") or "changeme"
    if s and len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1]
    return s


def issue_token(sub: str, ttl: int = 24 * 3600) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + int(ttl)}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def _extract_token():
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1].strip()
    q = request.args.get("token")
    if q:
        return q.strip()
    try:
        data = request.get_json(silent=True) or {}
        tok = data.get("token")
        if tok:
            return str(tok).strip()
    except Exception:
        pass
    return None


def jwt_required(fn):
    @functools.wraps(fn)
    def _wrap(*args, **kw):
        tok = _extract_token()
        if not tok:
            return jsonify({"error": "missing token"}), 401
        try:
            payload = jwt.decode(tok, _secret(), algorithms=["HS256"])
            request.user = payload.get("sub") or "unknown"
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401
        return fn(*args, **kw)

    return _wrap


require_jwt = jwt_required
token_required = jwt_required
