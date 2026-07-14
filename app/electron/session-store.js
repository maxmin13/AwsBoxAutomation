// In-memory only. A 4-hour STS session gains nothing from disk persistence
// and persisting it would be a pure liability — it's intentionally lost on
// every app restart, at which point the IAM user just re-authenticates with
// a fresh MFA code via get-session-token.
let session = null // { baseAccessKeyId, accessKeyId, secretAccessKey, sessionToken, expiresAt }

function setSession(s) {
  session = s
}

function clearSession() {
  session = null
}

function getStatus() {
  if (session && Date.now() >= session.expiresAt) session = null
  return session ? { active: true, expiresAt: session.expiresAt } : { active: false }
}

// `store` is the disk creds store ({ accessKeyId, secretAccessKey, region }).
// Returns the credential object to pass into an AWS SDK client constructor.
// Falls back to the permanent creds when: no session exists yet, the session
// expired, or the session was minted for a different base access key than
// what's currently on disk (e.g. user logged into a different account).
function getActiveCredentials(store) {
  if (session && session.baseAccessKeyId === store.accessKeyId && Date.now() < session.expiresAt) {
    return {
      accessKeyId: session.accessKeyId,
      secretAccessKey: session.secretAccessKey,
      sessionToken: session.sessionToken,
    }
  }
  if (session) session = null
  return { accessKeyId: store.accessKeyId, secretAccessKey: store.secretAccessKey }
}

module.exports = { setSession, clearSession, getStatus, getActiveCredentials }
