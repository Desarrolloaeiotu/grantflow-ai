#!/usr/bin/env python3
"""
Test API endpoints for GLOBAL module
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoints():
    """Test 5 key endpoints"""
    print("Testing GLOBAL Module API Endpoints\n")
    print("=" * 80)

    # Wait for server to start
    time.sleep(2)

    tests = [
        ("GET Organizations", "GET", f"{BASE_URL}/organizations?page=1&size=5"),
        ("GET Organization Detail", "GET", f"{BASE_URL}/organizations/11111111-1111-1111-1111-111111111101"),
        ("GET Tenders (Global)", "GET", f"{BASE_URL}/tenders?region=global&size=5"),
        ("GET Contacts", "GET", f"{BASE_URL}/contacts?size=5"),
        ("Health Check", "GET", "http://localhost:8000/health"),
    ]

    results = []
    for test_name, method, url in tests:
        try:
            if method == "GET":
                resp = requests.get(url, timeout=5)
            else:
                resp = requests.post(url, timeout=5)

            status = "OK" if resp.status_code < 400 else "FAIL"
            results.append((test_name, status, resp.status_code))

            print(f"\n[{status}] {test_name}")
            print(f"    Status: {resp.status_code}")
            if resp.status_code < 400:
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        if "total" in data:
                            print(f"    Total items: {data['total']}")
                        if "items" in data and len(data["items"]) > 0:
                            first = data["items"][0]
                            if isinstance(first, dict):
                                first_name = first.get("name") or first.get("title") or first.get("status")
                                print(f"    First item: {first_name}")
                except:
                    print(f"    Response size: {len(resp.text)} bytes")

        except Exception as e:
            results.append((test_name, "ERROR", str(e)))
            print(f"\n[ERROR] {test_name}")
            print(f"    Exception: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("-" * 80)
    passed = sum(1 for _, status, _ in results if status == "OK")
    print(f"Passed: {passed}/{len(results)}")
    for name, status, result in results:
        print(f"  [{status}] {name}")


if __name__ == "__main__":
    test_endpoints()
