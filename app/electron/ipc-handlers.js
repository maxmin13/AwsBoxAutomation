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
const SILENT_CHANNELS = new Set(['read-log', 'load-credentials', 'save-credentials', 'get-session-token', 'create-iam-user', 'rotate-access-key'])

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
  if (!identity.Arn?.endsWith(':root')) {
    log.info(`[ipc][root-key-deletion] caller "${identity.Arn}" is not root — declining to delete anything`)
    return false
  }

  const { AccessKeyMetadata = [] } = await client.send(new ListAccessKeysCommand({}))
  log.info(`[ipc][root-key-deletion] root has ${AccessKeyMetadata.length} access key(s): ${AccessKeyMetadata.map(k => k.AccessKeyId).join(', ') || '(none)'}`)
  for (const key of AccessKeyMetadata) {
    await client.send(new DeleteAccessKeyCommand({ AccessKeyId: key.AccessKeyId }))
    log.info(`[ipc][root-key-deletion] deleted root access key ${key.AccessKeyId}`)
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
    // create-iam-user is in SILENT_CHANNELS (its reply carries a freshly
    // minted secretAccessKey), so the generic recv/reply logging in
    // handleIpc() is suppressed for this channel — log the non-secret
    // parts explicitly instead, so the flow is still visible in gui.log.
    log.info(`[ipc][create-iam-user] recv username="${username}" policyArn="${policyArn}" deleteRootKeys=${deleteRootKeys}`)
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      log.info('[ipc][create-iam-user] no credentials configured')
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const {
        IAMClient,
        CreateUserCommand,
        AttachUserPolicyCommand,
        PutUserPolicyCommand,
        CreateAccessKeyCommand,
        DeleteAccessKeyCommand,
        ListAccessKeysCommand,
      } = require('@aws-sdk/client-iam')
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')

      const creds  = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
      const client = new IAMClient({ region: 'us-east-1', credentials: creds })

      // CreateUser isn't idempotent, so a retry after an earlier partial
      // failure (e.g. CreateAccessKey failed) would otherwise dead-end here
      // with EntityAlreadyExists. Treat that one error as "resume" — the two
      // calls below are already idempotent (AttachUserPolicy no-ops if
      // already attached, PutUserPolicy overwrites), so it's safe to just
      // carry on and finish provisioning this user.
      let resumed = false
      try {
        await client.send(new CreateUserCommand({ UserName: username }))
      } catch (err) {
        if (err.name !== 'EntityAlreadyExistsException') throw err
        resumed = true
        log.info(`[ipc][create-iam-user] user "${username}" already exists — resuming (retry after earlier partial failure, or re-run with same name)`)
      }
      await client.send(new AttachUserPolicyCommand({ UserName: username, PolicyArn: policyArn }))
      await client.send(new PutUserPolicyCommand({
        UserName:       username,
        PolicyName:     'enforce-mfa-for-privileged-actions',
        PolicyDocument: JSON.stringify(mfaEnforcementPolicy),
      }))

      // CreateAccessKey is never idempotent — it always mints a new key, and
      // IAM caps a user at 2. Check first so a resumed retry doesn't pile up
      // keys, and so hitting the cap surfaces a clear message instead of a
      // raw LimitExceeded error.
      const { AccessKeyMetadata = [] } = await client.send(new ListAccessKeysCommand({ UserName: username }))
      if (AccessKeyMetadata.length >= 2) {
        log.info(`[ipc][create-iam-user] user "${username}" already has ${AccessKeyMetadata.length} access keys — declining to create another`)
        return {
          ok: false,
          error: `IAM user "${username}" already has 2 access keys and neither secret can be retrieved again. Delete one in the AWS console, then retry.`,
        }
      }

      const keyResponse = await client.send(new CreateAccessKeyCommand({ UserName: username }))
      const key = keyResponse.AccessKey
      log.info(`[ipc][create-iam-user] created access key ${key.AccessKeyId} for user "${username}"`)

      // Verify the new key actually authenticates, persist it to disk, and
      // only THEN delete root's key (if asked to). Doing it in this order
      // means a crash/lost-IPC-response after this point can never leave
      // disk pointing at a dead credential — by the time root's key is
      // deleted, disk already holds a confirmed-working replacement.
      try {
        await new STSClient({ region: 'us-east-1', credentials: { accessKeyId: key.AccessKeyId, secretAccessKey: key.SecretAccessKey } })
          .send(new GetCallerIdentityCommand({}))
        log.info(`[ipc][create-iam-user] verified new access key ${key.AccessKeyId} authenticates`)
      } catch (verifyErr) {
        log.error(`[ipc][create-iam-user] new access key ${key.AccessKeyId} failed verification, deleting it`, verifyErr.message)
        await client.send(new DeleteAccessKeyCommand({ AccessKeyId: key.AccessKeyId, UserName: username })).catch(() => {})
        return { ok: false, error: 'New access key could not be verified — nothing was changed. IAM keys can take a few seconds to propagate; try again shortly.' }
      }

      await writeCredsStore({ ...store, accessKeyId: key.AccessKeyId, secretAccessKey: key.SecretAccessKey })
      log.info(`[ipc][create-iam-user] persisted new access key ${key.AccessKeyId} to disk`)

      let rootKeysDeleted = false
      if (deleteRootKeys) {
        rootKeysDeleted = await deleteAccessKeysIfRoot(client, creds)
      }

      log.info(`[ipc][create-iam-user] reply ok=true accessKeyId=${key.AccessKeyId} rootKeysDeleted=${rootKeysDeleted} resumed=${resumed}`)
      return { ok: true, accessKeyId: key.AccessKeyId, secretAccessKey: key.SecretAccessKey, rootKeysDeleted, resumed }
    } catch (error) {
      log.error('[ipc][create-iam-user]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── IAM user access key rotation ──────────────────────────────────────────
  // iam:CreateAccessKey / iam:DeleteAccessKey aren't in mfa-enforcement-policy's
  // no-MFA whitelist, so this only works with an active MFA-gated session
  // (sessionStore.getActiveCredentials) — the renderer gates the button the
  // same way as the other privileged security actions (withSession).
  //
  // Order matters: create the new key, verify it actually authenticates,
  // THEN persist it to disk and delete the old one. If verification fails,
  // the new key is deleted and nothing on disk changes — the old key (still
  // valid) keeps working. This avoids ever locking the user out mid-rotation.
  handleIpc('rotate-access-key', async () => {
    log.info('[ipc][rotate-access-key] recv')
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      log.info('[ipc][rotate-access-key] no credentials configured')
      return { ok: false, error: 'No credentials configured.' }
    }
    const oldAccessKeyId = store.accessKeyId
    try {
      const { IAMClient, CreateAccessKeyCommand, DeleteAccessKeyCommand } = require('@aws-sdk/client-iam')
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const creds  = sessionStore.getActiveCredentials(store)
      const client = new IAMClient({ region: 'us-east-1', credentials: creds })

      let newKey
      try {
        // UserName omitted — IAM infers "the caller's own user" from the
        // signing credentials, which is what we want here.
        ;({ AccessKey: newKey } = await client.send(new CreateAccessKeyCommand({})))
      } catch (err) {
        if (err.name === 'LimitExceededException') {
          return { ok: false, error: 'This IAM user already has 2 access keys. Delete one in the AWS console before rotating.' }
        }
        throw err
      }
      log.info(`[ipc][rotate-access-key] created new access key ${newKey.AccessKeyId}`)

      try {
        await new STSClient({ region: 'us-east-1', credentials: { accessKeyId: newKey.AccessKeyId, secretAccessKey: newKey.SecretAccessKey } })
          .send(new GetCallerIdentityCommand({}))
      } catch (verifyErr) {
        log.error('[ipc][rotate-access-key] new key failed verification, deleting it', verifyErr.message)
        await client.send(new DeleteAccessKeyCommand({ AccessKeyId: newKey.AccessKeyId })).catch(() => {})
        return { ok: false, error: 'New access key could not be verified — nothing was changed. IAM keys can take a few seconds to propagate; try again shortly.' }
      }

      await writeCredsStore({ ...store, accessKeyId: newKey.AccessKeyId, secretAccessKey: newKey.SecretAccessKey })
      sessionStore.clearSession() // the old session was minted for the key we're about to delete
      await client.send(new DeleteAccessKeyCommand({ AccessKeyId: oldAccessKeyId }))
      log.info(`[ipc][rotate-access-key] reply ok=true newAccessKeyId=${newKey.AccessKeyId} deletedAccessKeyId=${oldAccessKeyId}`)

      return { ok: true, accessKeyId: newKey.AccessKeyId, secretAccessKey: newKey.SecretAccessKey }
    } catch (error) {
      log.error('[ipc][rotate-access-key]', error.message)
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

  handleIpc('disable-guardduty', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { GuardDutyClient, ListDetectorsCommand, DeleteDetectorCommand } = require('@aws-sdk/client-guardduty')
      const client = new GuardDutyClient({
        region: store.region || 'eu-west-1',
        credentials: sessionStore.getActiveCredentials(store),
      })
      const { DetectorIds = [] } = await client.send(new ListDetectorsCommand({}))
      for (const DetectorId of DetectorIds) {
        await client.send(new DeleteDetectorCommand({ DetectorId }))
      }
      return { ok: true }
    } catch (error) {
      log.error('[ipc][disable-guardduty]', error.message)
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

      // AWS caps IMMEDIATE-frequency anomaly subscriptions at exactly one
      // subscriber — email and phone can't be registered as two separate
      // entries. When both are set, fan them both out through a single
      // shared SNS topic instead so there's only ever one subscriber.
      let subscribers
      if (phone) {
        const { SNSClient } = require('@aws-sdk/client-sns')
        const snsClient = new SNSClient({ region: 'us-east-1', credentials: creds })
        const TopicArn = await createAlertTopic(snsClient, { name: 'anomaly-sms-alerts', principal: 'costalerts.amazonaws.com', email, phone })
        subscribers = [{ Address: TopicArn, Type: 'SNS' }]
      } else {
        subscribers = [{ Address: email, Type: 'EMAIL' }]
      }

      const client = new CostExplorerClient({ region: 'us-east-1', credentials: creds })

      // Cost Explorer doesn't reject duplicate monitor/subscription names the
      // way Budgets does — re-running create would silently pile up a second
      // monitor and subscription. List first and update in place if found.
      // AWS also caps accounts at one DIMENSIONAL monitor total, so reuse any
      // existing one by type rather than requiring an exact name match — a
      // stray monitor from earlier testing or the Console would otherwise
      // cause CreateAnomalyMonitorCommand to fail with LimitExceededException.
      const monitorName = 'all-services-monitor'
      const { AnomalyMonitors = [] } = await client.send(new GetAnomalyMonitorsCommand({}))
      let monitorArn = AnomalyMonitors.find(m => m.MonitorType === 'DIMENSIONAL')?.MonitorArn

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

  // ── Cost summary (free) ───────────────────────────────────────────────────
  // Reads the existing AWS Budget (created in create-billing-alert) for a free
  // month-to-date actual + forecasted total. No Cost Explorer calls here.

  handleIpc('get-cost-summary', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
      const { BudgetsClient, DescribeBudgetCommand } = require('@aws-sdk/client-budgets')

      const creds = sessionStore.getActiveCredentials(store)

      const identity = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetCallerIdentityCommand({}))

      const budgetsClient = new BudgetsClient({ region: 'us-east-1', credentials: creds })

      let budget
      try {
        ({ Budget: budget } = await budgetsClient.send(new DescribeBudgetCommand({
          AccountId:  identity.Account,
          BudgetName: 'monthly-limit',
        })))
      } catch (error) {
        if (error.name === 'NotFoundException') return { ok: true, configured: false }
        throw error
      }

      return {
        ok:              true,
        configured:      true,
        limit:           budget.BudgetLimit.Amount,
        unit:            budget.BudgetLimit.Unit,
        actualSpend:     budget.CalculatedSpend?.ActualSpend?.Amount ?? '0',
        forecastedSpend: budget.CalculatedSpend?.ForecastedSpend?.Amount ?? null,
        periodEnd:       budget.TimePeriod?.End ?? null,
      }
    } catch (error) {
      log.error('[ipc][get-cost-summary]', error.message)
      return { ok: false, error: error.message }
    }
  })

  // ── Cost breakdown by service (paid — Cost Explorer bills per request) ─────
  // Only called when the user explicitly clicks "Show breakdown by service".

  handleIpc('get-cost-breakdown', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { CostExplorerClient, GetCostAndUsageCommand } = require('@aws-sdk/client-cost-explorer')

      const creds  = sessionStore.getActiveCredentials(store)
      const client = new CostExplorerClient({ region: 'us-east-1', credentials: creds })

      const now   = new Date()
      const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
      const tomorrow = new Date(now)
      tomorrow.setDate(tomorrow.getDate() + 1)
      const end = tomorrow.toISOString().slice(0, 10) // End is exclusive — include today's cost

      const { ResultsByTime = [] } = await client.send(new GetCostAndUsageCommand({
        TimePeriod:  { Start: start, End: end },
        Granularity: 'MONTHLY',
        Metrics:     ['UnblendedCost'],
        GroupBy:     [{ Type: 'DIMENSION', Key: 'SERVICE' }],
      }))

      const groups = ResultsByTime[0]?.Groups ?? []
      const services = groups
        .map(g => ({
          service: g.Keys[0],
          amount:  g.Metrics.UnblendedCost.Amount,
          unit:    g.Metrics.UnblendedCost.Unit,
        }))
        .filter(s => parseFloat(s.amount) > 0)
        .sort((a, b) => parseFloat(b.amount) - parseFloat(a.amount))

      return { ok: true, services, start, end }
    } catch (error) {
      log.error('[ipc][get-cost-breakdown]', error.message)
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

  handleIpc('disable-sms-security-alert', async () => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured. Save your AWS credentials first.' }
    }
    try {
      const { SNSClient, DeleteTopicCommand } = require('@aws-sdk/client-sns')
      const { EventBridgeClient, RemoveTargetsCommand, DeleteRuleCommand } = require('@aws-sdk/client-eventbridge')
      const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')

      const region = store.region || 'eu-west-1'
      const creds  = sessionStore.getActiveCredentials(store)
      const ruleName = 'guardduty-high-severity-findings'

      const ebClient = new EventBridgeClient({ region, credentials: creds })
      try {
        await ebClient.send(new RemoveTargetsCommand({ Rule: ruleName, Ids: [`${ruleName}-target`] }))
        await ebClient.send(new DeleteRuleCommand({ Name: ruleName }))
      } catch (error) {
        if (error.name !== 'ResourceNotFoundException') throw error
      }

      // Topic name is deterministic (same one enable-sms-security-alert
      // creates via createAlertTopic), so its ARN can be built directly
      // without a ListTopics round-trip.
      const { Account } = await new STSClient({ region: 'us-east-1', credentials: creds })
        .send(new GetCallerIdentityCommand({}))
      const TopicArn = `arn:aws:sns:${region}:${Account}:guardduty-security-alerts`
      try {
        await new SNSClient({ region, credentials: creds }).send(new DeleteTopicCommand({ TopicArn }))
      } catch (error) {
        if (error.name !== 'NotFoundException') throw error
      }

      return { ok: true }
    } catch (error) {
      log.error('[ipc][disable-sms-security-alert]', error.message)
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
      let iamUsername
      if (!isRoot) {
        const { MFADevices = [] } = await iam.send(new ListMFADevicesCommand({}))
        iamMfaEnabled = MFADevices.length > 0
        iamUsername = identityRes.Arn?.split('/').pop()
      }

      return {
        ok:          true,
        keysPresent: (map['AccountAccessKeysPresent'] ?? 0) > 0,
        mfaEnabled:  (map['AccountMFAEnabled'] ?? 0) > 0,
        accountId:   identityRes.Account,
        isRoot,
        iamMfaEnabled,
        iamUsername,
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
      const {
        IAMClient,
        CreateVirtualMFADeviceCommand,
        ListVirtualMFADevicesCommand,
        DeleteVirtualMFADeviceCommand,
      } = require('@aws-sdk/client-iam')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
      const client = new IAMClient({ region: 'us-east-1', credentials: creds })
      const name   = deviceName || 'root-account-mfa-device'

      let VirtualMFADevice
      try {
        ({ VirtualMFADevice } = await client.send(
          new CreateVirtualMFADeviceCommand({ VirtualMFADeviceName: name })))
      } catch (error) {
        if (error.name !== 'EntityAlreadyExistsException') throw error
        // A device with this name exists but was never enabled (e.g. a
        // previous attempt failed after creation) — AWS only returns the
        // QR/seed once, at creation, so the only way to get a fresh one is
        // to delete the orphaned, unassigned device and recreate it.
        const { VirtualMFADevices = [] } = await client.send(
          new ListVirtualMFADevicesCommand({ AssignmentStatus: 'Unassigned' }))
        const orphan = VirtualMFADevices.find(d => d.SerialNumber?.endsWith(`:mfa/${name}`))
        if (!orphan) throw error
        await client.send(new DeleteVirtualMFADeviceCommand({ SerialNumber: orphan.SerialNumber }))
        ;({ VirtualMFADevice } = await client.send(
          new CreateVirtualMFADeviceCommand({ VirtualMFADeviceName: name })))
      }

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
  // UserName is a required field on this API (unlike ListMFADevices, which
  // defaults to the caller when omitted) — root has no IAM UserName, so AWS's
  // documented workaround for enabling root's own MFA device via this API is
  // to pass the 12-digit account ID as UserName instead.

  handleIpc('enable-mfa-device', async (_event, { serialNumber, authCode1, authCode2, userName }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    try {
      const { IAMClient, EnableMFADeviceCommand } = require('@aws-sdk/client-iam')
      const creds = { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }

      let targetUserName = userName
      if (!targetUserName) {
        const { STSClient, GetCallerIdentityCommand } = require('@aws-sdk/client-sts')
        const identity = await new STSClient({ region: 'us-east-1', credentials: creds })
          .send(new GetCallerIdentityCommand({}))
        targetUserName = identity.Account
      }

      await new IAMClient({ region: 'us-east-1', credentials: creds })
        .send(new EnableMFADeviceCommand({
          UserName:            targetUserName,
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
  // Mints an STS session for the IAM user using their own MFA device, with a
  // caller-chosen duration (default 4h). The base permanent creds are used to
  // call GetSessionToken (this is one of the actions the mfa-enforcement-policy
  // exempts from requiring MFA itself); the resulting session lives only
  // in-memory (session-store.js) and is what subsequent privileged handlers
  // use via sessionStore.getActiveCredentials().

  // GetSessionToken's own limits for an IAM user (not root): 900s (15 min) to
  // 129600s (36 hours).
  const MIN_SESSION_SECONDS = 900
  const MAX_SESSION_SECONDS = 129600

  handleIpc('get-session-token', async (_event, { authCode, durationSeconds }) => {
    const store = await readCredsStore()
    if (!store.accessKeyId || !store.secretAccessKey) {
      return { ok: false, error: 'No credentials configured.' }
    }
    const clampedDuration = Math.min(
      MAX_SESSION_SECONDS,
      Math.max(MIN_SESSION_SECONDS, durationSeconds || 14400)
    )
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
        .send(new GetSessionTokenCommand({ SerialNumber: serialNumber, TokenCode: authCode, DurationSeconds: clampedDuration }))

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
