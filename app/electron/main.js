// ============================================================
//  main.js — Electron main process entry point
// ============================================================

const { app, BrowserWindow } = require('electron')
const path = require('path')
const { registerIpcHandlers } = require('./ipc-handlers')
const log = require('./logger')

app.commandLine.appendSwitch('disable-gpu-shader-disk-cache')

if (!app.requestSingleInstanceLock()) {
  app.quit()
}

function createWindow() {
  log.info('[main] creating window')

  const win = new BrowserWindow({
    width: 1100,
    height: 750,
    resizable: false,
    backgroundColor: '#18181b',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  if (!app.isPackaged && process.env.NODE_ENV !== 'production') {
    win.loadURL('http://localhost:5173')
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  return win
}

app.on('second-instance', () => {
  const wins = BrowserWindow.getAllWindows()
  if (wins.length > 0) {
    const win = wins[0]
    if (win.isMinimized()) win.restore()
    win.focus()
  }
})

app.whenReady().then(() => {
  log.info('[main] app ready')
  const win = createWindow()
  registerIpcHandlers(win)
})

app.on('window-all-closed', () => {
  log.info('[main] all windows closed — quitting')
  app.quit()
})

app.on('will-quit', () => {
  log.info('[main] will-quit')
})

app.on('render-process-gone', (_event, _webContents, details) => {
  log.error('[main] render-process-gone', JSON.stringify(details))
})

app.on('child-process-gone', (_event, details) => {
  log.error('[main] child-process-gone', JSON.stringify(details))
})

process.on('uncaughtException', (err) => {
  log.error('[main] uncaughtException:', err.stack || err.message)
})

process.on('unhandledRejection', (reason) => {
  log.error('[main] unhandledRejection:', reason instanceof Error ? reason.stack : String(reason))
})
