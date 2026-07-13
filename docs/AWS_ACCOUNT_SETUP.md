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

> Root access keys are temporary — the app deletes them automatically after creating an IAM user. Deleting them only removes programmatic API access; you can still sign in to the AWS console as root with your email and password at any time.

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

### Step 3 — Alerts (optional)

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

### Step 4 — Security Hardening (optional)

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

## Free Tier Limits

For current free tier allowances see: [aws.amazon.com/free](https://aws.amazon.com/free/)

> **Note:** Always destroy resources after testing to avoid charges. A running EC2 instance or an unattached Elastic IP will consume free tier hours or incur small charges even when idle.
