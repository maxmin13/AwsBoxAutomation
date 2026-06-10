// Type definitions for the API exposed by preload.js via contextBridge.

export interface Credentials {
  accessKeyId: string
  secretAccessKey: string
  region: string
}

export interface InstanceInfo {
  found:        boolean
  state?:       string
  instanceId?:  string
  instanceType?: string
  publicIp?:    string | null
  publicDns?:   string | null
  launchTime?:  string | null
}

declare global {
  interface Window {
    electronAPI: {
      loadCredentials:    () => Promise<{ ok: boolean } & Credentials>
      saveCredentials:    (accessKeyId: string, secretAccessKey: string, region: string) => Promise<{ ok: boolean }>

      describeDatacenter: () => Promise<{ ok: boolean; error?: string } & InstanceInfo>
      startInstance:      (instanceId: string) => Promise<{ ok: boolean; error?: string }>
      stopInstance:       (instanceId: string) => Promise<{ ok: boolean; error?: string }>

      readLog:    () => Promise<{ ok: boolean; content?: string }>
      openLogDir: () => Promise<{ ok: boolean; error?: string }>
      logError:   (message: string, stack: string) => Promise<void>
    }
  }
}
