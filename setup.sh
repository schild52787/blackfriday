#!/bin/bash
# Travel Deal Optimizer - Setup Script
# Run: ./setup.sh

set -e  # Exit on error

echo "🚀 Setting up Travel Deal Optimizer..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if command -v uv &> /dev/null; then
        uv venv .venv
    else
        python3 -m venv .venv
    fi
fi
echo -e "${GREEN}✓${NC} Virtual environment ready"

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q pyyaml pytest

echo -e "${GREEN}✓${NC} Dependencies installed"

# Create directories
mkdir -p data reports

# Verify installation
echo "Verifying installation..."
python -m app --cpp 3200 180000 200 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Installation verified"
else
    echo "❌ Verification failed"
    exit 1
fi

# Print success
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Quick start:"
echo "  source .venv/bin/activate"
echo "  python -m app              # Interactive menu"
echo "  python -m app --cpp 800 45000 50  # Quick CPP calc"
echo ""
echo "For Claude Code MCP integration, add to ~/.claude/claude_desktop_config.json:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "travel-deals": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "$PWD"
    }
  }
}
EOF
echo ""
