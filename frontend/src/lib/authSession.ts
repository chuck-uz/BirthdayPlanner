type UnauthorizedHandler = () => void

let onUnauthorized: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler
}

export function notifyUnauthorized(): void {
  onUnauthorized?.()
}

const BLOCKED_FLAG = 'bp_account_blocked'

let onAccountBlocked: UnauthorizedHandler | null = null

export function setAccountBlockedHandler(handler: UnauthorizedHandler | null): void {
  onAccountBlocked = handler
}

export function notifyAccountBlocked(): void {
  try {
    sessionStorage.setItem(BLOCKED_FLAG, '1')
  } catch {
    /* ignore */
  }
  onAccountBlocked?.()
}

export function readAndClearAccountBlockedFlag(): boolean {
  try {
    if (sessionStorage.getItem(BLOCKED_FLAG) === '1') {
      sessionStorage.removeItem(BLOCKED_FLAG)
      return true
    }
  } catch {
    /* ignore */
  }
  return false
}
