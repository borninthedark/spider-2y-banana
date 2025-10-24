#!/bin/bash
set -e

echo "Testing Hugo build..."

# Test 1: Check if Hugo can build successfully
echo "Test 1: Building Hugo site..."
docker run --rm -v $(pwd):/src klakegg/hugo:0.111.3-alpine hugo --minify

if [ -d "public" ]; then
    echo "✓ Hugo build successful - public directory created"
else
    echo "✗ Hugo build failed - public directory not found"
    exit 1
fi

# Test 2: Check if index.html exists
echo "Test 2: Checking for index.html..."
if [ -f "public/index.html" ]; then
    echo "✓ index.html exists"
else
    echo "✗ index.html not found"
    exit 1
fi

# Test 3: Check if resume content is present
echo "Test 3: Verifying resume content..."
if grep -q "Princeton A. Strong" public/index.html; then
    echo "✓ Resume content found"
else
    echo "✗ Resume content not found"
    exit 1
fi

# Test 4: Check for certifications section
echo "Test 4: Checking for certifications..."
if grep -q "Certified Kubernetes Administrator" public/index.html; then
    echo "✓ Certifications section found"
else
    echo "✗ Certifications section not found"
    exit 1
fi

# Test 5: Validate HTML structure
echo "Test 5: Validating HTML structure..."
if grep -q "<!DOCTYPE html>" public/index.html && \
   grep -q "</html>" public/index.html && \
   grep -q "<head>" public/index.html && \
   grep -q "<body>" public/index.html; then
    echo "✓ HTML structure valid"
else
    echo "✗ Invalid HTML structure"
    exit 1
fi

# Cleanup
echo "Cleaning up..."
rm -rf public resources

echo ""
echo "All tests passed! ✓"
