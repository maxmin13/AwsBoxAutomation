// ============================================================
//  ipc-handlers.js — registers all ipcMain.handle() calls
// ============================================================

const { ipcMain, app, shell, safeStorage } = require('electron')
const { inspect } = require('util')
const path = require('path')
const fs   = require('fs')
const os   = require('os')
const log = require('./logger')

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
const SILENT_CHANNELS = new Set(['read-log', 'load-credentials', 'save-credentials'])

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

  handleIpc('validate-credentials', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const client = new STSClient({
        region: store.region || 'us-east-1',
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
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
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
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
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
      })
      await client.send(new StopInstancesCommand({ InstanceIds: [instanceId] }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][stop-instance]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── IAM user creation ────────────────────────────────────────────────────
  // Creates an IAM user, attaches AdministratorAccess, and returns a new access key.
  // Credentials are only returned once — the caller must save them immediately.

  handleIpc('create-iam-user', async (_event, username) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const {
        IAMClient,
        CreateUserCommand,
        AttachUserPolicyCommand,
        CreateAccessKeyCommand,
      } = require('@aws-sdk/client-iam')

      const client = new IAMClient({
        region: 'us-east-1',
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
      })

      await client.send(new CreateUserCommand({ UserName: username }))

      await client.send(new AttachUserPolicyCommand({
        UserName: username,
        PolicyArn: 'arn:aws:iam::aws:policy/AdministratorAccess',
      }))

      const keyResponse = await client.send(new CreateAccessKeyCommand({ UserName: username }))
      const key = keyResponse.AccessKey

      return { ok: true, accessKeyId: key.AccessKeyId, secretAccessKey: key.SecretAccessKey }
    } catch (error) {
      log.error('[ipc][create-iam-user]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Billing alert ─────────────────────────────────────────────────────────
  // Creates a monthly AWS Budget and sends an email alert when 80% is reached.

  handleIpc('create-billing-alert', async (_event, { amount, email }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const { BudgetsClient, CreateBudgetCommand }  = require('@aws-sdk/client-budgets')

      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

      const identity = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetCallerIdentityCommand({}))

      await new BudgetsClient({ region: 'us-east-1', credentials: creds })
        .send(new CreateBudgetCommand({
          AccountId: identity.Account,
          Budget: {
            BudgetName: `monthly-limit-${amount}usd`,
            BudgetLimit: { Amount: String(amount), Unit: 'USD' },
            TimeUnit: 'MONTHLY',
            BudgetType: 'COST',
          },
          NotificationsWithSubscribers: [{
            Notification: {
              NotificationType:    'ACTUAL',
              ComparisonOperator:  'GREATER_THAN',
              Threshold:           80,
              ThresholdType:       'PERCENTAGE',
            },
            Subscribers: [{ SubscriptionType: 'EMAIL', Address: email }],
          }],
        }))

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
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
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
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

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
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
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
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
      }).send(new CreateAnalyzerCommand({ analyzerName: 'account-analyzer', type: 'ACCOUNT' }))
      return { ok: true }
    } catch (error) {
      log.error('[ipc][enable-access-analyzer]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Cost anomaly detection ────────────────────────────────────────────────

  handleIpc('create-anomaly-detection', async (_event, { threshold, email }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const {
        CostExplorerClient,
        CreateAnomalyMonitorCommand,
        CreateAnomalySubscriptionCommand,
      } = require('@aws-sdk/client-cost-explorer')

      const client = new CostExplorerClient({
        region: 'us-east-1',
        credentials: { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey },
      })

      const { MonitorArn } = await client.send(new CreateAnomalyMonitorCommand({
        AnomalyMonitor: {
          MonitorName:      'all-services-monitor',
          MonitorType:      'DIMENSIONAL',
          MonitorDimension: 'SERVICE',
        },
      }))

      await client.send(new CreateAnomalySubscriptionCommand({
        AnomalySubscription: {
          SubscriptionName: 'anomaly-alert',
          MonitorArnList:   [MonitorArn],
          Subscribers:      [{ Address: email, Type: 'EMAIL' }],
          Threshold:        threshold,
          Frequency:        'IMMEDIATE',
        },
      }))

      return { ok: true }
    } catch (error) {
      log.error('[ipc][create-anomaly-detection]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Log viewer ────────────────────────────────────────────────────────────

  handleIpc('read-log', async () => {
    try {
      const content = await fs.promises.readFile(log.APP_FILE, 'utf8')
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

  // ── Error logging ─────────────────────────────────────────────────────────

  handleIpc('log-error', async (_event, message, stack) => {
    log.error('[renderer]', message, stack)
  })
}

module.exports = { registerIpcHandlers }
