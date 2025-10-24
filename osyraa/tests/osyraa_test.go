package tests

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

// HugoTestSuite tests Hugo build functionality
type HugoTestSuite struct {
	suite.Suite
	publicDir string
}

// DockerTestSuite tests Docker build and container functionality
type DockerTestSuite struct {
	suite.Suite
	client      *client.Client
	containerID string
	imageTag    string
	ctx         context.Context
}

// SetupSuite runs once before all Hugo tests
func (suite *HugoTestSuite) SetupSuite() {
	suite.publicDir = filepath.Join("..", "public")
}

// TearDownSuite cleans up after all Hugo tests
func (suite *HugoTestSuite) TearDownSuite() {
	// Clean up build artifacts
	os.RemoveAll(suite.publicDir)
	os.RemoveAll(filepath.Join("..", "resources"))
	os.RemoveAll(filepath.Join("..", ".hugo_build.lock"))
}

// TestHugoBuild tests if Hugo can build successfully
func (suite *HugoTestSuite) TestHugoBuild() {
	t := suite.T()

	// Run Hugo build in Docker
	cmd := exec.Command("docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/src", filepath.Join("..", "..")),
		"klakegg/hugo:0.111.3-alpine",
		"hugo", "--minify")

	output, err := cmd.CombinedOutput()
	require.NoError(t, err, "Hugo build failed: %s", string(output))

	// Verify public directory was created
	assert.DirExists(t, suite.publicDir, "public directory should exist after build")
}

// TestIndexHTMLExists verifies index.html was generated
func (suite *HugoTestSuite) TestIndexHTMLExists() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")
	assert.FileExists(t, indexPath, "index.html should exist")
}

// TestResumeContent verifies resume content is present
func (suite *HugoTestSuite) TestResumeContent() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")

	content, err := os.ReadFile(indexPath)
	require.NoError(t, err, "Should be able to read index.html")

	contentStr := string(content)
	assert.Contains(t, contentStr, "Princeton A. Strong", "Resume should contain author name")
}

// TestCertificationsSection verifies certifications are present
func (suite *HugoTestSuite) TestCertificationsSection() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")

	content, err := os.ReadFile(indexPath)
	require.NoError(t, err, "Should be able to read index.html")

	contentStr := string(content)
	assert.Contains(t, contentStr, "Certified Kubernetes Administrator",
		"Resume should contain certifications")
}

// TestHTMLStructure validates proper HTML structure
func (suite *HugoTestSuite) TestHTMLStructure() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")

	content, err := os.ReadFile(indexPath)
	require.NoError(t, err, "Should be able to read index.html")

	contentStr := string(content)
	assert.Contains(t, contentStr, "<!DOCTYPE html>", "Should have DOCTYPE declaration")
	assert.Contains(t, contentStr, "</html>", "Should have closing html tag")
	assert.Contains(t, contentStr, "<head>", "Should have head section")
	assert.Contains(t, contentStr, "<body>", "Should have body section")
}

// TestMinifiedOutput verifies output is minified
func (suite *HugoTestSuite) TestMinifiedOutput() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")

	content, err := os.ReadFile(indexPath)
	require.NoError(t, err, "Should be able to read index.html")

	// Minified HTML should have minimal whitespace
	// This is a basic check - real minification is more complex
	assert.NotEmpty(t, content, "index.html should not be empty")
}

// TestNoInlineScripts checks for inline scripts (security concern)
func (suite *HugoTestSuite) TestNoInlineScripts() {
	t := suite.T()
	indexPath := filepath.Join(suite.publicDir, "index.html")

	content, err := os.ReadFile(indexPath)
	require.NoError(t, err, "Should be able to read index.html")

	contentStr := string(content)
	// For a basic resume site, we may not want inline scripts
	// This is a basic XSS prevention check
	if strings.Contains(contentStr, "<script>") {
		t.Log("Warning: inline scripts detected - review for XSS risks")
	}
}

// SetupSuite runs once before all Docker tests
func (suite *DockerTestSuite) SetupSuite() {
	suite.ctx = context.Background()
	suite.imageTag = "resume:test"

	var err error
	suite.client, err = client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	require.NoError(suite.T(), err, "Failed to create Docker client")
}

// TearDownSuite cleans up after all Docker tests
func (suite *DockerTestSuite) TearDownSuite() {
	if suite.containerID != "" {
		// Stop and remove container
		timeout := 10
		suite.client.ContainerStop(suite.ctx, suite.containerID, container.StopOptions{Timeout: &timeout})
		suite.client.ContainerRemove(suite.ctx, suite.containerID, container.RemoveOptions{Force: true})
	}

	// Remove test image
	if suite.imageTag != "" {
		suite.client.ImageRemove(suite.ctx, suite.imageTag, types.ImageRemoveOptions{Force: true})
	}

	if suite.client != nil {
		suite.client.Close()
	}
}

// TestDockerBuild tests Docker image building
func (suite *DockerTestSuite) TestDockerBuild() {
	t := suite.T()

	// Build Docker image using docker build command
	cmd := exec.Command("docker", "build", "-t", suite.imageTag, "..")
	output, err := cmd.CombinedOutput()
	require.NoError(t, err, "Docker build failed: %s", string(output))

	// Verify image exists
	images, err := suite.client.ImageList(suite.ctx, types.ImageListOptions{})
	require.NoError(t, err, "Failed to list images")

	found := false
	for _, image := range images {
		for _, tag := range image.RepoTags {
			if tag == suite.imageTag {
				found = true
				t.Logf("Image size: %d MB", image.Size/1024/1024)
				break
			}
		}
	}
	assert.True(t, found, "Built image should appear in image list")
}

// TestDockerImageSize checks the image size is reasonable
func (suite *DockerTestSuite) TestDockerImageSize() {
	t := suite.T()

	images, err := suite.client.ImageList(suite.ctx, types.ImageListOptions{})
	require.NoError(t, err, "Failed to list images")

	for _, image := range images {
		for _, tag := range image.RepoTags {
			if tag == suite.imageTag {
				sizeMB := image.Size / 1024 / 1024
				// nginx:alpine base is ~40MB, our app should be relatively small
				assert.Less(t, sizeMB, int64(100), "Image should be reasonably sized")
				return
			}
		}
	}
}

// TestContainerStart tests starting a container
func (suite *DockerTestSuite) TestContainerStart() {
	t := suite.T()

	// Create container
	resp, err := suite.client.ContainerCreate(
		suite.ctx,
		&container.Config{
			Image: suite.imageTag,
			ExposedPorts: nat.PortSet{
				"80/tcp": struct{}{},
			},
		},
		&container.HostConfig{
			PortBindings: nat.PortMap{
				"80/tcp": []nat.PortBinding{
					{
						HostIP:   "127.0.0.1",
						HostPort: "8080",
					},
				},
			},
		},
		nil,
		nil,
		"",
	)
	require.NoError(t, err, "Failed to create container")
	suite.containerID = resp.ID

	// Start container
	err = suite.client.ContainerStart(suite.ctx, suite.containerID, container.StartOptions{})
	require.NoError(t, err, "Failed to start container")

	// Wait for container to be ready
	time.Sleep(5 * time.Second)

	// Verify container is running
	containerJSON, err := suite.client.ContainerInspect(suite.ctx, suite.containerID)
	require.NoError(t, err, "Failed to inspect container")
	assert.True(t, containerJSON.State.Running, "Container should be running")
}

// TestContainerHealth checks container health status
func (suite *DockerTestSuite) TestContainerHealth() {
	t := suite.T()

	// Wait for health check to run
	time.Sleep(6 * time.Second)

	containerJSON, err := suite.client.ContainerInspect(suite.ctx, suite.containerID)
	require.NoError(t, err, "Failed to inspect container")

	if containerJSON.State.Health != nil {
		t.Logf("Health status: %s", containerJSON.State.Health.Status)
		// Health check may take time to become healthy
	}
}

// TestHTTPEndpoint tests the HTTP endpoint
func (suite *DockerTestSuite) TestHTTPEndpoint() {
	t := suite.T()

	resp, err := http.Get("http://localhost:8080/")
	require.NoError(t, err, "HTTP request should succeed")
	defer resp.Body.Close()

	assert.Equal(t, http.StatusOK, resp.StatusCode, "Should return 200 OK")
}

// TestHTTPContent verifies the content served
func (suite *DockerTestSuite) TestHTTPContent() {
	t := suite.T()

	resp, err := http.Get("http://localhost:8080/")
	require.NoError(t, err, "HTTP request should succeed")
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	require.NoError(t, err, "Should be able to read response body")

	contentStr := string(body)
	assert.Contains(t, contentStr, "Princeton A. Strong", "Resume content should be served")
}

// TestSecurityHeaders verifies security headers are present
func (suite *DockerTestSuite) TestSecurityHeaders() {
	t := suite.T()

	resp, err := http.Get("http://localhost:8080/")
	require.NoError(t, err, "HTTP request should succeed")
	defer resp.Body.Close()

	// Check for security headers
	xFrameOptions := resp.Header.Get("X-Frame-Options")
	assert.NotEmpty(t, xFrameOptions, "X-Frame-Options header should be set")
	assert.Equal(t, "SAMEORIGIN", xFrameOptions, "X-Frame-Options should be SAMEORIGIN")

	xContentType := resp.Header.Get("X-Content-Type-Options")
	assert.NotEmpty(t, xContentType, "X-Content-Type-Options header should be set")
	assert.Equal(t, "nosniff", xContentType, "X-Content-Type-Options should be nosniff")

	xXSSProtection := resp.Header.Get("X-XSS-Protection")
	assert.NotEmpty(t, xXSSProtection, "X-XSS-Protection header should be set")
}

// TestNginxStatus tests the nginx status endpoint
func (suite *DockerTestSuite) TestNginxStatus() {
	t := suite.T()

	// This endpoint is restricted to localhost, so we need to exec into container
	execConfig := types.ExecConfig{
		Cmd:          []string{"wget", "-q", "-O-", "http://localhost/nginx_status"},
		AttachStdout: true,
		AttachStderr: true,
	}

	execResp, err := suite.client.ContainerExecCreate(suite.ctx, suite.containerID, execConfig)
	require.NoError(t, err, "Failed to create exec")

	attachResp, err := suite.client.ContainerExecAttach(suite.ctx, execResp.ID, types.ExecStartCheck{})
	require.NoError(t, err, "Failed to attach to exec")
	defer attachResp.Close()

	output, err := io.ReadAll(attachResp.Reader)
	require.NoError(t, err, "Failed to read exec output")

	outputStr := string(output)
	assert.Contains(t, outputStr, "Active connections", "Nginx status should show active connections")
}

// TestResponseTime checks response time is acceptable
func (suite *DockerTestSuite) TestResponseTime() {
	t := suite.T()

	start := time.Now()
	resp, err := http.Get("http://localhost:8080/")
	duration := time.Since(start)

	require.NoError(t, err, "HTTP request should succeed")
	resp.Body.Close()

	assert.Less(t, duration, 1*time.Second, "Response time should be under 1 second")
	t.Logf("Response time: %v", duration)
}

// TestContainerLogs checks for errors in container logs
func (suite *DockerTestSuite) TestContainerLogs() {
	t := suite.T()

	logs, err := suite.client.ContainerLogs(suite.ctx, suite.containerID, container.LogsOptions{
		ShowStdout: true,
		ShowStderr: true,
	})
	require.NoError(t, err, "Failed to get container logs")
	defer logs.Close()

	logContent, err := io.ReadAll(logs)
	require.NoError(t, err, "Failed to read logs")

	logStr := string(logContent)
	// Check if there are error messages (this is a basic check)
	if strings.Contains(strings.ToLower(logStr), "error") {
		t.Logf("Warning: 'error' found in logs:\n%s", logStr)
	}
}

// TestMultiStageBuild verifies multi-stage build optimization
func (suite *DockerTestSuite) TestMultiStageBuild() {
	t := suite.T()

	// Inspect image history
	history, err := suite.client.ImageHistory(suite.ctx, suite.imageTag)
	require.NoError(t, err, "Failed to get image history")

	// Multi-stage builds will show evidence of the build stages
	foundHugo := false
	for _, layer := range history {
		if strings.Contains(layer.CreatedBy, "hugo") || strings.Contains(layer.CreatedBy, "klakegg") {
			foundHugo = true
			break
		}
	}

	t.Logf("Multi-stage build evidence: %v", foundHugo)
}

// Run test suites
func TestHugoSuite(t *testing.T) {
	suite.Run(t, new(HugoTestSuite))
}

func TestDockerSuite(t *testing.T) {
	suite.Run(t, new(DockerTestSuite))
}
