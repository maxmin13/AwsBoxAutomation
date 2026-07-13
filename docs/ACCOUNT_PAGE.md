# Account Page

The Account page groups one-time setup tasks and security hardening steps for a new AWS account. All actions are idempotent — safe to run more than once.

---

## Root Account Security

These three steps must be completed **while root credentials are still active** — before you create an IAM user and switch credentials. The status badges on the first two cards refresh automatically on page load.

---

---

### Root MFA

Sets up a virtual MFA device on the root account using a two-step wizard.

**Step 1 — Scan QR code:**

Clicking **Set Up Root MFA** calls `iam:CreateVirtualMFADevice`, which returns a QR code PNG and a base32 TOTP seed. Scan the QR code with any TOTP app (Google Authenticator, Authy, 1Password, etc.). If your app requires manual entry, expand **Manual entry code**.

**Step 2 — Enter codes:**

Click **Next: Enter Codes** and enter two consecutive 6-digit codes from your authenticator app. The first code comes from one 30-second window; the second from the next window. Click **Activate MFA** to call `iam:EnableMFADevice`.

The MFA status badge (On / Off) reflects live state from `iam:GetAccountSummary` on page load, and turns green immediately after successful activation.

**Why:** Without MFA, anyone who obtains your root password can sign in to the console and make irreversible changes. MFA is the single most impactful protection for a root account.

---

### Root Login Alarm

Creates an SNS topic and an EventBridge rule that fires on every root console sign-in.

| Field       | Description                                       |
| ----------- | ------------------------------------------------- |
| Alert email | Address that receives the notification            |
| SMS phone   | Optional — E.164 number, e.g. `+353871234567`     |

**How it works:**

1. Creates an SNS topic (`root-login-alarm`) in your region.
2. Subscribes your email address to the topic (confirmation email sent by AWS).
3. Optionally subscribes your phone number via SMS.
4. Creates an EventBridge rule matching `aws.signin` events where `userIdentity.type = Root`.

AWS routes console sign-in CloudTrail events to EventBridge by default — no explicit CloudTrail trail setup is required.

Example alert:

```text
AWS ALERT: Root account sign-in detected in eu-west-1 at 2026-06-13T10:42:00Z (account 123456789012)
```

> **Email confirmation:** After clicking Create Root Login Alarm, AWS sends a subscription confirmation email. You must click the link in that email before alerts are delivered.

---

## Account Setup

### Create IAM User

Creates an IAM user with the selected role and generates a long-term access key. The new key is immediately saved as your active credentials so subsequent actions in this app use it instead of root.

A **Delete root access keys after creating** checkbox (enabled by default) deletes the root account's long-term access keys as part of the same operation — while root credentials are still active — so the app cleanly transitions to IAM credentials in one step. The backend verifies the caller is root before attempting deletion, so the option is safe to leave checked even if root keys have already been removed.

> **Root access keys vs. root console access are separate.** Deleting root access keys only removes programmatic API access. You can still sign in to the AWS console at aws.amazon.com using your root email address and password at any time — that login method is never affected by this operation.

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

**Why:** Root credentials should never be used for day-to-day API calls. A dedicated IAM user limits the blast radius of a leaked key.

> The secret access key is displayed once and then saved locally. Copy it as a backup before closing.

---

### Set Billing Alert

Creates a monthly AWS Budget and sends an email when **80 %** of the limit is reached.

| Field          | Description                                        |
| -------------- | -------------------------------------------------- |
| Limit (USD/mo) | Monthly spend threshold, e.g. `5`                  |
| Alert email    | Address that receives the alert                    |
| SMS phone      | Optional — E.164 number, e.g. `+353871234567`      |

If a phone number is provided, an SNS topic (`billing-sms-alerts`) is created in `us-east-1`, the number is subscribed via SMS, and the topic is added as a second subscriber alongside the email.

**Why:** A forgotten EC2 instance or Elastic IP can silently accumulate charges. An early-warning alert at 80 % gives you time to act before the limit is hit.

---

### Cost Anomaly Detection

Enables AWS Cost Anomaly Detection and sends an immediate email when spending spikes unexpectedly — regardless of your monthly budget.

| Field           | Description                                            |
| --------------- | ------------------------------------------------------ |
| Threshold (USD) | Minimum anomalous spend to trigger an alert, e.g. `10` |
| Alert email     | Address that receives the alert                        |
| SMS phone       | Optional — E.164 number, e.g. `+353871234567`          |

If a phone number is provided, an SNS topic (`anomaly-sms-alerts`) is created in `us-east-1`, the number is subscribed via SMS, and the topic is added as a second subscriber alongside the email.

**Why:** A billing alert fires at a percentage of a fixed budget. Anomaly detection fires on *unexpected patterns*, so it catches sudden spikes even if your total spend is low.

---

## Security

One-click hardening steps. Each button calls the AWS API once and stays green — there is nothing to undo from this UI.

---

### IAM Password Policy

Applies an account-wide password policy for IAM console users.

| Setting                   | Value                                  |
| ------------------------- | -------------------------------------- |
| Minimum length            | 12 characters                          |
| Complexity                | Uppercase, lowercase, numbers, symbols |
| Rotation                  | 90 days                                |
| Password reuse prevention | Last 5 passwords                       |

---

### S3 Block Public Access

Enables the account-level S3 Block Public Access setting. This overrides any bucket-level ACL or policy that would make a bucket publicly readable or writable.

**Why:** The most common cause of AWS data breaches is an accidentally public S3 bucket. This setting is a hard guardrail at the account level.

---

### GuardDuty

Enables Amazon GuardDuty threat detection for the account and region.

GuardDuty continuously analyses:

- AWS CloudTrail management events (IAM changes, unusual API calls)
- VPC Flow Logs (unexpected network traffic)
- DNS logs (communication with known malicious domains)
- EC2 instance behaviour (crypto mining, port scanning)

Findings appear in the GuardDuty console and can be forwarded to notifications — see **GuardDuty SMS Alert** below.

---

### IAM Access Analyzer

Creates an IAM Access Analyzer for the account. It continuously evaluates IAM policies, S3 bucket policies, KMS key policies, and other resource-based policies to flag any resource accessible from *outside* your AWS account.

Findings appear in the IAM console under **Access Analyzer**.

---

### GuardDuty SMS Alert

Configures an SMS text message alert for **HIGH-severity** GuardDuty findings (severity ≥ 7).

| Field        | Description                                              |
| ------------ | -------------------------------------------------------- |
| Phone number | Your mobile number in E.164 format, e.g. `+353871234567` |

**How it works:**

1. Creates an SNS topic (`guardduty-security-alerts`) in your region.
2. Subscribes your phone number to the topic via SMS.
3. Creates an EventBridge rule that matches GuardDuty findings with severity ≥ 7 and delivers a formatted text message to the topic.

Example message:

```text
AWS ALERT: GuardDuty - UnauthorizedAccess:EC2/SSHBruteForce (severity 7.8) in eu-west-1
```

**Prerequisites:** GuardDuty must be enabled (see above). Without an active detector, no findings are generated and no texts are sent.

> **SMS Sandbox:** New AWS accounts are placed in the SNS SMS sandbox by default. In sandbox mode, texts can only be sent to phone numbers you verify in the SNS console. To lift this restriction, request production access under **SNS → Text messaging (SMS) → Production access** in the AWS console.
