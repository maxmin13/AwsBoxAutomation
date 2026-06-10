#!/usr/bin/env bash
# Bootstraps a Fedora development environment for AwsBoxAutomation.
#
# What it does:
#   1. Updates system packages and installs build tools, Python 3, Node.js, and awscli
#   2. Generates an SSH key for GitHub access (if not present)
#   3. Creates (or upgrades) a Python virtual environment at .venv/
#   4. Adds .venv/ to .gitignore (if not already present)
#   5. Installs runtime and development dependencies from requirements*.txt
#   6. Installs Electron GUI dependencies (app/node_modules/)
#   7. Creates .vscode/settings.json and .vscode/extensions.json (if not present)
#   8. Installs recommended VS Code extensions (if 'code' CLI is available)
#   9. Verifies the environment with pip check
#
# After running this script:
#   - If a new SSH key was generated, add the displayed public key to GitHub:
#       GitHub → Settings → SSH and GPG keys → New SSH key
#   - Activate the venv with: source .venv/bin/activate
#   - Configure AWS credentials with: aws configure
#   - Sign in to Claude Code: Ctrl+Shift+P → Claude Code: Sign In
set -euo pipefail

readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Setting up Fedora development environment for AwsBoxAutomation..."

# --- System packages ---
readonly SYSTEM_PACKAGES=(
  git python3.12 python3.12-devel
  gcc gcc-c++ libffi-devel openssl-devel make redhat-rpm-config
  awscli nodejs npm
)

echo "Installing system packages..."
sudo dnf update -y
sudo dnf install -y "${SYSTEM_PACKAGES[@]}"

# --- SSH key ---
echo "Configuring GitHub SSH access..."
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
  ssh-keygen -t ed25519 -C "maxmin130170@gmail.com" -f "$HOME/.ssh/id_ed25519" -N ""
  echo ""
  echo "SSH key generated. Add this public key to GitHub (Settings → SSH and GPG keys → New SSH key):"
  echo ""
  cat "$HOME/.ssh/id_ed25519.pub"
  echo ""
else
  echo "Notice: SSH key already exists at ~/.ssh/id_ed25519, skipping."
fi

# --- Python virtual environment ---
echo "Preparing Python virtual environment..."
if [ -d ".venv" ]; then
  echo "Notice: .venv already exists and will be reused."
  python3.12 -m venv --upgrade .venv
else
  python3.12 -m venv .venv
fi

# --- .gitignore ---
if ! grep -qxF '.venv/' .gitignore 2>/dev/null && ! grep -qxF '.venv' .gitignore 2>/dev/null; then
  echo ".venv/" >> .gitignore
  echo "Added .venv/ to .gitignore."
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# --- Electron GUI dependencies ---
echo "Installing Electron GUI dependencies..."
npm install --prefix app

# --- VS Code workspace settings ---
echo "Creating VS Code workspace settings..."
mkdir -p .vscode

if [ ! -f ".vscode/settings.json" ]; then
  cat > .vscode/settings.json <<'SETTINGS'
{
  "files.restoreUndoStack": false,
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "black-formatter.args": ["--line-length=79"],
  "flake8.args": ["--max-line-length=200"]
}
SETTINGS
  echo "Created .vscode/settings.json."
else
  echo "Notice: .vscode/settings.json already exists, skipping."
fi

if [ ! -f ".vscode/extensions.json" ]; then
  cat > .vscode/extensions.json <<'EXTENSIONS'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "redhat.ansible",
    "GoogleCloudTools.cloudcode"
  ]
}
EXTENSIONS
  echo "Created .vscode/extensions.json."
else
  echo "Notice: .vscode/extensions.json already exists, skipping."
fi

# --- VS Code extensions ---
if command -v code &>/dev/null; then
  echo "Installing recommended VS Code extensions..."
  code --install-extension ms-python.python
  code --install-extension ms-python.vscode-pylance
  code --install-extension ms-python.flake8
  code --install-extension ms-python.black-formatter
  code --install-extension redhat.ansible
  code --install-extension GoogleCloudTools.cloudcode
else
  echo "Notice: 'code' CLI not found — install VS Code extensions manually via Ctrl+Shift+X."
fi

# --- Verify ---
echo "Verifying the environment..."
python -m pip check
echo "pip check passed."

cat <<'EOF'

Done! The Fedora development environment is ready.

Next steps:
  1. Activate the venv:        source .venv/bin/activate
  2. Configure AWS credentials: aws configure
  3. Sign in to Claude Code:   Ctrl+Shift+P → Claude Code: Sign In

If a new SSH key was generated, add the public key shown above to GitHub:
  GitHub → Settings → SSH and GPG keys → New SSH key
  Then test with: ssh -T git@github.com
EOF
