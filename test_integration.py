#!/usr/bin/env python3
"""
Integration test for OpenClaw + specialized agents.
Tests that the skill scripts can successfully communicate with the agent APIs.
"""
import json
import sys
import time
import urllib.request
import urllib.error


def test_api(name: str, url: str, method: str = "GET") -> bool:
    """Test an API endpoint."""
    print(f"Testing {name}...", end=" ")
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("✓")
            return True
    except urllib.error.URLError as e:
        print(f"✗ ({e})")
        return False
    except Exception as e:
        print(f"✗ ({e})")
        return False


def main() -> int:
    print("🧪 Testing OpenClaw + Agents Integration")
    print("=" * 50)
    
    # Check if trading agent is running
    print("\n📈 Trading Agent API Tests")
    print("-" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test Trading Agent endpoints
    endpoints = [
        ("Get Stats", "http://localhost:8081/stats", "GET"),
        ("Get Raw Stats", "http://localhost:8081/stats/raw", "GET"),
    ]
    
    for name, url, method in endpoints:
        tests_total += 1
        if test_api(name, url, method):
            tests_passed += 1
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✅ All integration tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Make sure:")
        print("   1. Trading agent is running (python3 main.py)")
        print("   2. All dependencies are installed (pip3 install -r requirements.txt)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
