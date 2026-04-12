const DASHBOARD_API_BASE_URL = (
  import.meta.env.VITE_DASHBOARD_API_BASE_URL || 'http://localhost:8004'
).replace(/\/$/, '')

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // Ignore parse failures and fallback to HTTP status.
  }
  return `Request failed with status ${response.status}`
}

export interface AiSummaryResult {
  video_id: string
  summary: string
  source_kind: 'subtitle_text' | 'video_metadata'
  generated_at: string
}

export async function summarizeVideo(payload: {
  videoId: string
  subtitleText?: string
  maxSentences?: number
}): Promise<AiSummaryResult> {
  const response = await fetch(`${DASHBOARD_API_BASE_URL}/ai/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: payload.videoId,
      subtitle_text: payload.subtitleText,
      max_sentences: payload.maxSentences ?? 3,
    }),
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return (await response.json()) as AiSummaryResult
}
