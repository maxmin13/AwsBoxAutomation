# AWS Account Setup

## 1. Create a Free Tier Account

Go to [aws.amazon.com](https://aws.amazon.com) and click **Create a Free Account**.

You will need:

- An email address not already linked to another AWS account
- A phone number for SMS or voice verification
- A credit or debit card (a $1 hold is placed temporarily to verify it — no charge if you stay within the free tier)
- Your name and address

**Steps:**

1. Enter email + account name → verify email via code
2. Set a password
3. Enter contact info (personal or business)
4. Enter card details
5. Phone verification (automated call or SMS with a PIN)
6. Choose support plan → select **Basic (free)**

The account is active within minutes.

---

## 2. Generate Root Access Keys

The application needs credentials to connect to AWS for the first time. On a brand new account, root access keys are the only option.

Root has two independent authentication mechanisms: **access keys** (an Access Key ID + Secret Access Key pair, used for programmatic API calls) and **console login** (your root email + password, optionally + MFA). Deleting one has no effect on the other.

> Root access keys are temporary — the app deletes them automatically once an IAM user exists, since a long-lived root key is a much bigger risk if leaked than an IAM user's key. Deleting them only removes programmatic API access; you can still sign in to the AWS console as root with your email and password at any time.

1. Sign in to the AWS Console as root
2. Top-right menu → **Security credentials**
3. Scroll to **Access keys** → **Create access key**
4. Acknowledge the warning and confirm
5. Copy the **Access Key ID** and **Secret Access Key** — the secret is shown only once

---

## 3. Load Credentials into the App

Open the app and go to the **credentials screen**. Enter:

| Field             | Value              |
| ----------------- | ------------------ |
| Access Key ID     | from step 2        |
| Secret Access Key | from step 2        |
| Region            | e.g. `eu-west-1`   |

The app saves credentials locally in the system keychain.

---

## 4. Run Account Setup

Navigate to the **Account** page. The app detects that root credentials are active and launches the setup wizard automatically. All actions are idempotent — safe to run more than once.

### Step 1 — Root MFA (mandatory)

Sets up a virtual MFA device on the root account using a two-step wizard. MFA must be enabled before proceeding to step 2.

**Scan QR code:** clicking **Set Up Root MFA** calls `iam:CreateVirtualMFADevice`, which returns a QR code PNG and a base32 TOTP seed. Scan it with any TOTP app (Google Authenticator, Authy, 1Password, etc.). If your app requires manual entry, expand **Manual entry code**.

**Enter codes:** click **Next: Enter Codes** and enter two consecutive 6-digit codes from your authenticator app — the first from one 30-second window, the second from the next. Click **Activate MFA** to call `iam:EnableMFADevice`.

The MFA status badge (On / Off) reflects live state from `iam:GetAccountSummary` on page load, and turns green immediately after successful activation.

**Why:** without MFA, anyone who obtains your root password can sign in to the console and make irreversible changes. MFA is the single most impactful protection for a root account.

### Step 2 — Create IAM User (mandatory)

Creates a dedicated IAM user with the selected role and generates a long-term access key. The new key is immediately saved as your active credentials, so subsequent actions in this app use it instead of root.

| Field    | Description                                        |
| -------- | -------------------------------------------------- |
| Username | The IAM username, e.g. `admin`                     |
| Role     | The AWS managed policy to attach (see table below) |

**Available roles:**

| Role           | Policy                | Description                                      |
| -------------- | --------------------- | ------------------------------------------------ |
| Administrator  | `AdministratorAccess` | Full access to all AWS services and resources    |
| Power User     | `PowerUserAccess`     | Full access except IAM user and group management |
| Read Only      | `ReadOnlyAccess`      | Read-only access to all services                 |
| Security Audit | `SecurityAudit`       | Read security configuration across services      |
| Billing        | `Billing`             | Access to billing and cost management only       |

You can create multiple users — typing a new username clears the previous result so each user gets a clean form.

Leave **Delete root access keys after creating** checked (recommended) — the app deletes the root account's long-term access keys as part of the same operation, while root credentials are still active, so it cleanly transitions to IAM credentials in one step. The backend verifies the caller is root before attempting deletion, so the option is safe to leave checked even if root keys have already been removed.

> **Root access keys vs. root console access are separate.** Deleting root access keys only removes programmatic API access. You can still sign in to the AWS console at aws.amazon.com using your root email address and password at any time — that login method is never affected by this operation.

**Why:** root credentials should never be used for day-to-day API calls. A dedicated IAM user limits the blast radius of a leaked key.

> The secret access key is displayed once and then saved locally. Copy it as a backup before closing.

After this step the app operates entirely under IAM credentials.

### Step 3 — IAM User MFA (mandatory)

Sets up a virtual MFA device for the new IAM user, then mints its first temporary session — the same two-step wizard pattern as root MFA (step 1), plus a third sub-step to start the session.

**Scan QR code:** clicking **Set Up IAM User MFA** calls `iam:CreateVirtualMFADevice`, named after the IAM username so it doesn't collide with root's device. Scan it with any TOTP app.

**Enter codes:** enter two consecutive 6-digit codes to call `iam:EnableMFADevice` and activate the device.

**Start session:** enter one more fresh code to call `sts:GetSessionToken`, which exchanges the permanent access key + MFA code for temporary credentials valid for 4 hours. The app holds this session in memory only — it is never written to disk, and is lost on every restart.

**Why:** IAM user creation (step 2) attaches an inline policy alongside the chosen role that denies privileged actions unless `aws:MultiFactorAuthPresent` is true. This means the permanent access key saved to disk in step 2 is, by itself, no longer sufficient to do anything privileged — even if that key leaks (e.g. the credentials file is read off disk), an attacker still needs a live MFA code to call `sts:GetSessionToken` before they can do damage. A handful of self-service actions (managing your own MFA device, `GetSessionToken` itself, and read-only status checks like `GetCallerIdentity`, `GetAccountSummary`, and `DescribeInstances`) are exempted from this requirement — otherwise you could never bootstrap your first device or check "My VMs" without already having a session.

Once your first session is minted, subsequent privileged actions in the app — billing/anomaly/alarm setup, the security hardening cards, starting or stopping the VM — work without interruption for 4 hours. When the session expires, the app automatically prompts for a fresh MFA code the next time you attempt a privileged action, then retries it once you enter a valid code. Read-only actions (like the My VMs status view) never require MFA and keep working even with an expired or absent session.

> This only applies to IAM users created after this feature shipped. An IAM user created by an older version of the app keeps unconditional access under its permanent key unless you create a new IAM user or attach the policy manually via the IAM console.

### Step 4 — Alerts (optional)

All alerts require an email address. A phone number (E.164 format, e.g. `+353871234567`) is optional for SMS delivery. Click **Next Step** to skip and configure later.

**Billing alert** — creates a monthly AWS Budget and sends an email when 80% of the limit is reached.

| Field          | Description                                   |
| -------------- | ---------------------------------------------- |
| Limit (USD/mo) | Monthly spend threshold, e.g. `5`             |
| Alert email    | Address that receives the alert               |
| SMS phone      | Optional — E.164 number, e.g. `+353871234567` |

**Why:** a forgotten EC2 instance or Elastic IP can silently accumulate charges. An early-warning alert at 80% gives you time to act before the limit is hit.

**Cost anomaly detection** — enables AWS Cost Anomaly Detection and sends an immediate email when spending spikes unexpectedly, regardless of your monthly budget.

| Field           | Description                                            |
| --------------- | ------------------------------------------------------ |
| Threshold (USD) | Minimum anomalous spend to trigger an alert, e.g. `10` |
| Alert email     | Address that receives the alert                        |
| SMS phone       | Optional — E.164 number, e.g. `+353871234567`          |

**Why:** a billing alert fires at a percentage of a fixed budget. Anomaly detection fires on *unexpected patterns*, so it catches sudden spikes even if your total spend is low.

**Root login alarm** — creates an SNS topic and an EventBridge rule that fires on every root console sign-in.

| Field       | Description                                   |
| ----------- | ---------------------------------------------- |
| Alert email | Address that receives the notification        |
| SMS phone   | Optional — E.164 number, e.g. `+353871234567` |

1. Creates an SNS topic (`root-login-alarm`) in your region.
2. Subscribes your email address to the topic (confirmation email sent by AWS).
3. Optionally subscribes your phone number via SMS.
4. Creates an EventBridge rule matching `aws.signin` events where `userIdentity.type = Root`.

AWS routes console sign-in CloudTrail events to EventBridge by default — no explicit CloudTrail trail setup is required.

Example alert:

```text
AWS ALERT: Root account sign-in detected in eu-west-1 at 2026-06-13T10:42:00Z (account 123456789012)
```

> **Email confirmation:** after clicking Create Root Login Alarm, AWS sends a subscription confirmation email. You must click the link in that email before alerts are delivered.

### Step 5 — Security Hardening (optional)

One-click hardening steps. Each button calls the AWS API once and stays green — there is nothing to undo from this UI. Click **Complete Setup** when done.

**IAM password policy** — applies an account-wide password policy for IAM console users.

| Setting                   | Value                                  |
| -------------------------- | --------------------------------------- |
| Minimum length            | 12 characters                          |
| Complexity                | Uppercase, lowercase, numbers, symbols |
| Rotation                  | 90 days                                |
| Password reuse prevention | Last 5 passwords                       |

**S3 Block Public Access** — enables the account-level S3 Block Public Access setting. This overrides any bucket-level ACL or policy that would make a bucket publicly readable or writable.

**Why:** the most common cause of AWS data breaches is an accidentally public S3 bucket. This setting is a hard guardrail at the account level.

**GuardDuty** — enables Amazon GuardDuty threat detection for the account and region. GuardDuty continuously analyses:

- AWS CloudTrail management events (IAM changes, unusual API calls)
- VPC Flow Logs (unexpected network traffic)
- DNS logs (communication with known malicious domains)
- EC2 instance behaviour (crypto mining, port scanning)

Findings appear in the GuardDuty console and can be forwarded to notifications — see **GuardDuty SMS alert** below.

**IAM Access Analyzer** — creates an IAM Access Analyzer for the account. It continuously evaluates IAM policies, S3 bucket policies, KMS key policies, and other resource-based policies to flag any resource accessible from *outside* your AWS account. Findings appear in the IAM console under **Access Analyzer**.

**GuardDuty SMS alert** — configures an SMS text message alert for HIGH-severity GuardDuty findings (severity ≥ 7).

| Field        | Description                                              |
| ------------ | ---------------------------------------------------------- |
| Phone number | Your mobile number in E.164 format, e.g. `+353871234567` |

1. Creates an SNS topic (`guardduty-security-alerts`) in your region.
2. Subscribes your phone number to the topic via SMS.
3. Creates an EventBridge rule that matches GuardDuty findings with severity ≥ 7 and delivers a formatted text message to the topic.

Example message:

```text
AWS ALERT: GuardDuty - UnauthorizedAccess:EC2/SSHBruteForce (severity 7.8) in eu-west-1
```

**Prerequisites:** GuardDuty must be enabled (see above). Without an active detector, no findings are generated and no texts are sent.

> **SMS Sandbox:** new AWS accounts are placed in the SNS SMS sandbox by default. In sandbox mode, texts can only be sent to phone numbers you verify in the SNS console. To lift this restriction, request production access under **SNS → Text messaging (SMS) → Production access** in the AWS console.

---

## 5. Summary and Dashboard

After completing the wizard, the app displays a **setup summary** listing every item that was applied or skipped.

Click **Open Dashboard** to go to the Account detail page, which shows the live status of your account configuration. The detail page is shown on every subsequent visit to the Account tab.

To revisit any step, click **Re-run setup →** in the Account page header.

---

## Security Measures

A summary of every protection the wizard sets up, what it defends against, and where to configure it. All of it is optional after the two mandatory steps (root MFA, IAM user creation) — apply as much or as little as fits your use case.

| Measure | Defends against | Configured in | Cost |
| --- | --- | --- | --- |
| Root MFA | Root password alone being enough to sign in and make irreversible changes | Step 1 | Free |
| Root access key deletion | A long-lived root key sitting on disk indefinitely, unmonitored | Step 2 | Free |
| IAM user MFA-gated sessions | A leaked permanent IAM key being immediately usable for privileged actions | Step 3 | Free |
| Root login alarm | A root console sign-in going unnoticed | Step 4 | Free ([SNS pricing](https://aws.amazon.com/sns/pricing/), usage here is negligible) |
| Billing alert | A forgotten resource silently accumulating charges | Step 4 | Free — first 2 budgets/account, then [Budgets pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/) |
| Cost anomaly detection | A sudden spending spike going unnoticed until the monthly bill | Step 4 | Free ([pricing](https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/pricing/)) |
| IAM password policy | Weak or reused passwords for IAM console users | Step 5 | Free |
| S3 Block Public Access | A bucket becoming publicly readable/writable through a bucket-level ACL or policy | Step 5 | Free |
| GuardDuty | Unusual API calls, network traffic, DNS activity, or EC2 behaviour going undetected | Step 5 | **Paid after a 30-day trial** ([pricing](https://aws.amazon.com/guardduty/pricing/)) |
| IAM Access Analyzer | A resource-based policy unintentionally granting access from outside the account | Step 5 | Free |
| GuardDuty SMS alert | A HIGH-severity finding sitting unread in the console | Step 5 | Free itself, but requires GuardDuty running — paid once GuardDuty's trial ends |

Everything here is free except **GuardDuty** (and, by extension, the GuardDuty SMS alert, which depends on it) — that one starts billing after a 30-day trial, scaling with the volume of CloudTrail events, VPC Flow Logs, and DNS queries analyzed. Skip steps 5's GuardDuty card (and the SMS alert) if you want a fully free setup; every other measure still applies.

**The two layers that matter most, and why they're separate:**

- **Root MFA + key deletion (steps 1–2)** protect the account's single most powerful identity. Root is intentionally used only to bootstrap the IAM user, then stepped away from — the app never uses root credentials again once step 2 completes.
- **IAM user MFA-gated sessions (step 3)** protect the identity you actually use day to day. Without it, a leaked IAM access key (e.g. the credentials file copied off disk) would be permanently sufficient for whatever role you granted it — same risk profile root had before hardening. With it, the on-disk key is inert without a live MFA code: see step 3's **Why** for the exact IAM policy mechanism (`aws:MultiFactorAuthPresent`) and which actions stay exempt so you can still bootstrap and check status.

Everything else (steps 4–5) is detection and alerting, not access control — it doesn't stop an attacker, but it shortens how long a compromise or cost overrun goes unnoticed.

---

## Free Tier Limits

For current free tier allowances see: [aws.amazon.com/free](https://aws.amazon.com/free/)

> **Note:** Always destroy resources after testing to avoid charges. A running EC2 instance or an unattached Elastic IP will consume free tier hours or incur small charges even when idle.
