import { mapVideoApiItemToVideoItem, type VideoApiItem, type VideoItem } from '@/types/video'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // Ignore JSON parse failures and use HTTP fallback below.
  }

  return `Request failed with status ${response.status}`
}

export async function fetchVideos(): Promise<VideoItem[]> {
  const response = await fetch(`${API_BASE_URL}/videos`)

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as VideoApiItem[]
  return payload.map(mapVideoApiItemToVideoItem)
}
