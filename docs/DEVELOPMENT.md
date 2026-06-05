# AWS Box Automation Development

This document explains how to prepare a Fedora box for developing `AwsBoxAutomation` using a Python virtual environment.

## Prerequisites

- Fedora 38 or newer
- Python 3.11 or newer
- `git`

## Install system dependencies

```bash
sudo dnf update -y
sudo dnf install -y \
  git python3 python3-venv python3-pip python3-devel \
  gcc gcc-c++ libffi-devel openssl-devel make redhat-rpm-config
```

## Clone the project

```bash
git clone <repo-url> AwsBoxAutomation
cd AwsBoxAutomation
```

## Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```


## Formatters and linters

```bash
source .venv/bin/activate

# Lint
flake8 . --max-line-length 200
pycodestyle .

# Format
black --line-length=79 --check .
black --line-length=79 .
```

## Ansible and provisioning

```bash
source .venv/bin/activate
cd provision

# Inventory and configuration
ansible-config list | grep python
ansible-inventory --graph
ansible-inventory --list

# Check hosts
ansible name_guest_box -m ping
ansible name_guest_box -m command -a uptime
ansible name_guest_box -m command -a "tail /var/log/dmesg"
ansible name_guest_box -b -K -a "tail /var/log/syslog"
ansible name_guest_box -b -K -m package -a 'name=nginx update_cache=true'
ansible name_guest_box -m setup
ansible name_guest_box -m setup -a 'filter=ansible_all_ipv6_addresses'

# Documentation helpers
ansible-doc service
ansible-doc -l | grep ^apt
ansible-doc -t inventory amazon.aws.aws_ec2

# Validation
ansible-lint
yamllint playbooks/

# Run playbooks
ansible-playbook -b -K playbooks/upgrade.yml
ansible-playbook -b -K playbooks/python.yml
ansible-playbook -b -K -vvv playbooks/postgresql.yml
ansible-playbook -b -K -vvv playbooks/nginx.yml
```

## Optional: reproducible pins with pip-tools

```bash
pip install pip-tools

pip-compile requirements.in        # generates requirements.txt
pip-compile requirements-dev.in    # generates requirements-dev.txt
pip-sync requirements.txt requirements-dev.txt
```

> Warning: `pip-sync` will remove packages that are not listed in the specified requirements files.

## AWS credentials

Recommended: install `awscli` and run `aws configure`.

```bash
sudo dnf install -y awscli
aws configure
```

Alternatively, export credentials directly for the current shell session:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=...
```

## Verify the environment

```bash
python -m pip check
python -c "import com.maxmin.aws; print('imports ok')"
pytest -q
```

## Recommended housekeeping

- Add `.venv/` to `.gitignore`
- Add a `.env.sample` file for non-secret environment variable names
- Keep runtime and development dependencies separate: `requirements.txt` for runtime and `requirements-dev.txt` for development

## Configure Visual Studio Code for development

Create a `.vscode/settings.json` file in the repository root with at least the following settings:

```json
{
  "files.restoreUndoStack": false,
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=79"]
}
```

If you use Windows or WSL for development, adjust `python.defaultInterpreterPath` to the path of the activated virtual environment interpreter.

Create a `.vscode/extensions.json` file to recommend helpful extensions for this workspace:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "GoogleCloudTools.cloudcode"
  ]
}
```

To install the Cloud Code extension:

1. Open VS Code.
2. Open the Extensions view with `Ctrl+Shift+X`.
3. Search for `Cloud Code`.
4. Install the extension published by `GoogleCloudTools`.

Alternatively, open the Command Palette with `Ctrl+Shift+P`, type `Extensions: Install Extensions`, and enter `GoogleCloudTools.cloudcode`.

When VS Code is running, reload the window after updating `.vscode/settings.json` or `.vscode/extensions.json` so the new workspace settings take effect.

## Optional automation

Run the bootstrap script to automate this setup:

```bash
scripts/bootstrap-fedora.sh
```
