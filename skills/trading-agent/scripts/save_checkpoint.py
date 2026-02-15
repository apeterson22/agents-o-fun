#!/usr/bin/env python3
"""Save a checkpoint of the current model state."""
import json
import sys
import urllib.request
import urllib.error


def main() -> int:
    api_url = "http://localhost:8081/checkpoint"
    
    try:
        req = urllib.request.Request(api_url, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(data, indent=2))
            return 0
    except urllib.error.URLError as e:
        print(f"Error connecting to trading agent API: {e}", file=sys.stderr)
        print("Make sure the trading agent is running on port 8081", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
