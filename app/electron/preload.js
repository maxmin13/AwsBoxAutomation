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

  validateCredentials:  (accessKeyId, secretAccessKey, region) =>
    ipcRenderer.invoke('validate-credentials', accessKeyId ? { accessKeyId, secretAccessKey, region } : undefined),
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

  rotateAccessKey: () =>
    ipcRenderer.invoke('rotate-access-key'),

  createBillingAlert: (amount, email, phone) =>
    ipcRenderer.invoke('create-billing-alert', { amount, email, phone }),

  setIamPasswordPolicy: () =>
    ipcRenderer.invoke('set-iam-password-policy'),

  blockS3PublicAccess: () =>
    ipcRenderer.invoke('block-s3-public-access'),

  enableGuardDuty: () =>
    ipcRenderer.invoke('enable-guardduty'),

  disableGuardDuty: () =>
    ipcRenderer.invoke('disable-guardduty'),

  enableAccessAnalyzer: () =>
    ipcRenderer.invoke('enable-access-analyzer'),

  createAnomalyDetection: (threshold, email, phone) =>
    ipcRenderer.invoke('create-anomaly-detection', { threshold, email, phone }),

  enableSmsSecurityAlert: (phone) =>
    ipcRenderer.invoke('enable-sms-security-alert', { phone }),

  disableSmsSecurityAlert: () =>
    ipcRenderer.invoke('disable-sms-security-alert'),

  // ── Costs ──────────────────────────────────────────────────
  getCostSummary: () =>
    ipcRenderer.invoke('get-cost-summary'),

  getCostBreakdown: () =>
    ipcRenderer.invoke('get-cost-breakdown'),

  // ── Root security ─────────────────────────────────────────
  checkRootCredentials: () =>
    ipcRenderer.invoke('check-root-credentials'),

  deleteRootAccessKeys: () =>
    ipcRenderer.invoke('delete-root-access-keys'),

  createVirtualMfaDevice: (deviceName) =>
    ipcRenderer.invoke('create-virtual-mfa-device', { deviceName }),

  enableMfaDevice: (serialNumber, authCode1, authCode2, userName) =>
    ipcRenderer.invoke('enable-mfa-device', { serialNumber, authCode1, authCode2, userName }),

  createRootLoginAlarm: (email, phone) =>
    ipcRenderer.invoke('create-root-login-alarm', { email, phone }),

  // ── MFA-gated session ─────────────────────────────────────
  getSessionToken: (authCode, durationSeconds) =>
    ipcRenderer.invoke('get-session-token', { authCode, durationSeconds }),

  getSessionStatus: () =>
    ipcRenderer.invoke('get-session-status'),

  // ── Log viewer ────────────────────────────────────────────
  readLog: () => ipcRenderer.invoke('read-log'),

  openLogDir:   () => ipcRenderer.invoke('open-log-dir'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // ── Error logging ─────────────────────────────────────────
  logError: (message, stack) => ipcRenderer.invoke('log-error', message, stack),
})
