# AWS Box Automation Development

This document explains how to prepare a Fedora box for developing `AwsBoxAutomation`.

## Prerequisites

- Fedora 38 or newer
- Visual Studio Code

## Install system dependencies

Installs Python 3.12, Node.js 20 (for the Electron GUI), build tools, and `awscli`.

```bash
sudo dnf update -y
sudo dnf install -y \
  git python3.12 python3.12-devel \
  gcc gcc-c++ libffi-devel openssl-devel make redhat-rpm-config \
  awscli nodejs npm
```

## Configure GitHub SSH access

Generate an SSH key:

```bash
ssh-keygen -t ed25519 -C "maxmin130170@gmail.com"
```

Print the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Add it to GitHub: **Settings → SSH and GPG keys → New SSH key**, paste the output above and save.

Test the connection:

```bash
ssh -T git@github.com
```

Expected output: `Hi maxmin13! You've successfully authenticated...`

## Clone the project

```bash
mkdir ~/Projects && cd ~/Projects
git clone git@github.com:maxmin13/AwsBoxAutomation.git
cd AwsBoxAutomation
```

## Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

> Each new shell starts with no venv active — re-run `source .venv/bin/activate` every time you open a new terminal.

| Layer | Key packages |
| --- | --- |
| **Runtime** (`requirements.txt`) | `ansible` + `ansible-core`, `boto3` / `botocore` (AWS SDK), `moto` (AWS mocking), `docker`, `Jinja2`, `cryptography` |
| **Development** (`requirements-dev.txt`) | `pytest`, `pytest-cov`, `pytest-mock`, `moto`, `black`, `flake8`, `pycodestyle`, `cfn-lint` |

> `awscli` is the only AWS-related tool installed system-wide. The AWS SDK (`boto3`) and Ansible's `amazon.aws` collection are installed inside the venv so their versions are pinned and isolated.

## Electron GUI

The `app/` directory contains an Electron + React desktop GUI for running Make, Provision, and Delete without the command line.

```bash
cd app
npm install
npm start        # builds with Vite then launches Electron
```

> **Linux note:** VSCode sets `ELECTRON_RUN_AS_NODE=1` in its environment, which causes `require('electron')` to return a path string instead of the Electron module. The `start` npm script calls `env -u ELECTRON_RUN_AS_NODE electron .` to unset it before launching. If you run electron directly, unset the variable first: `env -u ELECTRON_RUN_AS_NODE electron .`

| Command | What it does |
| --- | --- |
| `npm start` | Builds with Vite then launches Electron |
| `npm test` | Runs Vitest test suite |

| Package | Purpose |
| --- | --- |
| `electron` | Desktop shell — wraps the React UI in a native window |
| `react` / `react-dom` | UI component library |
| `vite` / `@vitejs/plugin-react` | Bundler and dev build tool |
| `typescript` | Type checking |
| `tailwindcss` / `autoprefixer` / `postcss` | Utility-first CSS |
| `@tailwindcss/typography` | Prose typography styles |
| `cross-env` | Cross-platform env var setting for the `start` script |
| `vitest` | Test runner |
| `@testing-library/react` / `jest-dom` / `user-event` | React component testing utilities |
| `jsdom` | DOM environment for Vitest |

AWS credentials are entered in the **Credentials** tab of the GUI and stored base64-encoded at `~/.config/AwsBoxAutomation/credentials.json`.

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
ansible name_dtc_box -m ping
ansible name_dtc_box -m command -a uptime
ansible name_dtc_box -m command -a "tail /var/log/dmesg"
ansible name_dtc_box -b -K -a "tail /var/log/messages"
ansible name_dtc_box -b -K -m package -a 'name=nginx update_cache=true'
ansible name_dtc_box -m setup
ansible name_dtc_box -m setup -a 'filter=ansible_all_ipv6_addresses'

# Documentation helpers
ansible-doc service
ansible-doc -l | grep ^amazon
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

## AWS credentials

The scripts require three environment variables. Export them before running any `bin/` script directly:

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=eu-west-1
```

When using the GUI these are configured in the **Credentials** tab and passed to the scripts automatically.

To create the credentials, log into the AWS Console → IAM → Users → select the user → Security credentials → Create access key. Associate the user with `AmazonEC2FullAccess` and `AmazonRoute53FullAccess`.

The AWS SDK (`boto3`) and the `amazon.aws` Ansible collection resolve credentials in this order:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`)
2. `~/.aws/credentials` file (set by `aws configure`)
3. IAM instance role (when running on an EC2 instance)

## Verify the environment

```bash
source .venv/bin/activate
python -m pip check
python -c "import com.maxmin.aws; print('imports ok')"
pytest -q
```

## Configure Visual Studio Code

The bootstrap script creates `.vscode/settings.json` and `.vscode/extensions.json` automatically. To configure manually:

```json
// .vscode/settings.json
{
  "files.restoreUndoStack": false,
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "black-formatter.args": ["--line-length=79"],
  "flake8.args": ["--max-line-length=200"]
}
```

| Extension | Purpose |
| --- | --- |
| `ms-python.python` | Core Python support: IntelliSense, debugging, virtual environment management |
| `ms-python.vscode-pylance` | Type-aware language server — auto-complete, type checking, import resolution |
| `ms-python.flake8` | Flake8 linter integration |
| `ms-python.black-formatter` | Black formatter integration |
| `redhat.ansible` | Ansible syntax highlighting, auto-complete, `ansible-lint` |
| `GoogleCloudTools.cloudcode` | Cloud services and Kubernetes tooling |

## Optional automation

Run the bootstrap script to automate the full setup:

```bash
scripts/bootstrap-fedora.sh
```
