#!/usr/bin/env python3
"""Hugo build tests."""

import os
import subprocess
import sys
import shutil


def run_command(cmd, capture_output=False):
    """Execute a shell command and return result."""
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    return result


def print_test(test_num, message):
    """Print test header."""
    print(f"Test {test_num}: {message}...")


def test_hugo_build():
    """Test 1: Check if Hugo can build successfully."""
    print_test(1, "Building Hugo site")

    # Get current directory for volume mount
    cwd = os.getcwd()
    cmd = f"podman run --rm -v {cwd}:/src:Z klakegg/hugo:0.111.3-alpine hugo --minify"

    run_command(cmd)

    if os.path.isdir("public"):
        print("✓ Hugo build successful - public directory created")
        return True
    else:
        print("✗ Hugo build failed - public directory not found")
        return False


def test_index_exists():
    """Test 2: Check if index.html exists."""
    print_test(2, "Checking for index.html")

    if os.path.isfile("public/index.html"):
        print("✓ index.html exists")
        return True
    else:
        print("✗ index.html not found")
        return False


def test_resume_content():
    """Test 3: Check if resume content is present."""
    print_test(3, "Verifying resume content")

    try:
        with open("public/index.html", "r") as f:
            content = f.read()

        if "Princeton A. Strong" in content:
            print("✓ Resume content found")
            return True
        else:
            print("✗ Resume content not found")
            return False
    except Exception as e:
        print(f"✗ Failed to read index.html: {e}")
        return False


def test_certifications():
    """Test 4: Check for certifications section."""
    print_test(4, "Checking for certifications")

    try:
        with open("public/index.html", "r") as f:
            content = f.read()

        if "Certified Kubernetes Administrator" in content:
            print("✓ Certifications section found")
            return True
        else:
            print("✗ Certifications section not found")
            return False
    except Exception as e:
        print(f"✗ Failed to read index.html: {e}")
        return False


def test_html_structure():
    """Test 5: Validate HTML structure."""
    print_test(5, "Validating HTML structure")

    try:
        with open("public/index.html", "r") as f:
            content = f.read()

        required_tags = ["<!DOCTYPE html>", "</html>", "<head>", "<body>"]

        all_present = all(tag in content for tag in required_tags)

        if all_present:
            print("✓ HTML structure valid")
            return True
        else:
            print("✗ Invalid HTML structure")
            return False
    except Exception as e:
        print(f"✗ Failed to validate HTML: {e}")
        return False


def cleanup():
    """Clean up build artifacts."""
    print("Cleaning up...")

    for directory in ["public", "resources"]:
        if os.path.exists(directory):
            shutil.rmtree(directory)


def main():
    """Run all Hugo build tests."""
    print("Testing Hugo build...\n")

    # Test 1: Build Hugo site
    if not test_hugo_build():
        sys.exit(1)

    # Test 2: Check index.html
    if not test_index_exists():
        cleanup()
        sys.exit(1)

    # Test 3: Verify resume content
    if not test_resume_content():
        cleanup()
        sys.exit(1)

    # Test 4: Check certifications
    if not test_certifications():
        cleanup()
        sys.exit(1)

    # Test 5: Validate HTML structure
    if not test_html_structure():
        cleanup()
        sys.exit(1)

    # Cleanup
    cleanup()

    print("\nAll tests passed! ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
