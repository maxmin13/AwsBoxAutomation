// ============================================================
//  ipc-handlers.js — registers all ipcMain.handle() calls
// ============================================================

const { ipcMain, app, shell, safeStorage } = require('electron')
const { inspect } = require('util')
const path = require('path')
const fs   = require('fs')
const os   = require('os')
const log = require('./logger')
const sessionStore = require('./session-store')
const { mfaEnforcementPolicy } = require('./mfa-enforcement-policy')

// Credentials store — in userData so it survives reinstalls
const CREDS_DIR  = app?.isPackaged
  ? path.join(app.getPath('userData'), '.aws-data')
  : path.join(os.homedir(), '.config', 'AwsBoxAutomation')
const CREDS_FILE = path.join(CREDS_DIR, 'credentials.json')

async function readCredsStore() {
  try {
    const raw = await fs.promises.readFile(CREDS_FILE)  // Buffer
    if (safeStorage.isEncryptionAvailable()) {
      return JSON.parse(safeStorage.decryptString(raw))
    }
    // fallback: legacy base64 plaintext
    return JSON.parse(Buffer.from(raw.toString().trim(), 'base64').toString('utf8'))
  } catch {
    return {}
  }
}

async function writeCredsStore(data) {
  await fs.promises.mkdir(CREDS_DIR, { recursive: true })
  const json = JSON.stringify(data, null, 2)
  const content = safeStorage.isEncryptionAvailable()
    ? safeStorage.encryptString(json)           // encrypted Buffer (OS keychain)
    : Buffer.from(json, 'utf8').toString('base64') // fallback: base64 (no keychain)
  await fs.promises.writeFile(CREDS_FILE, content, { mode: 0o600 })
}

// Channels excluded from IPC logging — keep credentials out of gui.log
const SILENT_CHANNELS = new Set(['read-log', 'load-credentials', 'save-credentials', 'get-session-token'])

function truncate(str, max = 120) {
  return str.length <= max ? str : str.slice(0, max) + ` …[+${str.length - max} chars]`
}

function handleIpc(channel, handler) {
  ipcMain.handle(channel, async (event, ...args) => {
    if (!SILENT_CHANNELS.has(channel)) {
      log.info(`[ipc] recv ${channel}`, args.length ? truncate(inspect(args, { depth: 3, breakLength: Infinity })) : '')
    }
    const result = await handler(event, ...args)
    if (!SILENT_CHANNELS.has(channel)) {
      log.info(`[ipc] reply ${channel}`, truncate(inspect(result, { depth: 3, breakLength: Infinity })))
    }
    return result
  })
}

// ── Shared alert-topic helpers ───────────────────────────────────────────────
// The billing, anomaly, GuardDuty SMS, and root-login-alarm handlers all create
// an SNS topic with the same publish-policy/subscribe shape, and the two
// EventBridge-based ones (GuardDuty SMS, root login alarm) put an identically
// shaped rule + target. Factored out here so the four handlers stay one-liners.

async function createAlertTopic(snsClient, { name, principal, email, phone }) {
  const { CreateTopicCommand, SetTopicAttributesCommand, SubscribeCommand } = require('@aws-sdk/client-sns')
  const { TopicArn } = await snsClient.send(new CreateTopicCommand({ Name: name }))
  await snsClient.send(new SetTopicAttributesCommand({
    TopicArn,
    AttributeName:  'Policy',
    AttributeValue: JSON.stringify({
      Version: '2012-10-17',
      Statement: [{ Effect: 'Allow', Principal: { Service: principal }, Action: 'SNS:Publish', Resource: TopicArn }],
    }),
  }))
  if (email) await snsClient.send(new SubscribeCommand({ TopicArn, Protocol: 'email', Endpoint: email }))
  if (phone) await snsClient.send(new SubscribeCommand({ TopicArn, Protocol: 'sms', Endpoint: phone }))
  return TopicArn
}

async function putAlertRule(ebClient, { name, description, eventPattern, targetArn, inputPathsMap, inputTemplate }) {
  const { PutRuleCommand, PutTargetsCommand } = require('@aws-sdk/client-eventbridge')
  await ebClient.send(new PutRuleCommand({
    Name: name, Description: description, State: 'ENABLED', EventPattern: JSON.stringify(eventPattern),
  }))
  await ebClient.send(new PutTargetsCommand({
    Rule:    name,
    Targets: [{ Id: `${name}-target`, Arn: targetArn, InputTransformer: { InputPathsMap: inputPathsMap, InputTemplate: inputTemplate } }],
  }))
}

// Deletes all access keys belonging to `creds`, but only after confirming via
// STS that those credentials actually belong to the root user. Shared by
// create-iam-user's "delete root keys" option and the standalone
// delete-root-access-keys handler so the safety check can't drift between them.
async function deleteAccessKeysIfRoot(client, creds) {
  const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
  const { ListAccessKeysCommand, DeleteAccessKeyCommand } = require('@aws-sdk/client-iam')

  const identity = await new STSClient({ region: 'us-east-1', credentials: creds })
    .send(new GetCallerIdentityCommand({}))
  if (!identity.Arn?.endsWith(':root')) return false

  const { AccessKeyMetadata = [] } = await client.send(new ListAccessKeysCommand({}))
  for (const key of AccessKeyMetadata) {
    await client.send(new DeleteAccessKeyCommand({ AccessKeyId: key.AccessKeyId }))
  }
  return true
}

/**
 * Registers all IPC handlers. Called once from main.js after the window is created.
 * @param {Electron.BrowserWindow} win
 */
function registerIpcHandlers(win) {

  // ── Credentials ───────────────────────────────────────────────────────────

  handleIpc('load-credentials', async () => {
    const store = await readCredsStore()
    return {
      ok: true,
      accessKeyId:     store.accessKeyId     ?? '',
      secretAccessKey: store.secretAccessKey ?? '',
      region:          store.region          ?? 'eu-west-1',
    }
  })

  handleIpc('save-credentials', async (_event, { accessKeyId, secretAccessKey, region }) => {
    await writeCredsStore({ accessKeyId, secretAccessKey, region })
    return { ok: true }
  })

  handleIpc('encryption-available', async () => {
    return { ok: safeStorage.isEncryptionAvailable() }
  })

  // Validates either explicitly-passed credentials (used before they are ever
  // saved to disk — see LoginPage) or, if none are passed, whatever is
  // currently in the store (used by AuthContext to re-check saved credentials).
  handleIpc('validate-credentials', async (_event, candidate) => {
    const { accessKeyId, secretAccessKey, region } = candidate ?? await readCredsStore()
    if (!accessKeyId || !secretAccessKey) {
      return { ok: false, error: 'No credentials configured' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const client = new STSClient({
        region: region || 'us-east-1',
        credentials: { accessKeyId, secretAccessKey },
      })
      await client.send(new GetCallerIdentityCommand({}))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][validate-credentials]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Datacenter status ─────────────────────────────────────────────────────
  // Queries AWS for the dtc-box EC2 instance state. Returns found=false when no
  // non-terminated instance with tag Name=dtc-box exists.

  handleIpc('describe-datacenter', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured' }
    }

    try {
      const { EC2Client, DescribeInstancesCommand } = require('@aws-sdk/client-ec2')
      const client = new EC2Client({
        region: store.region || 'eu-west-1',
        credentials: {
          accessKeyId:     store.accessKeyId,
          secretAccessKey: store.secretAccessKey,
        },
      })

      const response = await client.send(new DescribeInstancesCommand({
        Filters: [{ Name: 'tag:Name', Values: ['dtc-box'] }],
      }))

      const instances = (response.Reservations ?? [])
        .flatMap(r => r.Instances ?? [])
        .filter(i => i.State?.Name !== 'terminated')

      if (instances.length === 0) {
        return { ok: true, found: false }
      }

      const inst = instances[0]
      return {
        ok:           true,
        found:        true,
        state:        inst.State?.Name        ?? 'unknown',
        instanceId:   inst.InstanceId         ?? '',
        instanceType: inst.InstanceType       ?? '',
        publicIp:     inst.PublicIpAddress    ?? null,
        publicDns:    inst.PublicDnsName      ?? null,
        launchTime:   inst.LaunchTime?.toISOString() ?? null,
      }
    } catch (error) {
      log.error('[ipc][describe-datacenter]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Instance control ─────────────────────────────────────────────────────

  handleIpc('start-instance', async (_event, instanceId) => {
    const store = await readCredsStore()
    try {
      const { EC2Client, StartInstancesCommand } = require('@aws-sdk/client-ec2')
      const client = new EC2Client({
        region: store.region || 'eu-west-1',
        credentials: sessionStore.getActiveCredentials(store),
      })
      await client.send(new StartInstancesCommand({ InstanceIds: [instanceId] }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][start-instance]', error.message)
      return { ok: false, error: error.message }
    }
  })

  handleIpc('stop-instance', async (_event, instanceId) => {
    const store = await readCredsStore()
    try {
      const { EC2Client, StopInstancesCommand } = require('@aws-sdk/client-ec2')
      const client = new EC2Client({
        region: store.region || 'eu-west-1',
        credentials: sessionStore.getActiveCredentials(store),
      })
      await client.send(new StopInstancesCommand({ InstanceIds: [instanceId] }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][stop-instance]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── IAM user creation ────────────────────────────────────────────────────
  // Creates an IAM user, attaches the chosen policy, and returns a new access key.
  // If deleteRootKeys is true, root access keys are deleted before returning — this
  // is safe here because the credential store still holds root credentials at call time.
  // A safety check ensures we only delete keys when the caller is actually root.

  handleIpc('create-iam-user', async (_event, { username, policyArn, deleteRootKeys }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const {
        IAMClient,
        CreateUserCommand,
        AttachUserPolicyCommand,
        PutUserPolicyCommand,
        CreateAccessKeyCommand,
      } = require('@aws-sdk/client-iam')

      const creds  = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
      const client = new IAMClient({ region: 'us-east-1', credentials: creds })

      await client.send(new CreateUserCommand({ UserName: username }))
      await client.send(new AttachUserPolicyCommand({ UserName: username, PolicyArn: policyArn }))
      await client.send(new PutUserPolicyCommand({
        UserName:       username,
        PolicyName:     'enforce-mfa-for-privileged-actions',
        PolicyDocument: JSON.stringify(mfaEnforcementPolicy),
      }))

      const keyResponse = await client.send(new CreateAccessKeyCommand({ UserName: username }))
      const key = keyResponse.AccessKey

      let rootKeysDeleted = false
      if (deleteRootKeys) {
        rootKeysDeleted = await deleteAccessKeysIfRoot(client, creds)
      }

      return { ok: true, accessKeyId: key.AccessKeyId, secretAccessKey: key.SecretAccessKey, rootKeysDeleted }
    } catch (error) {
      log.error('[ipc][create-iam-user]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Billing alert ─────────────────────────────────────────────────────────
  // Creates a monthly AWS Budget and sends an email alert when 80% is reached.

  handleIpc('create-billing-alert', async (_event, { amount, email, phone }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const {
        BudgetsClient,
        CreateBudgetCommand,
        UpdateBudgetCommand,
        CreateSubscriberCommand,
      } = require('@aws-sdk/client-budgets')

      const creds = sessionStore.getActiveCredentials(store)

      const identity = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetCallerIdentityCommand({}))

      const subscribers = [{ SubscriptionType: 'EMAIL', Address: email }]

      if (phone) {
        const { SNSClient } = require('@aws-sdk/client-sns')
        const snsClient = new SNSClient({ region: 'us-east-1', credentials: creds })
        const TopicArn = await createAlertTopic(snsClient, { name: 'billing-sms-alerts', principal: 'budgets.amazonaws.com', phone })
        subscribers.push({ SubscriptionType: 'SNS', Address: TopicArn })
      }

      const budgetsClient = new BudgetsClient({ region: 'us-east-1', credentials: creds })
      const budgetName = 'monthly-limit'
      const notification = {
        NotificationType:   'ACTUAL',
        ComparisonOperator: 'GREATER_THAN',
        Threshold:          80,
        ThresholdType:      'PERCENTAGE',
      }
      const newBudget = {
        BudgetName:  budgetName,
        BudgetLimit: { Amount: String(amount), Unit: 'USD' },
        TimeUnit:    'MONTHLY',
        BudgetType:  'COST',
      }

      try {
        await budgetsClient.send(new CreateBudgetCommand({
          AccountId: identity.Account,
          Budget: newBudget,
          NotificationsWithSubscribers: [{ Notification: notification, Subscribers: subscribers }],
        }))
      } catch (error) {
        if (error.name !== 'DuplicateRecordException') throw error
        // A budget from a previous run already exists under this fixed name —
        // update its limit in place instead of creating a second budget, then
        // (re-)attach subscribers (ignoring "already subscribed").
        await budgetsClient.send(new UpdateBudgetCommand({ AccountId: identity.Account, NewBudget: newBudget }))
        for (const subscriber of subscribers) {
          try {
            await budgetsClient.send(new CreateSubscriberCommand({
              AccountId:    identity.Account,
              BudgetName:   budgetName,
              Notification: notification,
              Subscriber:   subscriber,
            }))
          } catch (subError) {
            if (subError.name !== 'DuplicateRecordException') throw subError
          }
        }
      }

      return { ok: true }
    } catch (error) {
      log.error('[ipc][create-billing-alert]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── IAM password policy ───────────────────────────────────────────────────

  handleIpc('set-iam-password-policy', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { IAMClient, UpdateAccountPasswordPolicyCommand } = require('@aws-sdk/client-iam')
      await new IAMClient({
        region: 'us-east-1',
        credentials: sessionStore.getActiveCredentials(store),
      }).send(new UpdateAccountPasswordPolicyCommand({
        MinimumPasswordLength:      12,
        RequireUppercaseCharacters: true,
        RequireLowercaseCharacters: true,
        RequireNumbers:             true,
        RequireSymbols:             true,
        PasswordReusePrevention:    5,
        MaxPasswordAge:             90,
        HardExpiry:                 false,
      }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][set-iam-password-policy]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── S3 block public access ────────────────────────────────────────────────

  handleIpc('block-s3-public-access', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand }           = require('@aws-sdk/client-sts')
      const { S3ControlClient, PutPublicAccessBlockCommand }  = require('@aws-sdk/client-s3-control')
      const creds = sessionStore.getActiveCredentials(store)

      const { Account } = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetCallerIdentityCommand({}))

      await new S3ControlClient({ region: 'us-east-1', credentials: creds })
        .send(new PutPublicAccessBlockCommand({
          AccountId: Account,
          PublicAccessBlockConfiguration: {
            BlockPublicAcls:       true,
            IgnorePublicAcls:      true,
            BlockPublicPolicy:     true,
            RestrictPublicBuckets: true,
          },
        }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][block-s3-public-access]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── GuardDuty ─────────────────────────────────────────────────────────────

  handleIpc('enable-guardduty', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { GuardDutyClient, CreateDetectorCommand } = require('@aws-sdk/client-guardduty')
      await new GuardDutyClient({
        region: store.region || 'eu-west-1',
        credentials: sessionStore.getActiveCredentials(store),
      }).send(new CreateDetectorCommand({ Enable: true }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][enable-guardduty]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── IAM Access Analyzer ───────────────────────────────────────────────────

  handleIpc('enable-access-analyzer', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { AccessAnalyzerClient, CreateAnalyzerCommand } = require('@aws-sdk/client-accessanalyzer')
      await new AccessAnalyzerClient({
        region: store.region || 'eu-west-1',
        credentials: sessionStore.getActiveCredentials(store),
      }).send(new CreateAnalyzerCommand({ analyzerName: 'account-analyzer', type: 'ACCOUNT' }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][enable-access-analyzer]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Cost anomaly detection ────────────────────────────────────────────────

  handleIpc('create-anomaly-detection', async (_event, { threshold, email, phone }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const {
        CostExplorerClient,
        CreateAnomalyMonitorCommand,
        GetAnomalyMonitorsCommand,
        CreateAnomalySubscriptionCommand,
        UpdateAnomalySubscriptionCommand,
        GetAnomalySubscriptionsCommand,
      } = require('@aws-sdk/client-cost-explorer')

      const creds = sessionStore.getActiveCredentials(store)

      const subscribers = [{ Address: email, Type: 'EMAIL' }]

      if (phone) {
        const { SNSClient } = require('@aws-sdk/client-sns')
        const snsClient = new SNSClient({ region: 'us-east-1', credentials: creds })
        const TopicArn = await createAlertTopic(snsClient, { name: 'anomaly-sms-alerts', principal: 'costalerts.amazonaws.com', phone })
        subscribers.push({ Address: TopicArn, Type: 'SNS' })
      }

      const client = new CostExplorerClient({ region: 'us-east-1', credentials: creds })

      // Cost Explorer doesn't reject duplicate monitor/subscription names the
      // way Budgets does — re-running create would silently pile up a second
      // monitor and subscription. List first and update in place if found.
      const monitorName = 'all-services-monitor'
      const { AnomalyMonitors = [] } = await client.send(new GetAnomalyMonitorsCommand({}))
      let monitorArn = AnomalyMonitors.find(m => m.MonitorName === monitorName)?.MonitorArn

      if (!monitorArn) {
        const created = await client.send(new CreateAnomalyMonitorCommand({
          AnomalyMonitor: {
            MonitorName:      monitorName,
            MonitorType:      'DIMENSIONAL',
            MonitorDimension: 'SERVICE',
          },
        }))
        monitorArn = created.MonitorArn
      }

      const subscriptionName = 'anomaly-alert'
      const { AnomalySubscriptions = [] } = await client.send(new GetAnomalySubscriptionsCommand({ MonitorArn: monitorArn }))
      const existingSubscription = AnomalySubscriptions.find(s => s.SubscriptionName === subscriptionName)

      if (existingSubscription) {
        await client.send(new UpdateAnomalySubscriptionCommand({
          SubscriptionArn: existingSubscription.SubscriptionArn,
          Threshold:       threshold,
          Subscribers:     subscribers,
        }))
      } else {
        await client.send(new CreateAnomalySubscriptionCommand({
          AnomalySubscription: {
            SubscriptionName: subscriptionName,
            MonitorArnList:   [monitorArn],
            Subscribers:      subscribers,
            Threshold:        threshold,
            Frequency:        'IMMEDIATE',
          },
        }))
      }

      return { ok: true }
    } catch (error) {
      log.error('[ipc][create-anomaly-detection]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── GuardDuty SMS alert ───────────────────────────────────────────────────
  // Creates an SNS SMS subscription and an EventBridge rule so HIGH-severity
  // GuardDuty findings trigger a text message to the given phone number.

  handleIpc('enable-sms-security-alert', async (_event, { phone }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { SNSClient } = require('@aws-sdk/client-sns')
      const { EventBridgeClient } = require('@aws-sdk/client-eventbridge')

      const region = store.region || 'eu-west-1'
      const creds  = sessionStore.getActiveCredentials(store)

      const snsClient = new SNSClient({ region, credentials: creds })
      const TopicArn = await createAlertTopic(snsClient, { name: 'guardduty-security-alerts', principal: 'events.amazonaws.com', phone })

      const ebClient = new EventBridgeClient({ region, credentials: creds })
      await putAlertRule(ebClient, {
        name:         'guardduty-high-severity-findings',
        description:  'SMS alert for GuardDuty HIGH severity findings',
        eventPattern: {
          source:        ['aws.guardduty'],
          'detail-type': ['GuardDuty Finding'],
          detail:        { severity: [{ numeric: ['>=', 7] }] },
        },
        targetArn:     TopicArn,
        inputPathsMap: { severity: '$.detail.severity', type: '$.detail.type', region: '$.region' },
        inputTemplate: '"AWS ALERT: GuardDuty - <type> (severity <severity>) in <region>"',
      })

      return { ok: true }
    } catch (error) {
      log.error('[ipc][enable-sms-security-alert]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Root credential status ────────────────────────────────────────────────
  // Calls GetAccountSummary to check whether root access keys and root MFA are
  // enabled. Works with both root and IAM credentials (needs iam:GetAccountSummary).

  handleIpc('check-root-credentials', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient, GetAccountSummaryCommand, ListMFADevicesCommand } = require('@aws-sdk/client-iam')
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
      const iam = new IAMClient({ region: 'us-east-1', credentials: creds })

      const [summaryRes, identityRes] = await Promise.all([
        iam.send(new GetAccountSummaryCommand({})),
        new STSClient({ region: 'us-east-1', credentials: creds }).send(new GetCallerIdentityCommand({})),
      ])

      const map = summaryRes.SummaryMap ?? {}
      const isRoot = identityRes.Arn?.endsWith(':root') ?? false

      let iamMfaEnabled = false
      if (!isRoot) {
        const { MFADevices = [] } = await iam.send(new ListMFADevicesCommand({}))
        iamMfaEnabled = MFADevices.length > 0
      }

      return {
        ok:          true,
        keysPresent: (map['AccountAccessKeysPresent'] ?? 0) > 0,
        mfaEnabled:  (map['AccountMFAEnabled'] ?? 0) > 0,
        accountId:   identityRes.Account,
        isRoot,
        iamMfaEnabled,
      }
    } catch (error) {
      log.error('[ipc][check-root-credentials]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Root access key deletion ───────────────────────────────────────────────
  // Deletes the currently-stored credentials' access keys — but only after
  // deleteAccessKeysIfRoot confirms via STS that they belong to root.

  handleIpc('delete-root-access-keys', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient } = require('@aws-sdk/client-iam')
      const creds  = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
      const client = new IAMClient({ region: 'us-east-1', credentials: creds })

      const deleted = await deleteAccessKeysIfRoot(client, creds)
      return deleted
        ? { ok: true }
        : { ok: false, error: 'Current credentials are not root — refusing to delete access keys.' }
    } catch (error) {
      log.error('[ipc][delete-root-access-keys]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Virtual MFA device creation ───────────────────────────────────────────
  // Creates a virtual MFA device for root. Returns a base64 QR code PNG and
  // the base32 TOTP seed. Must be called while root credentials are active.

  handleIpc('create-virtual-mfa-device', async (_event, { deviceName } = {}) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient, CreateVirtualMFADeviceCommand } = require('@aws-sdk/client-iam')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

      const { VirtualMFADevice } = await new IAMClient({ region: 'us-east-1', credentials: creds })
        .send(new CreateVirtualMFADeviceCommand({ VirtualMFADeviceName: deviceName || 'root-account-mfa-device' }))

      return {
        ok:           true,
        serialNumber: VirtualMFADevice.SerialNumber,
        qrCodePng:    Buffer.from(VirtualMFADevice.QRCodePNG).toString('base64'),
        base32Seed:   Buffer.from(VirtualMFADevice.Base32StringSeed).toString('utf8'),
      }
    } catch (error) {
      log.error('[ipc][create-virtual-mfa-device]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Enable MFA device ─────────────────────────────────────────────────────
  // Activates the virtual MFA device using two consecutive TOTP codes.
  // Omitting UserName causes the API to apply the device to the caller (root).

  handleIpc('enable-mfa-device', async (_event, { serialNumber, authCode1, authCode2, userName }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient, EnableMFADeviceCommand } = require('@aws-sdk/client-iam')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

      await new IAMClient({ region: 'us-east-1', credentials: creds })
        .send(new EnableMFADeviceCommand({
          ...(userName ? { UserName: userName } : {}), // omitted ⇒ API applies to caller (root)
          SerialNumber:        serialNumber,
          AuthenticationCode1: authCode1,
          AuthenticationCode2: authCode2,
        }))

      return { ok: true }
    } catch (error) {
      log.error('[ipc][enable-mfa-device]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── STS session (MFA-gated) ───────────────────────────────────────────────
  // Mints a 4-hour STS session for the IAM user using their own MFA device.
  // The base permanent creds are used to call GetSessionToken (this is one of
  // the actions the mfa-enforcement-policy exempts from requiring MFA itself);
  // the resulting session lives only in-memory (session-store.js) and is what
  // subsequent privileged handlers use via sessionStore.getActiveCredentials().

  handleIpc('get-session-token', async (_event, { authCode }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient, ListMFADevicesCommand } = require('@aws-sdk/client-iam')
      const { STSClient, GetSessionTokenCommand } = require('@aws-sdk/client-sts')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

      const { MFADevices = [] } = await new IAMClient({ region: 'us-east-1', credentials: creds })
        .send(new ListMFADevicesCommand({}))
      const serialNumber = MFADevices[0]?.SerialNumber
      if (!serialNumber) {
        return { ok: false, error: 'No MFA device enrolled for this IAM user yet.' }
      }

      const { Credentials } = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetSessionTokenCommand({ SerialNumber: serialNumber, TokenCode: authCode, DurationSeconds: 14400 }))

      sessionStore.setSession({
        baseAccessKeyId: store.accessKeyId,
        accessKeyId:     Credentials.AccessKeyId,
        secretAccessKey: Credentials.SecretAccessKey,
        sessionToken:    Credentials.SessionToken,
        expiresAt:       Credentials.Expiration.getTime(),
      })

      return { ok: true, expiresAt: Credentials.Expiration.getTime() }
    } catch (error) {
      log.error('[ipc][get-session-token]', error.message)
      return { ok: false, error: error.message }
    }
  })

  handleIpc('get-session-status', async () => {
    return { ok: true, ...sessionStore.getStatus() }
  })

  // ── Root login alarm ──────────────────────────────────────────────────────
  // Creates an SNS topic + EventBridge rule that fires on every root console
  // sign-in. AWS routes aws.signin CloudTrail events to EventBridge by default,
  // so no explicit CloudTrail trail is needed.

  handleIpc('create-root-login-alarm', async (_event, { email, phone }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { SNSClient } = require('@aws-sdk/client-sns')
      const { EventBridgeClient } = require('@aws-sdk/client-eventbridge')

      const region = store.region || 'eu-west-1'
      const creds  = sessionStore.getActiveCredentials(store)

      const sns = new SNSClient({ region, credentials: creds })
      const TopicArn = await createAlertTopic(sns, { name: 'root-login-alarm', principal: 'events.amazonaws.com', email, phone })

      const eb = new EventBridgeClient({ region, credentials: creds })
      await putAlertRule(eb, {
        name:         'root-account-login-alarm',
        description:  'Alert on every root account console sign-in',
        eventPattern: {
          source:        ['aws.signin'],
          'detail-type': ['AWS Console Sign In via CloudTrail'],
          detail:        { userIdentity: { type: ['Root'] } },
        },
        targetArn:     TopicArn,
        inputPathsMap: { account: '$.account', region: '$.region', time: '$.time' },
        inputTemplate: '"AWS ALERT: Root account sign-in detected in <region> at <time> (account <account>)"',
      })

      return { ok: true }
    } catch (error) {
      log.error('[ipc][create-root-login-alarm]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Log viewer ────────────────────────────────────────────────────────────

  handleIpc('read-log', async () => {
    try {
      const content = await fs.promises.readFile(log.LOG_FILE, 'utf8')
      const lines = content.split('\n')
      return { ok: true, content: lines.slice(-500).join('\n') }
    } catch {
      return { ok: true, content: '' }
    }
  })

  handleIpc('open-log-dir', async () => {
    const result = await shell.openPath(log.LOG_DIR)
    return result ? { ok: false, error: result } : { ok: true }
  })


  handleIpc('open-external', async (_event, url) => {
    try {
      await shell.openExternal(url)
      return { ok: true }
    } catch (error) {
      log.error('[ipc][open-external]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Error logging ─────────────────────────────────────────────────────────

  handleIpc('log-error', async (_event, message, stack) => {
    log.error('[renderer]', message, stack)
  })
}

module.exports = { registerIpcHandlers }
