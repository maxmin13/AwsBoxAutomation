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

## 2. Secure the Root Account

Never use the root account for day-to-day work. Secure it immediately after signup.

**Enable MFA on root:**
- Console → top-right account menu → **Security credentials**
- MFA → **Assign MFA device**
- Choose **Authenticator app** (Google Authenticator, Authy, etc.)
- Scan the QR code and enter two consecutive codes to confirm

---

## 3. Create an IAM User

All API calls (including this application) must use an IAM user, not root credentials.

- Console → **IAM** → **Users** → **Create user**
- Attach the `AdministratorAccess` policy
- Under the **Security credentials** tab → **Create access key**
- Download the `.csv` file and keep it safe — the secret is shown only once

---

## 4. Set a Billing Alert

Prevents unexpected charges if you forget to delete resources.

- Console → **Billing** → **Budgets** → **Create budget**
- Choose **Zero spend budget** or set a $5 monthly threshold
- Enter your email address to receive alerts

---

## 5. Configure AWS Credentials Locally

Run this once after creating the IAM user:

```bash
aws configure
```

Enter the values from the downloaded `.csv`:

| Prompt | Value |
|---|---|
| AWS Access Key ID | from the .csv |
| AWS Secret Access Key | from the .csv |
| Default region name | e.g. `eu-west-1` |
| Default output format | `json` |

Credentials are stored in `~/.aws/credentials` and picked up automatically by this application.

---

## Free Tier Limits Relevant to This Project

| Service | Free allowance |
|---|---|
| EC2 `t2.micro` / `t3.micro` | 750 hrs/month for 12 months |
| S3 | 5 GB for 12 months |
| Route53 hosted zone | **Not free** — $0.50/month per zone |
| Data transfer out | 1 GB/month |

> **Note:** Always destroy resources after testing to avoid charges. A running EC2 instance or an unattached Elastic IP will consume free tier hours or incur small charges even when idle.
