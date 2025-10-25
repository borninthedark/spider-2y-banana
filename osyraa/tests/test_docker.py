#!/usr/bin/env python3
"""Podman build and container integration tests."""

import subprocess
import sys
import time
import requests


def run_command(cmd, capture_output=False):
    """Execute a shell command and return result."""
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    return result


def print_test(test_num, message):
    """Print test header."""
    print(f"Test {test_num}: {message}...")


def test_podman_build():
    """Test 1: Build container image with Podman."""
    print_test(1, "Building container image with Podman")
    result = run_command("podman build -t osyraa:test ../")

    if result.returncode == 0:
        print("✓ Container image built successfully")
        return True
    else:
        print("✗ Container build failed")
        return False


def test_start_container():
    """Test 2: Start container."""
    print_test(2, "Starting container")
    result = run_command("podman run -d -p 8080:80 osyraa:test", capture_output=True)

    container_id = result.stdout.strip()

    if container_id:
        print(f"✓ Container started: {container_id}")
        return container_id
    else:
        print("✗ Failed to start container")
        return None


def test_container_running(container_id):
    """Test 3: Check if container is running."""
    print_test(3, "Checking container status")

    # Wait for container to be ready
    print("Waiting for container to be ready...")
    time.sleep(5)

    result = run_command(f"podman ps | grep {container_id}", capture_output=True)

    if result.returncode == 0:
        print("✓ Container is running")
        return True
    else:
        print("✗ Container is not running")
        cleanup_container(container_id)
        return False


def test_http_endpoint(container_id):
    """Test 4: Test HTTP response."""
    print_test(4, "Testing HTTP endpoint")

    try:
        response = requests.get("http://localhost:8080/", timeout=10)

        if response.status_code == 200:
            print("✓ HTTP endpoint responds with 200")
            return True, response.text
        else:
            print(f"✗ HTTP endpoint returned: {response.status_code}")
            cleanup_container(container_id)
            return False, None
    except Exception as e:
        print(f"✗ HTTP request failed: {e}")
        cleanup_container(container_id)
        return False, None


def test_content(content, container_id):
    """Test 5: Check content."""
    print_test(5, "Verifying content")

    if "Princeton A. Strong" in content:
        print("✓ Resume content found in HTTP response")
        return True
    else:
        print("✗ Resume content not found")
        cleanup_container(container_id)
        return False


def test_security_headers(container_id):
    """Test 6: Check security headers."""
    print_test(6, "Checking security headers")

    try:
        response = requests.head("http://localhost:8080/", timeout=10)
        headers = response.headers

        has_xframe = "X-Frame-Options" in headers
        has_xcontent = "X-Content-Type-Options" in headers

        if has_xframe and has_xcontent:
            print("✓ Security headers present")
            return True
        else:
            print("✗ Security headers missing")
            cleanup_container(container_id)
            return False
    except Exception as e:
        print(f"✗ Failed to check headers: {e}")
        cleanup_container(container_id)
        return False


def cleanup_container(container_id):
    """Clean up container resources."""
    print("Cleaning up...")
    run_command(f"podman rm -f {container_id}")
    run_command("podman rmi osyraa:test")


def main():
    """Run all container tests."""
    print("Testing Podman build and container...\n")

    # Test 1: Build image
    if not test_podman_build():
        sys.exit(1)

    # Test 2: Start container
    container_id = test_start_container()
    if not container_id:
        sys.exit(1)

    # Test 3: Container running
    if not test_container_running(container_id):
        sys.exit(1)

    # Test 4: HTTP endpoint
    success, content = test_http_endpoint(container_id)
    if not success:
        sys.exit(1)

    # Test 5: Content check
    if not test_content(content, container_id):
        sys.exit(1)

    # Test 6: Security headers
    if not test_security_headers(container_id):
        sys.exit(1)

    # Cleanup
    cleanup_container(container_id)

    print("\nAll container tests passed! ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
