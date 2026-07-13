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

Navigate to the **Account** page. The app detects that root credentials are active and launches the setup wizard automatically.

### Step 1 — Root MFA (mandatory)

Protects the root account from console sign-in without a physical device.

1. Click **Set Up Root MFA** — the app generates a virtual MFA device via `iam:CreateVirtualMFADevice` and displays a QR code
2. Scan the QR code in any TOTP app (Google Authenticator, Authy, 1Password, etc.)
3. Click **Next: Enter Codes** and enter two consecutive 6-digit codes
4. Click **Activate MFA**

MFA must be enabled before proceeding to step 2.

### Step 2 — Create IAM User (mandatory)

Creates a dedicated administrator user for day-to-day API access. The root account should not be used for routine work.

1. Enter a username (e.g. `admin`)
2. Leave **Delete root access keys after creating** checked (recommended) — the app deletes root keys atomically before switching credentials, while root access is still active
3. Click **Create IAM User**

The app attaches the `AdministratorAccess` policy, generates an access key, and immediately saves the new IAM credentials. Copy the secret key as a backup — it is shown only once.

After this step the app operates entirely under IAM credentials.

### Step 3 — Alerts (optional)

| Alert                  | What it does                                              |
| ---------------------- | --------------------------------------------------------- |
| Billing alert          | Monthly budget — email at 80% of your threshold           |
| Cost anomaly detection | Immediate alert on unexpected spending spikes             |
| Root login alarm       | Email on every root console sign-in via EventBridge + SNS |

All alerts require an email address. A phone number (E.164 format, e.g. `+353871234567`) is optional for SMS delivery.

Click **Next Step** to skip and configure later.

### Step 4 — Security Hardening (optional)

| Action                 | What it does                                                        |
| ---------------------- | ------------------------------------------------------------------- |
| IAM password policy    | Enforces min 12 chars, uppercase, numbers, symbols, 90-day rotation |
| S3 block public access | Account-wide guard against accidentally public buckets              |
| GuardDuty              | Continuous threat detection — API calls, network, DNS, EC2 behaviour|
| IAM Access Analyzer    | Flags resources accessible from outside your account                |
| GuardDuty SMS alert    | Text on HIGH-severity findings (requires GuardDuty enabled)         |

Click **Complete Setup** when done.

---

## 5. Summary and Dashboard

After completing the wizard, the app displays a **setup summary** listing every item that was applied or skipped.

Click **Open Dashboard** to go to the Account detail page, which shows the live status of your account configuration. The detail page is shown on every subsequent visit to the Account tab.

To revisit any step, click **Re-run setup →** in the Account page header.

---

## Free Tier Limits

For current free tier allowances see: [aws.amazon.com/free](https://aws.amazon.com/free/)

> **Note:** Always destroy resources after testing to avoid charges. A running EC2 instance or an unattached Elastic IP will consume free tier hours or incur small charges even when idle.
