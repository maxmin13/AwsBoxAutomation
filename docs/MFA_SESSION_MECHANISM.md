# MFA & Session Mechanism

How this app protects root and the IAM admin user with MFA, and how the IAM
user's permanent access key is neutered without a live session. This is a
deep-dive on the mechanism — see [AWS_ACCOUNT_SETUP.md](AWS_ACCOUNT_SETUP.md)
for the setup wizard walkthrough.

## The two layers

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph Root["Root account"]
        R1[Virtual MFA device] --- R2[Protects console + root login alarm]
    end
    subgraph IAM["IAM admin user"]
        I1[Virtual MFA device] --- I2[Gates every privileged API call]
    end
    R2 -. independent of .- I2
```

Root MFA and IAM user MFA both start the same way (device creation + QR
code) but **diverge at activation**, and do different jobs besides. Root MFA
just protects the root login itself. IAM user MFA is paired with an
enforcement policy that makes the day-to-day permanent access key powerless
on its own — that's the part this document focuses on.

## 📱 Enrolling a virtual MFA device

`mfaCard` (root) and `iamMfaCard` (IAM user) in `AccountPage.tsx` share the
device-creation step, then split: `iam:EnableMFADevice` requires a real IAM
`UserName`, which root doesn't have — no API can activate root's own device
(confirmed against the SDK's model and live testing; `sts:AssumeRoot`'s
fixed task-policy list doesn't cover MFA either), so root activation only
exists in the AWS Console:

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant You
    participant Phone as 📱 Authenticator app
    participant App
    participant AWS as AWS IAM
    participant Console as AWS Console

    You->>App: Click "Set Up MFA"
    App->>AWS: CreateVirtualMFADevice
    AWS-->>App: QR code + secret
    App-->>You: Show QR code
    You->>Phone: Scan QR code
    Phone-->>You: Displays 6-digit code (rotates every 30s)
    alt IAM user
        You->>App: Enter two consecutive 6-digit codes
        App->>AWS: EnableMFADevice(UserName, code1, code2)
        AWS-->>App: MFA active
    else Root
        Note over App,AWS: No API can activate root's own device
        You->>Console: Open Console, create + activate a<br/>separate device there instead
        Console-->>You: MFA active (account-wide)
        You->>App: Click "Check Status"
        App->>AWS: GetAccountSummary
        AWS-->>App: AccountMFAEnabled = true
    end
```

The Console flow creates its own virtual MFA device, independent from the
one the app created — you end up with an extra, unassigned device (and a
matching unused authenticator app entry) that's harmless but can be deleted
later if you want to tidy up. `Check Status` reads `AccountMFAEnabled`,
which is account-wide, not tied to which specific device activated it.

## The enforcement policy — why a leaked key isn't enough

`create-iam-user` attaches an inline policy
([mfa-enforcement-policy.js](../app/electron/mfa-enforcement-policy.js))
alongside `AdministratorAccess`. IAM always lets an explicit `Deny` win over
any `Allow`, so this single policy turns "admin" into "admin, only with a
live MFA session":

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TD
    A[API request arrives] --> B{Is it on the<br/>self-service allow-list?}
    B -- "yes<br/>(check MFA status, manage own<br/>MFA device, GetSessionToken, GetCallerIdentity,<br/>DescribeInstances)" --> C[Allowed — no MFA needed]
    B -- no --> D{aws:MultiFactorAuthPresent<br/>= true?}
    D -- yes --> E[Allowed by AdministratorAccess]
    D -- "no / missing" --> F[Denied]
```

The subtle bit: `aws:MultiFactorAuthPresent` only exists as a request
attribute on **STS temporary credentials**. A request signed with the plain
permanent access key carries no such attribute at all — it isn't `false`,
it's *absent*. The policy uses `BoolIfExists` (not `Bool`) specifically so
"absent" is treated as "false," otherwise a permanent-key request would slip
past the Deny entirely.

**Net effect:** the permanent access key saved to disk in step 2 of setup
can, by itself, only check its own status and start a session — nothing
else — until a live MFA code is supplied.

## Minting a session

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant You
    participant App as Renderer (AuthContext)
    participant Main as Main process
    participant AWS as AWS STS

    You->>App: Trigger a privileged action (e.g. Stop instance)
    App->>Main: getSessionStatus()
    Main-->>App: { active: false }
    App-->>You: Show MFA prompt modal
    You->>App: Enter fresh 6-digit code
    App->>Main: getSessionToken(code)
    Main->>AWS: GetSessionToken(SerialNumber, TokenCode, 14400s)
    AWS-->>Main: temp accessKeyId + secret + sessionToken
    Main->>Main: session-store.setSession(...)
    Main-->>App: { ok: true }
    App->>App: run the original action
```

The session lives in `session-store.js`, **in memory only** — never written
to `credentials.json`. A 4-hour token gains nothing from disk persistence,
and persisting it would just be a second thing to leak. Restarting the app
loses the session; the next privileged action re-prompts for a fresh code.

## Which credentials actually get used

Every privileged IPC handler resolves credentials the same way before
calling an AWS SDK client:

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TD
    A[Handler needs credentials] --> B{Live session in<br/>session-store?}
    B -- "yes, and matches<br/>the on-disk access key" --> C[Use session credentials<br/>accessKeyId + secret + sessionToken]
    B -- "no / expired / for a<br/>different account" --> D[Use the permanent<br/>accessKeyId + secret from disk]
    C --> E[Request carries<br/>MultiFactorAuthPresent = true]
    D --> F[Enforcement policy denies<br/>anything but self-service actions]
```

This is `getActiveCredentials()` in `session-store.js` — it falls back to
the permanent key automatically if there's no session, the session expired,
or credentials.json now points at a different account than the session was
minted for.

## Session lifecycle over time

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    A["t = 0<br/>MFA code entered<br/>Session minted"] --> B["t = 0 to 4h<br/>Session active<br/>Privileged calls allowed"]
    B --> C["t = 4h<br/>Session expires<br/>Falls back to permanent key"]
    C --> D["Next privileged action<br/>MFA prompt shown again"]
    D --> A
```

At the 4-hour mark the session silently expires. Nothing breaks — the next
privileged action just re-triggers the MFA prompt shown above, and read-only
actions (like the My VMs status view) keep working the whole time regardless
of session state, since they're on the enforcement policy's allow-list.

## What this defends against

| Threat | Outcome |
| --- | --- |
| `credentials.json` read off disk | Attacker gets a permanent key that can only check status / start a session — no live MFA code, no damage. |
| App left running, no active session | Next privileged action re-prompts for MFA before doing anything. |
| Stale session after switching AWS accounts | `getActiveCredentials()` detects the access-key mismatch and falls back to the (harmless-without-MFA) permanent key. |

## What this doesn't do

The permanent key still exists on disk — STS `GetSessionToken` requires
*something* to authenticate the bootstrap call with, so it can't be
eliminated outright without a different architecture (federated login via
AWS IAM Identity Center, which issues no long-lived key at all). That's a
larger change than this mechanism and isn't implemented here.

## Glossary

| Acronym | Stands for | Meaning here |
| --- | --- | --- |
| AWS | Amazon Web Services | The cloud provider this whole app automates. |
| MFA | Multi-Factor Authentication | A second proof of identity beyond a password/access key — a 6-digit code from an authenticator app (TOTP) in this app's case. |
| TOTP | Time-based One-Time Password | The specific MFA code format used here — a 6-digit code that rotates every 30 seconds, generated by an authenticator app from a shared secret. |
| IAM | Identity and Access Management | AWS's system for users, roles, and permission policies. "Root" and the "IAM admin user" are both IAM concepts, though root itself sits outside IAM. |
| STS | Security Token Service | The AWS service that issues the temporary credentials (access key + secret + session token) minted by `GetSessionToken`. |
| IPC | Inter-Process Communication | How this Electron app's renderer (UI, e.g. `AccountPage.tsx`) talks to its main process (`ipc-handlers.js`, where AWS SDK calls actually happen). |
| QR (code) | Quick Response code | The scannable barcode shown during MFA enrollment — it encodes the shared secret so your authenticator app can start generating matching TOTP codes. |
