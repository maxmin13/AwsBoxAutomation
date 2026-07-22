// Type definitions for the API exposed by preload.js via contextBridge.

declare module '*.md?raw' {
  const content: string
  export default content
}

declare module '*?raw' {
  const content: string
  export default content
}

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

export interface CostSummary {
  configured:      boolean
  limit?:          string
  unit?:           string
  actualSpend?:    string
  forecastedSpend?: string | null
  periodEnd?:      string | null
}

export interface CostServiceAmount {
  service: string
  amount:  string
  unit:    string
}

declare global {
  interface Window {
    electronAPI: {
      loadCredentials:      () => Promise<{ ok: boolean } & Credentials>
      saveCredentials:      (accessKeyId: string, secretAccessKey: string, region: string) => Promise<{ ok: boolean }>
      validateCredentials:  (accessKeyId?: string, secretAccessKey?: string, region?: string) => Promise<{ ok: boolean; error?: string }>
      encryptionAvailable:  () => Promise<{ ok: boolean }>

      describeDatacenter: () => Promise<{ ok: boolean; error?: string } & InstanceInfo>
      startInstance:      (instanceId: string) => Promise<{ ok: boolean; error?: string }>
      stopInstance:       (instanceId: string) => Promise<{ ok: boolean; error?: string }>

      createIamUser:          (username: string, policyArn: string, deleteRootKeys?: boolean) => Promise<{ ok: boolean; error?: string; accessKeyId?: string; secretAccessKey?: string; rootKeysDeleted?: boolean; resumed?: boolean }>
      rotateAccessKey:        () => Promise<{ ok: boolean; error?: string; accessKeyId?: string; secretAccessKey?: string }>
      createBillingAlert:     (amount: number, email: string, phone?: string) => Promise<{ ok: boolean; error?: string }>
      describeBillingAlert:   () => Promise<{ ok: boolean; error?: string; configured?: boolean; amount?: string; email?: string; phone?: string }>
      setIamPasswordPolicy:   () => Promise<{ ok: boolean; error?: string }>
      blockS3PublicAccess:    () => Promise<{ ok: boolean; error?: string }>
      enableGuardDuty:        () => Promise<{ ok: boolean; error?: string }>
      disableGuardDuty:       () => Promise<{ ok: boolean; error?: string }>
      enableAccessAnalyzer:   () => Promise<{ ok: boolean; error?: string }>
      createAnomalyDetection:  (threshold: number, email: string, phone?: string) => Promise<{ ok: boolean; error?: string }>
      describeAnomalyDetection: () => Promise<{ ok: boolean; error?: string; configured?: boolean; threshold?: number; email?: string; phone?: string }>
      enableSmsSecurityAlert:  (phone: string) => Promise<{ ok: boolean; error?: string }>
      disableSmsSecurityAlert: () => Promise<{ ok: boolean; error?: string }>

      getCostSummary:   () => Promise<{ ok: boolean; error?: string } & Partial<CostSummary>>
      getCostBreakdown: () => Promise<{ ok: boolean; error?: string; services?: CostServiceAmount[]; start?: string; end?: string }>

      checkRootCredentials:   () => Promise<{ ok: boolean; error?: string; keysPresent?: boolean; mfaEnabled?: boolean; accountId?: string; isRoot?: boolean; iamMfaEnabled?: boolean; iamUsername?: string }>
      deleteRootAccessKeys:   () => Promise<{ ok: boolean; error?: string }>
      createVirtualMfaDevice: (deviceName?: string) => Promise<{ ok: boolean; error?: string; serialNumber?: string; qrCodePng?: string; base32Seed?: string }>
      enableMfaDevice:        (serialNumber: string, authCode1: string, authCode2: string, userName?: string) => Promise<{ ok: boolean; error?: string }>
      createRootLoginAlarm:   (email: string, phone?: string) => Promise<{ ok: boolean; error?: string }>
      describeRootLoginAlarm: () => Promise<{ ok: boolean; error?: string; configured?: boolean; email?: string; phone?: string }>

      getSessionToken:  (authCode: string, durationSeconds?: number) => Promise<{ ok: boolean; error?: string; expiresAt?: number }>
      getSessionStatus: () => Promise<{ ok: boolean; active?: boolean; expiresAt?: number }>

      readLog:      () => Promise<{ ok: boolean; content?: string }>
      openLogDir:   () => Promise<{ ok: boolean; error?: string }>
      openExternal: (url: string) => Promise<{ ok: boolean; error?: string }>
      logError:     (message: string, stack: string) => Promise<void>
    }
  }
}
