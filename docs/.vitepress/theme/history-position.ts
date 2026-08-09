const HISTORY_POSITION_KEY = '__ddnsHistoryPosition'

export interface HistoryPosition {
  session: string
  index: number
}

type TrackedWindow = Window & {
  __ddnsHistoryPositionTracking?: boolean
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function readHistoryPosition(state: unknown): HistoryPosition | null {
  if (!isRecord(state)) return null
  const position = state[HISTORY_POSITION_KEY]
  if (
    !isRecord(position) ||
    typeof position.session !== 'string' ||
    typeof position.index !== 'number' ||
    !Number.isInteger(position.index)
  ) {
    return null
  }
  return { session: position.session, index: position.index }
}

function withHistoryPosition(state: unknown, position: HistoryPosition): Record<string, unknown> {
  return {
    ...(isRecord(state) ? state : {}),
    [HISTORY_POSITION_KEY]: position,
  }
}

export function installHistoryPositionTracking() {
  if (typeof window === 'undefined') return
  const trackedWindow = window as TrackedWindow
  if (trackedWindow.__ddnsHistoryPositionTracking) return
  trackedWindow.__ddnsHistoryPositionTracking = true

  const originalPushState = window.history.pushState.bind(window.history)
  const originalReplaceState = window.history.replaceState.bind(window.history)
  const existingPosition = readHistoryPosition(window.history.state)
  const session =
    existingPosition?.session ||
    `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
  const initialPosition = existingPosition || { session, index: 0 }

  originalReplaceState(withHistoryPosition(window.history.state, initialPosition), '')

  const trackedPushState: History['pushState'] = (state, unused, url) => {
    const current = readHistoryPosition(window.history.state)
    const index = current?.session === session ? current.index + 1 : 0
    originalPushState(withHistoryPosition(state, { session, index }), unused, url)
  }
  const trackedReplaceState: History['replaceState'] = (state, unused, url) => {
    const current = readHistoryPosition(window.history.state)
    const position = current?.session === session ? current : initialPosition
    originalReplaceState(withHistoryPosition(state, position), unused, url)
  }

  window.history.pushState = trackedPushState
  window.history.replaceState = trackedReplaceState
}
