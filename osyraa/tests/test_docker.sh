#!/bin/bash
set -e

echo "Testing Docker build and container..."

# Test 1: Build Docker image
echo "Test 1: Building Docker image..."
docker build -t resume:test ../

if [ $? -eq 0 ]; then
    echo "✓ Docker image built successfully"
else
    echo "✗ Docker build failed"
    exit 1
fi

# Test 2: Start container
echo "Test 2: Starting container..."
CONTAINER_ID=$(docker run -d -p 8080:80 resume:test)

if [ -n "$CONTAINER_ID" ]; then
    echo "✓ Container started: $CONTAINER_ID"
else
    echo "✗ Failed to start container"
    exit 1
fi

# Wait for container to be ready
echo "Waiting for container to be ready..."
sleep 5

# Test 3: Check if container is running
echo "Test 3: Checking container status..."
if docker ps | grep -q $CONTAINER_ID; then
    echo "✓ Container is running"
else
    echo "✗ Container is not running"
    docker rm -f $CONTAINER_ID
    exit 1
fi

# Test 4: Test HTTP response
echo "Test 4: Testing HTTP endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)

if [ "$HTTP_CODE" == "200" ]; then
    echo "✓ HTTP endpoint responds with 200"
else
    echo "✗ HTTP endpoint returned: $HTTP_CODE"
    docker rm -f $CONTAINER_ID
    exit 1
fi

# Test 5: Check content
echo "Test 5: Verifying content..."
CONTENT=$(curl -s http://localhost:8080/)

if echo "$CONTENT" | grep -q "Princeton A. Strong"; then
    echo "✓ Resume content found in HTTP response"
else
    echo "✗ Resume content not found"
    docker rm -f $CONTAINER_ID
    exit 1
fi

# Test 6: Check security headers
echo "Test 6: Checking security headers..."
HEADERS=$(curl -s -I http://localhost:8080/)

if echo "$HEADERS" | grep -q "X-Frame-Options" && \
   echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    echo "✓ Security headers present"
else
    echo "✗ Security headers missing"
    docker rm -f $CONTAINER_ID
    exit 1
fi

# Cleanup
echo "Cleaning up..."
docker rm -f $CONTAINER_ID
docker rmi resume:test

echo ""
echo "All Docker tests passed! ✓"
