"""
Test the actual HTTP endpoint to see what error the server returns.
Make sure your server is running first:
  uvicorn app.main:app --reload

Then in ANOTHER terminal, run:
  python test_http.py
"""

import httpx
import json

API_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test if server is reachable."""
    print("=" * 60)
    print("TEST 1: Server Reachable")
    print("=" * 60)
    try:
        r = httpx.get("http://localhost:8000/", timeout=5)
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.json()}")
        print("  ✅ Server is running")
        return True
    except Exception as e:
        print(f"  ❌ Server not reachable: {e}")
        print("  Make sure uvicorn is running!")
        return False


def test_register():
    """Test the register endpoint via HTTP."""
    print("\n" + "=" * 60)
    print("TEST 2: POST /api/v1/auth/register")
    print("=" * 60)

    payload = {
        "email": "httptest@example.com",
        "password": "TestPass123!",
        "first_name": "HTTP",
        "last_name": "Test",
        "organization_name": "HTTP Test Org",
    }

    print(f"  Sending: {json.dumps(payload, indent=4)}")

    try:
        r = httpx.post(
            f"{API_URL}/auth/register",
            json=payload,
            timeout=10,
        )
        print(f"  Status: {r.status_code}")
        print(f"  Headers: {dict(r.headers)}")

        try:
            body = r.json()
            print(f"  Response: {json.dumps(body, indent=4)}")
        except Exception:
            print(f"  Raw Response: {r.text[:500]}")

        if r.status_code == 201:
            print("  ✅ Registration via HTTP: OK")
            return True
        elif r.status_code == 409:
            print("  ⚠️  User already exists (expected if run twice)")
            return True
        else:
            print(f"  ❌ Registration failed with status {r.status_code}")
            return False

    except httpx.ConnectError:
        print("  ❌ Cannot connect to server. Is uvicorn running?")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_cors():
    """Test CORS by simulating a browser preflight."""
    print("\n" + "=" * 60)
    print("TEST 3: CORS Preflight (OPTIONS)")
    print("=" * 60)

    try:
        r = httpx.options(
            f"{API_URL}/auth/register",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=5,
        )
        print(f"  Status: {r.status_code}")
        cors_headers = {
            k: v for k, v in r.headers.items()
            if k.startswith("access-control")
        }
        print(f"  CORS Headers: {json.dumps(cors_headers, indent=4)}")

        if "access-control-allow-origin" in r.headers:
            print("  ✅ CORS preflight: OK")
            return True
        else:
            print("  ❌ No CORS headers — browser will block the request!")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🔍 TrackForge HTTP Endpoint Test\n")

    if not test_health():
        print("\n⛔ Server not running. Start it first.")
        exit(1)

    test_cors()
    test_register()

    print("\n" + "=" * 60)
    print("Done! Check results above.")
    print("=" * 60)
