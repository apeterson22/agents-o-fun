import time, psutil, os, json
from flask import Blueprint, jsonify, Response
from ..jwtutil import jwt_required

bp = Blueprint("metrics", __name__)


def _gpu_info():
    try:
        import pynvml as nv
        nv.nvmlInit()
        n = nv.nvmlDeviceGetCount()
        arr = []
        for i in range(n):
            h = nv.nvmlDeviceGetHandleByIndex(i)
            mem = nv.nvmlDeviceGetMemoryInfo(h)
            util = nv.nvmlDeviceGetUtilizationRates(h).gpu
            temp = nv.nvmlDeviceGetTemperature(h, nv.NVML_TEMPERATURE_GPU)
            arr.append({
                "index": i,
                "name": nv.nvmlDeviceGetName(h).decode()
                if hasattr(nv.nvmlDeviceGetName(h), "decode")
                else str(nv.nvmlDeviceGetName(h)),
                "mem_total": int(mem.total),
                "mem_used": int(mem.used),
                "util": int(util),
                "temp": int(temp),
            })
        nv.nvmlShutdown()
        return arr
    except Exception:
        return []


def _redis_stats():
    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    try:
        import redis
        r = redis.Redis.from_url(url, socket_connect_timeout=0.2, socket_timeout=0.2)
        info = r.info()
        return {
            "ok": True,
            "used_memory": info.get("used_memory", 0),
            "connected_clients": info.get("connected_clients", 0),
        }
    except Exception:
        return {"ok": False}


@bp.get("/api/metrics/once")
@jwt_required
def once():
    vm = psutil.virtual_memory()
    data = {
        "ts": int(time.time() * 1000),
        "cpu": psutil.cpu_percent(interval=0.05),
        "mem": {"total": vm.total, "used": vm.used, "percent": vm.percent},
        "gpu": _gpu_info(),
        "redis": _redis_stats(),
    }
    return jsonify(data)


@bp.get("/api/metrics/stream")
def stream():
    def gen():
        yield "retry: 2000\n\n"
        while True:
            from ..jwtutil import _extract_token, _secret
            import jwt

            tok = _extract_token()
            if not tok:
                yield "event: error\ndata: missing token\n\n"
                time.sleep(2)
                continue
            try:
                jwt.decode(tok, _secret(), algorithms=["HS256"])
            except Exception:
                yield "event: error\ndata: invalid token\n\n"
                time.sleep(2)
                continue

            vm = psutil.virtual_memory()
            payload = {
                "ts": int(time.time() * 1000),
                "cpu": psutil.cpu_percent(interval=0.25),
                "mem": {"total": vm.total, "used": vm.used, "percent": vm.percent},
                "gpu": _gpu_info(),
                "redis": _redis_stats(),
            }
            yield "event: metrics\ndata: " + json.dumps(payload) + "\n\n"
            time.sleep(1.0)

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
