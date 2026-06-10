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

  // ── Datacenter ────────────────────────────────────────────
  describeDatacenter: () =>
    ipcRenderer.invoke('describe-datacenter'),

  startInstance: (instanceId) =>
    ipcRenderer.invoke('start-instance', instanceId),

  stopInstance: (instanceId) =>
    ipcRenderer.invoke('stop-instance', instanceId),

  // ── Log viewer ────────────────────────────────────────────
  readLog: () => ipcRenderer.invoke('read-log'),

  openLogDir: () => ipcRenderer.invoke('open-log-dir'),

  // ── Error logging ─────────────────────────────────────────
  logError: (message, stack) => ipcRenderer.invoke('log-error', message, stack),
})
