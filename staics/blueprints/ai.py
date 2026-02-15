from flask import Blueprint, request, jsonify, Response
from ..jwtutil import jwt_required

bp = Blueprint("ai", __name__)


@bp.get("/api/ai/config")
@jwt_required
def ai_config():
    return jsonify({"provider": "local", "model": "staics-agent", "streaming": True})


@bp.post("/api/ai/chat")
@jwt_required
def ai_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    # Simple bot: mirror with system hint
    reply = f"[main-agent] You said: {msg}"
    return jsonify({"ok": True, "reply": reply})


@bp.get("/api/chat/stream")
def chat_stream():
    # SSE streaming "tokens" from a trivial reply
    from ..jwtutil import _extract_token, _secret
    import jwt, time

    tok = _extract_token()
    try:
        jwt.decode(tok, _secret(), algorithms=["HS256"])
    except Exception:
        return Response("event: error\ndata: invalid token\n\n", mimetype="text/event-stream")
    q = (request.args.get("q") or "").strip()
    text = f"[main-agent] You said: {q}"

    def gen():
        yield "retry: 2000\n\n"
        for ch in text:
            yield "event: delta\ndata: " + ch + "\n\n"
            time.sleep(0.01)
        yield "event: done\ndata: ok\n\n"

    return Response(gen(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
