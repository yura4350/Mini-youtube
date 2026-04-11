import { mapVideoApiItemToVideoItem, type VideoApiItem, type VideoItem } from '@/types/video'

const DEFAULT_HOST = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const DASHBOARD_API_BASE_URL = (
  import.meta.env.VITE_DASHBOARD_API_BASE_URL || `http://${DEFAULT_HOST}:8003`
).replace(/\/$/, '')

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // ignore
  }
  return `Request failed with status ${response.status}`
}

export async function fetchRecommended(): Promise<VideoItem[]> {
  const response = await fetch(`${DASHBOARD_API_BASE_URL}/dashboard/recommend`)

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as { videos: VideoApiItem[] }
  return payload.videos.map(mapVideoApiItemToVideoItem)
}

export async function searchVideos(query: string): Promise<VideoItem[]> {
  const response = await fetch(
    `${DASHBOARD_API_BASE_URL}/search?q=${encodeURIComponent(query)}`,
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as { query: string; results: VideoApiItem[] }
  return payload.results.map(mapVideoApiItemToVideoItem)
}

export async function fetchSearchSuggestions(query: string): Promise<string[]> {
  const response = await fetch(
    `${DASHBOARD_API_BASE_URL}/search/suggestions?q=${encodeURIComponent(query)}`,
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as { query: string; suggestions: string[] }
  return payload.suggestions
}
