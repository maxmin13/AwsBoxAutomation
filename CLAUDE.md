# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An Electron + React desktop GUI for provisioning an AWS VM "datacenter" (VPC, subnet, security group, EC2 instance, DNS record) and hardening a fresh AWS account's security posture (IAM user creation, root MFA, billing alerts, GuardDuty, etc.). All AWS calls go through the AWS SDK for JavaScript v3, invoked directly from the Electron main process — there is no AWS CLI dependency and no default credential provider chain; credentials are always passed explicitly.

**Test frameworks in use:** none yet. `vitest` is installed and `npm test` is wired up in `app/package.json`, but no test files exist under `app/electron/` or `app/src/`.

## Running the app

```bash
cd app
npm install
npm start        # runs `vite build` then launches Electron in production mode
```

There is no `npm run dev` / live-reload script — `start` always does a full Vite build first, then launches Electron pointed at `dist/`. `main.js` has a dead branch that loads `http://localhost:5173` when unpackaged and `NODE_ENV !== 'production'`, but no npm script currently exercises that path.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for full machine setup (Fedora, Node, Python, GitHub SSH).

## Architecture

See [docs/ELECTRON-GUI-DESIGN.md](docs/ELECTRON-GUI-DESIGN.md) for the full file-by-file breakdown. Summary:

- `app/electron/main.js` — window creation, single-instance lock, top-level error logging
- `app/electron/ipc-handlers.js` — every `ipcMain.handle()` registration, wrapped in `handleIpc()` which logs each call/reply to `gui.log` (credentials channels excluded — see `SILENT_CHANNELS`)
- `app/electron/preload.js` — `contextBridge` exposing `window.electronAPI` to the renderer; every new IPC channel needs an entry here **and** in `app/src/electron.d.ts`
- `app/electron/logger.js` — file logger, writes to `~/.config/AwsBoxAutomation/logs/{gui,app}.log`, rotates at 2 MB / 5 MB
- `app/src/AuthContext.tsx` — `requireCreds()` (blocks with a toast if no credentials at all) vs `withAuth()` (re-validates against STS, falls back to an inline `LoginPage` overlay) — two different gating strategies used depending on the page
- `app/src/pages/` — one component per nav tab (`AccountPage`, `DatacenterPage` = "My VMs", `CreateVmPage`, `LogsPage` = "Console", `DocsPage`)

**`vm/` is a separate, disconnected implementation.** It contains a Python/boto3 + Ansible pipeline (`vm/datacenter/`, `vm/provision/`) for the same conceptual task (create the datacenter, provision it), predating the Electron GUI. Nothing in `app/electron/` spawns or reads from `vm/` — confirmed no `child_process`/`spawn` calls anywhere in `app/electron/*.js`. Treat the two as independent unless/until they're wired together.

## Key Constraints

- Linux only (developed on Fedora); no Windows/macOS-specific code paths
- AWS credentials are always passed as explicit `{ accessKeyId, secretAccessKey }` — never rely on the SDK's default provider chain or `~/.aws/credentials`
- Credentials are stored at `~/.config/AwsBoxAutomation/credentials.json` in dev, `<userData>/.aws-data/credentials.json` when packaged; encrypted via `safeStorage` when an OS keychain is available, base64 fallback otherwise (`mode: 0o600` either way)
- **Credentials are only ever saved after a successful `validate-credentials` call** (STS `GetCallerIdentity`) — `LoginPage.tsx` validates before calling `saveCredentials`, never after
- Root-only operations (`delete-root-access-keys`, deleting root keys during IAM user creation) always re-verify via STS that the caller ARN ends in `:root` before deleting anything (`deleteAccessKeysIfRoot` in `ipc-handlers.js`) — never trust a UI flag alone for a destructive root action

## Critical Coding Rules

- **New `ipcMain.handle()` registrations require a full app restart** — `main.js` calls `registerIpcHandlers()` once at startup; the renderer's Vite dev server hot-reloads but the Electron main process does not.
- **`ELECTRON_RUN_AS_NODE` leaking from the shell breaks `electron .`** — VSCode's integrated terminal sets it, causing `require('electron')` to resolve to a path string instead of the module (`Cannot read properties of undefined (reading 'commandLine')`). The `start` script already unsets it (`env -u ELECTRON_RUN_AS_NODE electron .`); do the same if launching Electron manually.
- **Bare `tsc --noEmit` is not the real typecheck gate.** `app/src/pages/DocsPage.tsx` uses `?raw` Vite imports that plain `tsc` can't resolve, producing pre-existing errors unrelated to any change. Use `npm run build` (`vite build`) to verify.
- **`SILENT_CHANNELS` in `ipc-handlers.js` must be kept in sync** — any new IPC channel that carries credentials or secrets should be added there, or it will be logged in full to `gui.log`.
- **Don't add a new "create datacenter" AWS call without checking `CreateVmPage.tsx` first** — its Create VM button is currently a stub (`/* TODO: trigger VM creation */`); there is no `create-instance`/`create-datacenter` IPC handler yet. `describe-datacenter` / `start-instance` / `stop-instance` are the only instance-lifecycle handlers that exist.

## Known Gaps

- No tests (`app/electron/__tests__/`, `app/src/__tests__/` don't exist despite `vitest` being configured)
- `CreateVmPage` doesn't actually create anything yet
- `package.json`'s `build` block configures `electron-builder` (AppImage output) but `electron-builder` isn't in `devDependencies` — packaging is not currently runnable
- `vm/`'s Python/Ansible pipeline and `app/`'s Electron GUI solve overlapping problems independently; no shared source of truth for datacenter config (VPC CIDR, instance type, etc.) between the two
