#!/bin/bash
# Setup Go development tools for autonomous fixing
# Based on config language adapter expectations

set -e

echo "=================================="
echo "Go Tools Setup"
echo "=================================="
echo ""

# Check if sudo is requested
USE_SUDO=""
if [ "$1" = "--sudo" ]; then
    USE_SUDO="sudo"
    echo "Running with sudo for system-wide installation"
else
    echo "Installing to user environment"
fi
echo ""

# Check Go installation
echo "1. Checking Go installation..."
if ! command -v go &> /dev/null; then
    echo "❌ Go not found. Installing Go..."
    echo ""

    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            GO_ARCH="amd64"
            ;;
        aarch64|arm64)
            GO_ARCH="arm64"
            ;;
        *)
            echo "❌ Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    # Detect OS
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')

    # Download and install Go (latest stable)
    GO_VERSION="1.21.5"
    GO_TARBALL="go${GO_VERSION}.${OS}-${GO_ARCH}.tar.gz"

    echo "Downloading Go ${GO_VERSION} for ${OS}-${GO_ARCH}..."
    wget -q "https://go.dev/dl/${GO_TARBALL}" -O "/tmp/${GO_TARBALL}"

    echo "Extracting Go..."
    if [ -n "$USE_SUDO" ]; then
        $USE_SUDO rm -rf /usr/local/go
        $USE_SUDO tar -C /usr/local -xzf "/tmp/${GO_TARBALL}"

        # Add to PATH in profile
        if ! grep -q "/usr/local/go/bin" ~/.profile 2>/dev/null; then
            echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
            echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.profile
        fi

        export PATH=$PATH:/usr/local/go/bin
        export PATH=$PATH:$HOME/go/bin
    else
        # Install to user directory
        mkdir -p ~/go-sdk
        tar -C ~/go-sdk -xzf "/tmp/${GO_TARBALL}"

        if ! grep -q "go-sdk/go/bin" ~/.profile 2>/dev/null; then
            echo 'export PATH=$PATH:$HOME/go-sdk/go/bin' >> ~/.profile
            echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.profile
        fi

        export PATH=$PATH:$HOME/go-sdk/go/bin
        export PATH=$PATH:$HOME/go/bin
    fi

    rm "/tmp/${GO_TARBALL}"

    echo "✅ Go installed"
else
    GO_VERSION=$(go version)
    echo "✅ Found: $GO_VERSION"
fi
echo ""

# Ensure GOPATH is set
if [ -z "$GOPATH" ]; then
    export GOPATH=$HOME/go
    if ! grep -q "GOPATH=" ~/.profile 2>/dev/null; then
        echo 'export GOPATH=$HOME/go' >> ~/.profile
    fi
fi

# Install go vet (built into go, just verify)
echo "2. Verifying go vet (built-in)..."
if go vet -h &> /dev/null; then
    echo "✅ go vet available"
else
    echo "❌ go vet not working"
fi
echo ""

# Install staticcheck (optional linter)
echo "3. Installing staticcheck (optional linter)..."
go install honnef.co/go/tools/cmd/staticcheck@latest

echo "✅ staticcheck installed to $GOPATH/bin/staticcheck"
echo ""

# Install additional useful tools
echo "4. Installing optional tools..."
echo "   - gocyclo (complexity metrics)"
echo "   - golint (additional linting)"

go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
go install golang.org/x/lint/golint@latest

echo "✅ Optional tools installed"
echo ""

# Verify installation
echo "=================================="
echo "Verification"
echo "=================================="
echo ""

echo "Checking installed versions..."
go version
go vet -h &> /dev/null && echo "go vet: OK"

# Check if tools are in PATH
if [ -f "$GOPATH/bin/staticcheck" ] || [ -f "$HOME/go/bin/staticcheck" ]; then
    $HOME/go/bin/staticcheck --version 2>&1 | head -1
else
    echo "⚠️  staticcheck: Installed but not in PATH"
    echo "   Add to PATH: export PATH=\$PATH:\$HOME/go/bin"
fi

if [ -f "$GOPATH/bin/gocyclo" ] || [ -f "$HOME/go/bin/gocyclo" ]; then
    echo "gocyclo: OK"
else
    echo "⚠️  gocyclo: Check installation"
fi

echo ""
echo "✅ Go toolchain setup complete!"
echo ""
echo "Tools installed:"
echo "  - go         (compiler, test runner)"
echo "  - go vet     (built-in static analysis)"
echo "  - staticcheck (advanced linter)"
echo "  - gocyclo    (complexity metrics)"
echo "  - golint     (additional linting)"
echo ""
echo "⚠️  IMPORTANT: Reload your shell or run:"
echo "   source ~/.profile"
echo "   Or restart your terminal"
echo ""
echo "Then run: python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all"
