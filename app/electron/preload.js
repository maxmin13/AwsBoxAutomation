// ============================================================
//  preload.js — contextBridge between main and renderer
// ============================================================

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {

  // ── Credentials ───────────────────────────────────────────
  loadCredentials: () =>
    ipcRenderer.invoke('load-credentials'),

  saveCredentials: (accessKeyId, secretAccessKey, region) =>
    ipcRenderer.invoke('save-credentials', { accessKeyId, secretAccessKey, region }),

  validateCredentials:  () => ipcRenderer.invoke('validate-credentials'),
  encryptionAvailable:  () => ipcRenderer.invoke('encryption-available'),

  // ── Datacenter ────────────────────────────────────────────
  describeDatacenter: () =>
    ipcRenderer.invoke('describe-datacenter'),

  startInstance: (instanceId) =>
    ipcRenderer.invoke('start-instance', instanceId),

  stopInstance: (instanceId) =>
    ipcRenderer.invoke('stop-instance', instanceId),

  // ── AWS account setup ─────────────────────────────────────
  createIamUser: (username) =>
    ipcRenderer.invoke('create-iam-user', username),

  createBillingAlert: (amount, email) =>
    ipcRenderer.invoke('create-billing-alert', { amount, email }),

  setIamPasswordPolicy: () =>
    ipcRenderer.invoke('set-iam-password-policy'),

  blockS3PublicAccess: () =>
    ipcRenderer.invoke('block-s3-public-access'),

  enableGuardDuty: () =>
    ipcRenderer.invoke('enable-guardduty'),

  enableAccessAnalyzer: () =>
    ipcRenderer.invoke('enable-access-analyzer'),

  createAnomalyDetection: (threshold, email) =>
    ipcRenderer.invoke('create-anomaly-detection', { threshold, email }),

  // ── Log viewer ────────────────────────────────────────────
  readLog: () => ipcRenderer.invoke('read-log'),

  openLogDir: () => ipcRenderer.invoke('open-log-dir'),

  // ── Error logging ─────────────────────────────────────────
  logError: (message, stack) => ipcRenderer.invoke('log-error', message, stack),
})
