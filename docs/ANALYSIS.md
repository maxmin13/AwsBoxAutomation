# AwsBoxAutomation — Project Analysis

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AWS infrastructure | Python + boto3 |
| Configuration | JSON (`config/`) |
| Instance bootstrap | cloud-init (`cloudinit.yml.j2`) |
| Provisioning | Ansible + `amazon.aws` collection |
| Ansible inventory | Dynamic — `aws_ec2` plugin |
| Playbook variables | YAML (`variables/provision.yml`, `variables/secrets.yml`) |
| Entry-point scripts | Bash (`bin/`) |
| Unit tests | pytest + moto (AWS mocking) |
| Linter | flake8, pycodestyle |
| Formatter | black |
| Dev environment setup | `scripts/bootstrap-fedora.sh` |

---

## Architecture

```
AwsBoxAutomation/
  bin/
    make.sh                  <- creates the AWS datacenter (VPC, subnet, security group, EC2 instance, DNS)
    provision.sh             <- provisions the instance by running all Ansible playbooks in order
    delete.sh                <- tears down the entire datacenter
    test/
      tests.sh               <- activates the venv and runs pytest
  config/
    datacenter.json          <- VPC, subnet, security group, instance parameters
    hostedzone.json          <- Route 53 hosted zone and registered domain
  project/
    constants/
      ec2.ini                <- instance type, device, and volume size constants
    src/
      com/maxmin/aws/        <- Python boto3 source (startup.py, shutdown.py, ...)
    templates/
      cloudinit.yml.j2       <- cloud-init template: creates the OS user, sets the hostname, bootstraps packages
    tests/
      config/
        test_datacenter.json <- test fixtures mirroring config/datacenter.json
        test_hostedzone.json <- test fixtures mirroring config/hostedzone.json
      test_smoke.py          <- placeholder smoke test
  provision/
    ansible.cfg              <- SSH transport, dynamic inventory plugin, log path
    inventory/
      aws_ec2.yml            <- dynamic inventory: groups instances by EC2 tags
      group_vars/
        all                  <- connection settings applied to every host
        name_dtc_box         <- per-instance SSH key, user, and password; reads DATACENTER_DIR
    playbooks/
      upgrade.yml            <- yum update + base package install
      openssl.yml            <- builds OpenSSL 1.1.1u from source
      python.yml             <- builds Python 3.11.4 from source
      docker.yml             <- installs Docker CE
      java.yml               <- installs OpenJDK 18
      tomcat.yml             <- installs Tomcat 10
      nginx.yml              <- installs and configures Nginx (HTTP + HTTPS)
      postgresql.yml         <- installs PostgreSQL 14
      mariadb.yml            <- installs MariaDB 10.5
      phpmyadmin.yml         <- installs phpMyAdmin
      variables/
        provision.yml        <- all version numbers, URLs, and paths used by the playbooks
        secrets.yml          <- service usernames and passwords (not encrypted)
      files/
        requirements.txt     <- Python packages installed inside the EC2 instance venv
  scripts/
    bootstrap-fedora.sh      <- one-shot developer setup: dnf packages, SSH key, venv, VS Code config
  access/                    <- SSH private key for the instance (gitignored)
  .venv/                     <- Python virtual environment (gitignored)
  requirements.txt           <- runtime dependencies: boto3, ansible, moto, Jinja2, docker, cryptography
  requirements-dev.txt       <- dev-only: pytest, pytest-cov, pytest-mock, moto, black, flake8, cfn-lint
  pytest.ini                 <- test discovery config; testpaths = project/tests tests
```

---

## Configuration

### `config/datacenter.json`

Single source of truth for all AWS resource names and parameters.

| Key path | Value | Purpose |
|----------|-------|---------|
| `Datacenter.VPC.Name` | `dtc-datacenter` | VPC name tag |
| `Datacenter.VPC.Cidr` | `10.0.0.0/16` | VPC address space |
| `Datacenter.VPC.Region` | `eu-west-1` | AWS region |
| `Datacenter.Subnets[0].Az` | `eu-west-1a` | Availability zone |
| `Datacenter.Subnets[0].Cidr` | `10.0.20.0/24` | Subnet address space |
| `Datacenter.SecurityGroups[0].Rules` | ICMP, 22, 8080, 8443, 5432 | Open inbound ports |
| `Datacenter.Instances[0].Name` | `dtc-box` | EC2 name tag; also used by Ansible as `instance_name` |
| `Datacenter.Instances[0].PrivateIp` | `10.0.20.35` | Static private IP |
| `Datacenter.Instances[0].ParentImage` | `amzn2-ami-kernel-5.10-...` | AMI name (Amazon Linux 2) |
| `Datacenter.Instances[0].DnsDomain` | `dtc.maxmin.it` | Public DNS name |

### `config/hostedzone.json`

| Key | Value |
|-----|-------|
| `HostedZone.RegisteredDomain` | `maxmin.it` |

### `project/constants/ec2.ini`

| Key | Value |
|-----|-------|
| `instance_type` | `t3.micro` |
| `volume_size` | `10` (GB) |
| `device` | `/dev/xvda` |

### `provision/playbooks/variables/provision.yml`

Centralises all version numbers, download URLs, and remote paths used across every playbook. Playbooks reference values via the `aws.instance.*` namespace (e.g. `aws.instance.python.version`, `aws.instance.nginx.https.port`).

### `provision/playbooks/variables/secrets.yml`

Service credentials (Tomcat admin, PostgreSQL superuser, MariaDB root password, Tomcat keystore). Currently stored in plaintext — see [Gaps](#gaps--improvement-areas).

---

## Credential Requirements

All three entry-point scripts (`make.sh`, `provision.sh`, `delete.sh`) validate that these environment variables are set before doing anything:

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
```

The SSH private key for Ansible is expected at `access/<instance_name>` (e.g. `access/admin-box`). The `access/` directory is gitignored.

---

## How to Run

All commands from the repository root.

| Command | What it does |
|---------|-------------|
| `scripts/bootstrap-fedora.sh` | One-time dev environment setup |
| `source .venv/bin/activate` | Activate the Python venv (required before any other command) |
| `bin/make.sh` | Create the datacenter on AWS |
| `bin/provision.sh` | Run all Ansible playbooks against the running instance |
| `bin/delete.sh` | Delete all AWS resources |
| `bin/test/tests.sh` | Run the pytest suite |
| `pytest -q` | Same, run directly from an active venv |

AWS credentials must be exported before running any script:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=eu-west-1
```

---

## Pipeline

### Phase 1 — `make.sh` (infrastructure)

Calls `project/src/com/maxmin/aws/startup.py` with `config/datacenter.json` and `config/hostedzone.json`. The Python code uses boto3 to create:

1. VPC with CIDR `10.0.0.0/16`
2. Internet Gateway attached to the VPC
3. Route table with a default route to the gateway
4. Subnet `10.0.20.0/24` in `eu-west-1a`
5. Security group with inbound rules for ICMP, SSH (22), HTTP (8080), HTTPS (8443), PostgreSQL (5432)
6. EC2 instance (`t3.micro`, Amazon Linux 2) bootstrapped via cloud-init
7. Route 53 DNS A record pointing `dtc.maxmin.it` at the instance's public IP

### Phase 2 — `provision.sh` (software)

Runs each playbook sequentially via `ansible-playbook`. Ansible connects over SSH using the dynamic inventory (EC2 tags → groups). Playbook execution order:

| Step | Playbook | What it installs |
|------|----------|-----------------|
| 1 | `upgrade.yml` | `yum update`, base packages (git, vim, supervisor, python3-devel) |
| 2 | `openssl.yml` | OpenSSL 1.1.1u from source |
| 3 | `python.yml` | Python 3.11.4 from source |
| 4 | `docker.yml` | Docker CE 25 + Docker Compose |
| 5 | `phpmyadmin.yml` | phpMyAdmin on port 8000 |
| 6 | `postgresql.yml` | PostgreSQL 14 |
| 7 | `nginx.yml` | Nginx with self-signed TLS on ports 8080/8443 |
| 8 | `java.yml` | OpenJDK 18 |
| 9 | `tomcat.yml` | Tomcat 10.1.23 with TLS keystore |
| 10 | `mariadb.yml` | MariaDB 10.5 |

Each playbook checks whether the software is already installed and skips installation if it is (idempotent).

### Phase 3 — `delete.sh` (teardown)

Calls `project/src/com/maxmin/aws/shutdown.py`. Reverses phase 1 — deletes resources in the correct dependency order.

---

## Ansible Inventory

The `aws_ec2` dynamic inventory plugin queries AWS at runtime and groups instances by EC2 tags:

| Group prefix | Tag key | Example group |
|---|---|---|
| `name_` | `tags.name` | `name_dtc_box` |
| `class_` | `tags.class` | `class_webservices` |
| `database_` | `tags.database` | `database_postgresql` |
| `webserver_` | `tags.webserver` | `webserver_nginx` |
| `common_` | `tags.common` | `common_programs` |

Playbooks target specific groups (e.g. `hosts: webserver_nginx`) so they only run on instances that carry the relevant tag. Instances not tagged `webserver: nginx` are silently skipped by `nginx.yml`.

`compose: ansible_host: public_ip_address` maps the Ansible connection address to the instance's public IP (resolved dynamically at run time).

---

## cloud-init (`project/templates/cloudinit.yml.j2`)

Applied when the EC2 instance first boots. Variables (`username`, `hashed_password`, `public_key`, `hostname`) are rendered by the Python boto3 code before the instance is launched.

What it does:
- Creates the OS user with sudo access and password authentication enabled
- Injects the SSH public key
- Sets the hostname
- Runs `yum update` and installs `git`
- Installs `ansible2` via `amazon-linux-extras`

---

## Unit Tests

Tests live in `project/tests/` and are discovered by pytest via `pytest.ini` (`testpaths = project/tests tests`).

| File | What it tests |
|------|--------------|
| `project/tests/test_smoke.py` | Placeholder — `assert True` |

### Test fixtures

`project/tests/config/` contains copies of the config files used as test inputs:

| File | Mirrors |
|------|---------|
| `test_datacenter.json` | `config/datacenter.json` |
| `test_hostedzone.json` | `config/hostedzone.json` |

### Available test tooling (unused)

| Tool | Purpose |
|------|---------|
| `moto` | Mocks the AWS API so boto3 tests run without a real AWS account |
| `pytest-mock` | `mocker` fixture for patching |
| `pytest-cov` | Coverage reporting |
| `responses` | HTTP response mocking for non-boto3 calls |

### Running tests

```bash
source .venv/bin/activate
pytest -q
```

Or from `bin/test/`:

```bash
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=...
./bin/test/tests.sh
```

---

## Code Style

### Bash scripts

All four scripts in `bin/` share the same header pattern:

```bash
set -o errexit    # exit on any error
set -o pipefail   # exit on pipe failure
set -o nounset    # exit on unset variable
set +o xtrace     # no command echoing
```

`DATACENTER_DIR` is computed in every script independently using `$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)`.

### Python

- Line length: 79 characters (black), 200 characters (flake8 — effectively no limit)
- Formatter: black
- Type checking: not configured

### Ansible

- Playbooks use fully-qualified module names (`ansible.builtin.yum`, `ansible.builtin.template`)
- All variable values live in `provision.yml` — playbooks reference them by path, never hardcode versions or URLs
- Each playbook has a smoke-test task at the end that verifies the installed service responds correctly before the play exits

---

## Gaps / Improvement Areas

### 1. No meaningful tests

The only test is `assert True`. The `moto`, `pytest-mock`, and `pytest-cov` packages are already installed but unused. The boto3 source code in `project/src/` has no coverage.

**Recommended approach:** one test file per Python module, using `moto` to intercept all AWS API calls. The test fixtures in `project/tests/config/` are already in place.

### 2. No Bash tests

`bin/make.sh`, `bin/provision.sh`, and `bin/delete.sh` have no tests. The credential-validation block and `DATACENTER_DIR` computation in each script are untested.

**Recommended approach:** bats-core, with stubs for `python`, `ansible-playbook`, and the AWS CLI placed in a temporary `bin/` prepended to `PATH` — the same pattern used by FedoraBoxAutomation's 31 Bash test files.

### 3. Repeated code across `bin/` scripts

The AWS credential validation block and `DATACENTER_DIR` computation appear identically in `make.sh`, `provision.sh`, `delete.sh`, and `tests.sh`.

**Recommended approach:** extract a `bin/common.sh` sourced by all four scripts.

### 4. Secrets in plaintext

`provision/playbooks/variables/secrets.yml` stores service passwords in plaintext. It is not gitignored.

**Recommended approach:** encrypt with `ansible-vault` (`ansible-vault encrypt variables/secrets.yml`) and add the vault password to a `.env` file that is gitignored.

### 5. Hardcoded credentials in `group_vars/name_dtc_box`

`ansible_password` and `ansible_sudo_pass` are set to `"dtcadmin"` in a committed file.

**Recommended approach:** move to `secrets.yml` (then vault-encrypted) or to environment variables read via `lookup('env', ...)`.

### 6. `tests.sh` requires live AWS credentials

`bin/test/tests.sh` validates AWS environment variables before activating the venv or running pytest. Unit tests mocked with `moto` do not need real credentials — this gate should be removed so tests can run in CI without AWS access.
