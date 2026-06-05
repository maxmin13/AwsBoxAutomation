#!/usr/bin/env bash
set -euo pipefail

readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Setting up Fedora development environment for AwsBoxAutomation..."

readonly SYSTEM_PACKAGES=(
  git python3 python3-venv python3-pip python3-devel
  gcc gcc-c++ libffi-devel openssl-devel make redhat-rpm-config awscli
)

echo "Installing system packages..."
sudo dnf update -y
sudo dnf install -y "${SYSTEM_PACKAGES[@]}"

echo "Preparing Python virtual environment..."
if [ -d ".venv" ]; then
  echo "Notice: .venv already exists and will be reused."
  python3 -m venv --upgrade .venv
else
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

cat <<'EOF'

Done! The Fedora development environment is ready.
Activate it with:
  source .venv/bin/activate

If you want reproducible pins, install pip-tools inside the activated environment:
  pip install pip-tools
  pip-compile requirements.in
  pip-compile requirements-dev.in
  pip-sync requirements.txt requirements-dev.txt
EOF
