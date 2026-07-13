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
  createIamUser: (username, policyArn, deleteRootKeys) =>
    ipcRenderer.invoke('create-iam-user', { username, policyArn, deleteRootKeys }),

  createBillingAlert: (amount, email, phone) =>
    ipcRenderer.invoke('create-billing-alert', { amount, email, phone }),

  setIamPasswordPolicy: () =>
    ipcRenderer.invoke('set-iam-password-policy'),

  blockS3PublicAccess: () =>
    ipcRenderer.invoke('block-s3-public-access'),

  enableGuardDuty: () =>
    ipcRenderer.invoke('enable-guardduty'),

  enableAccessAnalyzer: () =>
    ipcRenderer.invoke('enable-access-analyzer'),

  createAnomalyDetection: (threshold, email, phone) =>
    ipcRenderer.invoke('create-anomaly-detection', { threshold, email, phone }),

  enableSmsSecurityAlert: (phone) =>
    ipcRenderer.invoke('enable-sms-security-alert', { phone }),

  // ── Root security ─────────────────────────────────────────
  checkRootCredentials: () =>
    ipcRenderer.invoke('check-root-credentials'),

  deleteRootAccessKeys: () =>
    ipcRenderer.invoke('delete-root-access-keys'),

  createVirtualMfaDevice: () =>
    ipcRenderer.invoke('create-virtual-mfa-device'),

  enableMfaDevice: (serialNumber, authCode1, authCode2) =>
    ipcRenderer.invoke('enable-mfa-device', { serialNumber, authCode1, authCode2 }),

  createRootLoginAlarm: (email, phone) =>
    ipcRenderer.invoke('create-root-login-alarm', { email, phone }),

  // ── Log viewer ────────────────────────────────────────────
  readLog: () => ipcRenderer.invoke('read-log'),

  openLogDir:   () => ipcRenderer.invoke('open-log-dir'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // ── Error logging ─────────────────────────────────────────
  logError: (message, stack) => ipcRenderer.invoke('log-error', message, stack),
})
