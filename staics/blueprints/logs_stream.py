import time, threading, collections, json
from flask import Blueprint, Response
from ..jwtutil import jwt_required, _extract_token, _secret
import jwt

bp = Blueprint("logs_stream", __name__)
_buf = collections.deque(maxlen=500)
_subs = set()
_lock = threading.Lock()


def push_log(obj):
    line = json.dumps(obj)
    with _lock:
        _buf.append(line)
        for q in list(_subs):
            try:
                q.append(line)
            except Exception:
                pass


class QueueLite(list):
    def pop_all(self):
        out = self[:]
        del self[:]
        return out


@bp.get("/api/logs/stream")
def logs_stream():
    def gen():
        yield "retry: 2000\n\n"
        # quick auth
        while True:
            tok = _extract_token()
            if not tok:
                yield "event: error\ndata: missing token\n\n"; time.sleep(2); continue
            try:
                jwt.decode(tok, _secret(), algorithms=["HS256"])
                break
            except Exception:
                yield "event: error\ndata: invalid token\n\n"; time.sleep(2)

        q = QueueLite()
        with _lock:
            _subs.add(q)
        try:
            # send recent history
            for l in list(_buf)[-50:]:
                yield "event: log\ndata: "+l+"\n\n"
            # live
            last_ping = time.time()
            while True:
                if q:
                    for l in q.pop_all():
                        yield "event: log\ndata: "+l+"\n\n"
                now = time.time()
                if now - last_ping > 15:
                    yield f": ping {int(now)}\n\n"
                    last_ping = now
                time.sleep(0.5)
        finally:
            with _lock:
                _subs.discard(q)

    return Response(gen(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# convenience exports
def log_exec_start(user, cmd, args):
    push_log({"ts": int(time.time()), "level": "INFO", "event": "exec_start", "user": user, "cmd": cmd, "args": args})


def log_exec_line(line):
    push_log({"ts": int(time.time()), "level": "INFO", "msg": line})
