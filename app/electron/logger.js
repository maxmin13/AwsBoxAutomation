// Shared file logger for the Electron main process.
// Writes to ~/.config/AwsBoxAutomation/logs/gui.log

const fs   = require('fs')
const path = require('path')
const os   = require('os')

const LOG_DIR  = path.join(os.homedir(), '.config', 'AwsBoxAutomation', 'logs')
const LOG_FILE = path.join(LOG_DIR, 'gui.log')

const MAX_GUI = 2 * 1024 * 1024  // 2 MB

function rotate(file, maxBytes) {
  try {
    if (fs.statSync(file).size >= maxBytes) fs.renameSync(file, file + '.1')
  } catch {}
}

try {
  fs.mkdirSync(LOG_DIR, { recursive: true })
} catch {}

function format(level, args) {
  const ts   = new Date().toISOString().replace('T', ' ').slice(0, 23)
  const text = args
    .map((a) => (a !== null && typeof a === 'object' ? JSON.stringify(a) : String(a)))
    .join(' ')
  return `[${ts}] [${level.padEnd(5)}] ${text}\n`
}

function write(level, args) {
  const line = format(level, args)
  try {
    rotate(LOG_FILE, MAX_GUI)
    fs.appendFileSync(LOG_FILE, line, 'utf8')
  } catch {}
}

module.exports = {
  LOG_DIR,
  LOG_FILE,
  info:  (...args) => write('info',  args),
  warn:  (...args) => write('warn',  args),
  error: (...args) => write('error', args),
}
