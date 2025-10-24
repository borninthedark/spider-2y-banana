# Osyraa Test Suite

This directory contains comprehensive tests for the Osyraa Hugo resume application.

## Test Implementations

### Go Test Suite (Recommended)

The Go test suite provides structured, maintainable tests with better error handling and reporting.

**Requirements:**
- Go 1.21 or later
- Docker installed and running
- Hugo (for direct testing, otherwise uses Docker)

**Installation:**
```bash
cd tests
go mod download
```

**Running Tests:**

```bash
# Run all tests
go test -v

# Run specific test suite
go test -v -run TestHugoSuite
go test -v -run TestDockerSuite

# Run with coverage
go test -v -cover

# Run with race detection
go test -v -race

# Generate coverage report
go test -coverprofile=coverage.out
go tool cover -html=coverage.out
```

**Test Suites:**

1. **HugoTestSuite** - Tests Hugo build process
   - Build success verification
   - Output file validation
   - Content verification
   - HTML structure validation
   - Security checks

2. **DockerTestSuite** - Tests Docker image and container
   - Image build verification
   - Image size optimization
   - Container lifecycle management
   - HTTP endpoint testing
   - Security headers validation
   - Performance testing
   - Log analysis

### Bash Test Scripts (Legacy)

The original bash scripts are still available:

```bash
# Test Hugo build
./test_build.sh

# Test Docker container
./test_docker.sh
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run tests
        run: |
          cd osyraa/tests
          go test -v -cover
```

### GitLab CI Example

```yaml
test:
  image: golang:1.21
  services:
    - docker:dind
  script:
    - cd osyraa/tests
    - go mod download
    - go test -v -cover
```

## Test Coverage

The Go test suite covers:

- ✅ Hugo build process
- ✅ Generated file validation
- ✅ Content accuracy
- ✅ HTML structure
- ✅ Docker image building
- ✅ Multi-stage build optimization
- ✅ Container lifecycle
- ✅ HTTP endpoints
- ✅ Security headers
- ✅ Performance metrics
- ✅ Error logging
- ✅ Health checks

## Advantages of Go Tests

1. **Structured Testing**: Uses testify/suite for organized test cases
2. **Better Error Handling**: Proper error propagation and reporting
3. **Parallel Execution**: Can run tests in parallel for speed
4. **Cross-Platform**: Works on Windows, Linux, macOS
5. **IDE Integration**: Better integration with Go IDEs
6. **Type Safety**: Compile-time checking
7. **Maintainability**: Easier to refactor and extend
8. **Docker SDK**: Direct Docker API access vs shell commands
9. **Assertions**: Rich assertion library from testify
10. **Coverage Reports**: Built-in coverage analysis

## Common Issues

### Docker Connection Error
If tests fail with Docker connection errors:
```bash
# Ensure Docker daemon is running
sudo systemctl start docker

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Port Already in Use
If port 8080 is already in use:
```bash
# Find process using port 8080
sudo lsof -i :8080

# Kill the process or change test port in osyraa_test.go
```

### Module Download Issues
If `go mod download` fails:
```bash
# Clear module cache
go clean -modcache

# Try again with verbose output
go mod download -x
```

## Contributing

When adding new tests:

1. Follow Go testing best practices
2. Use testify assertions for clarity
3. Add proper cleanup in TearDown methods
4. Document expected behavior
5. Keep tests independent and idempotent
6. Add meaningful test names and descriptions

## License

Same as parent project.
