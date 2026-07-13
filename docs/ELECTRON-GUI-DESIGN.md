# Electron GUI Design — AwsBoxAutomation

## Technology Stack

| Layer | Technology |
| --- | --- |
| Desktop shell + IPC | Electron |
| Main process | Node.js (via Electron) |
| Renderer | React + TypeScript |
| Bundler | Vite |
| Styling | Tailwind CSS |
| AWS access | AWS SDK for JavaScript v3, called directly from the main process |
| Credential encryption | Electron `safeStorage` (OS keychain — gnome-keyring, kwallet, macOS Keychain, Windows DPAPI), base64 fallback when no keychain service is running |
| Unit tests | none yet — `vitest` is installed and `npm test` is wired up, but no test files exist |

There is no script-runner / child-process layer: every AWS operation is an SDK call made in-process in `ipc-handlers.js`, not a spawned external script.

## Architecture

```text
app/
  electron/                      <- Node.js main process files
    main.js                      <- window creation, single-instance lock, top-level error/crash logging
    preload.js                   <- contextBridge: exposes window.electronAPI to the renderer
    ipc-handlers.js              <- every ipcMain.handle() registration; credential store; AWS SDK calls
    logger.js                    <- file logger; writes gui.log + app.log to ~/.config/AwsBoxAutomation/logs/
  src/                           <- React renderer files
    index.html
    index.tsx                    <- React entry point
    styles.css                   <- Tailwind imports
    electron.d.ts                <- TypeScript types for window.electronAPI (keep in sync with preload.js)
    App.tsx                      <- top-level nav state; renders one page per tab
    AuthContext.tsx              <- credential-gating context: requireCreds() / withAuth()
    ErrorBoundary.tsx            <- catches render errors, reports to log-error IPC channel
    components/
      NavBar.tsx                 <- tab bar: My Account, My VMs, Create VM, Activity, Docs
    pages/
      AccountPage.tsx            <- root hardening + IAM user creation + billing/anomaly alerts (775 lines, largest page)
      LoginPage.tsx               <- AWS credentials form; validates via STS before saving
      CredentialsPage.tsx        <- dead code — not imported anywhere; LoginPage.tsx is the active credentials form
      DatacenterPage.tsx         <- "My VMs" tab: describe/start/stop the dtc-box EC2 instance
      ProvisionPage.tsx          <- provisioning sub-view reached from DatacenterPage's detail view
      CreateVmPage.tsx           <- "Create VM" tab; shows config summary; Create button is a TODO stub
      LogsPage.tsx                <- "Activity" tab: tails gui.log, polls every 2.5s when Sync is on
      DocsPage.tsx                <- renders this repo's Markdown docs in-app via react-markdown
```

## IPC channel map

All channels are registered once in `registerIpcHandlers(win)`, called from `main.js` after the window is created. Adding a channel requires three edits kept in sync: `ipc-handlers.js` (the handler), `preload.js` (the `contextBridge` entry), `electron.d.ts` (the TS type).

| Group | Channels |
| --- | --- |
| Credentials | `load-credentials`, `save-credentials`, `validate-credentials`, `encryption-available` |
| Datacenter status | `describe-datacenter`, `start-instance`, `stop-instance` |
| Account setup | `create-iam-user`, `create-billing-alert`, `set-iam-password-policy`, `block-s3-public-access`, `enable-guardduty`, `enable-access-analyzer`, `create-anomaly-detection`, `enable-sms-security-alert` |
| Root security | `check-root-credentials`, `delete-root-access-keys`, `create-virtual-mfa-device`, `enable-mfa-device`, `create-root-login-alarm` |
| Log viewer | `read-log`, `open-log-dir`, `open-external` |
| Error logging | `log-error` |

`load-credentials` and `save-credentials` (plus `read-log`) are excluded from the `[ipc]` logging wrapper via `SILENT_CHANNELS`, so secrets never land in `gui.log`.

## Credential handling

- Store location: `~/.config/AwsBoxAutomation/credentials.json` in dev, `<userData>/.aws-data/credentials.json` when packaged.
- Encrypted at rest with `safeStorage.encryptString()` when `safeStorage.isEncryptionAvailable()`; otherwise base64-encoded with file mode `0o600`.
- **Save-on-success only**: `LoginPage.tsx` calls `validate-credentials` (STS `GetCallerIdentity`) with the candidate values *before* calling `save-credentials`. Bad credentials are never written to disk.
- Two independent gating mechanisms in `AuthContext.tsx`:
  - `requireCreds(action)` — cheap check against `hasCredentials` (whether any credentials are saved at all); shows a toast and refuses if none.
  - `withAuth(action)` — re-validates the saved credentials against STS on every call; on failure, shows an inline `LoginPage` overlay instead of the toast.
  - Pages choose which one (or both, chained) fits the action's cost/risk.

## State persistence

`App.tsx` keeps `DatacenterPage` ("My VMs") and `LogsPage` ("Activity") always mounted with `display: none` when their tab isn't active, so their internal state (loaded instance info, log tail position) survives navigation. `AccountPage`, `CreateVmPage`, and `DocsPage` are conditionally rendered and re-mount from scratch on every visit.

## Root vs. IAM credentials

Several handlers are root-only in practice (`delete-root-access-keys`, `create-virtual-mfa-device`, `enable-mfa-device`, `create-root-login-alarm`) because a fresh AWS account has no IAM user yet and these operations must run while root keys are still active — see [AWS_ACCOUNT_SETUP.md](AWS_ACCOUNT_SETUP.md). `deleteAccessKeysIfRoot()` in `ipc-handlers.js` re-verifies the caller's ARN via STS before deleting any access key, rather than trusting a UI-supplied flag, so a stale or wrong credential set can't accidentally nuke IAM user keys.

## Known gaps

- `CreateVmPage.tsx`'s Create button has no handler wired up yet (`/* TODO: trigger VM creation */`); there is no `create-instance` / `create-datacenter` IPC channel.
- No `app/electron/__tests__/` or `app/src/__tests__/` — despite `vitest` + `@testing-library/react` being installed.
- `package.json`'s `build` block configures `electron-builder` for AppImage output, but `electron-builder` isn't a `devDependency` — packaging isn't runnable as configured.
- `vm/`'s Python/boto3 + Ansible pipeline is a separate, disconnected implementation of the same "create a datacenter" goal; nothing in `app/electron/` spawns or reads from it.
