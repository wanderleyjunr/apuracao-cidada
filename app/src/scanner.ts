// Continuous QR reading from the camera (zxing-cpp in WASM), with a photo as fallback.
import { prepareZXingModule, readBarcodes } from 'zxing-wasm/reader'
import wasmUrl from 'zxing-wasm/reader/zxing_reader.wasm?url'

// WASM served by the app itself (not the default CDN) so it works offline.
prepareZXingModule({ overrides: { locateFile: (p: string) => (p.endsWith('.wasm') ? wasmUrl : p) } })

const OPTIONS = { formats: ['QRCode'] as const, tryHarder: true, maxNumberOfSymbols: 8 }

export async function readImage(img: Blob | ImageData): Promise<string[]> {
  const r = await readBarcodes(img, OPTIONS as never)
  return r.filter(b => b.isValid).map(b => b.text)
}

/** Opens the rear camera and calls onRead for each new QR. Returns a stop function. */
export async function startCamera(video: HTMLVideoElement, onRead: (text: string) => void): Promise<() => void> {
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1920 } }, audio: false })
  video.srcObject = stream
  await video.play()
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!
  const seen = new Set<string>()
  let active = true
  const loop = async () => {
    if (!active) return
    if (video.videoWidth) {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0)
      for (const t of await readImage(ctx.getImageData(0, 0, canvas.width, canvas.height))) {
        if (!seen.has(t)) { seen.add(t); navigator.vibrate?.(40); onRead(t) }
      }
    }
    setTimeout(loop, 250)
  }
  loop()
  return () => { active = false; stream.getTracks().forEach(t => t.stop()) }
}
