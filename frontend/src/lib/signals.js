import { apiFetch } from './api'

/**
 * Tiny client used by the student practice/adaptive pages to push biosignal
 * samples to the backend. Headband + face-rec scripts can either:
 *   1) call window.AL_signals.pushCognitive([...]) directly, OR
 *   2) POST to /api/signals/{cognitive|face} with the student's bearer token.
 *
 * Buffers samples and flushes every `flushMs` (default 1000ms) so we don't
 * hammer the API once per EEG sample.
 */
export function createSignalRecorder({ sessionId, flushMs = 1000 } = {}) {
  if (!sessionId) throw new Error('sessionId required')

  let cogBuf  = []
  let faceBuf = []
  let timer   = null
  let stopped = false

  const flush = async () => {
    if (cogBuf.length) {
      const samples = cogBuf; cogBuf = []
      try { await apiFetch('/api/signals/cognitive', { method: 'POST', body: { session_id: sessionId, samples } }) }
      catch (e) { console.warn('[signals] cognitive flush failed', e) }
    }
    if (faceBuf.length) {
      const samples = faceBuf; faceBuf = []
      try { await apiFetch('/api/signals/face', { method: 'POST', body: { session_id: sessionId, samples } }) }
      catch (e) { console.warn('[signals] face flush failed', e) }
    }
  }

  const start = () => {
    if (timer) return
    timer = setInterval(() => { if (!stopped) flush() }, flushMs)
  }

  const stop = async () => {
    stopped = true
    if (timer) { clearInterval(timer); timer = null }
    await flush()
  }

  const api = {
    sessionId,
    pushCognitive: (sample) => {
      if (Array.isArray(sample)) cogBuf.push(...sample); else cogBuf.push(sample)
    },
    pushFace: (sample) => {
      if (Array.isArray(sample)) faceBuf.push(...sample); else faceBuf.push(sample)
    },
    flush,
    stop,
    start,
  }

  // expose globally so partner scripts running in the same tab can find it
  window.AL_signals = api
  start()
  return api
}