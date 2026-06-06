#!/usr/bin/env bash
# Bootstraps a Fedora development environment for AwsBoxAutomation.
#
# What it does:
#   1. Updates system packages and installs build tools, Python 3, and awscli
#   2. Creates (or upgrades) a Python virtual environment at .venv/
#   3. Installs runtime and development dependencies from requirements*.txt
#
# After running this script:
#   - Activate the venv with: source .venv/bin/activate
#   - Configure AWS credentials with: aws configure
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

Configure AWS credentials with:
  aws configure
EOF
