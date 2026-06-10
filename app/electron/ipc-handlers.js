// ============================================================
//  ipc-handlers.js — registers all ipcMain.handle() calls
// ============================================================

const { ipcMain, app, shell } = require('electron')
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
    const raw = await fs.promises.readFile(CREDS_FILE, 'utf8')
    return JSON.parse(Buffer.from(raw.trim(), 'base64').toString('utf8'))
  } catch {
    return {}
  }
}

async function writeCredsStore(data) {
  await fs.promises.mkdir(CREDS_DIR, { recursive: true })
  const encoded = Buffer.from(JSON.stringify(data, null, 2), 'utf8').toString('base64')
  await fs.promises.writeFile(CREDS_FILE, encoded, 'utf8')
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
