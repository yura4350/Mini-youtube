import { mapVideoApiItemToVideoItem, type VideoApiItem, type VideoItem } from '@/types/video'

const DASHBOARD_API_BASE_URL = (
  import.meta.env.VITE_DASHBOARD_API_BASE_URL || 'http://localhost:8003'
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

/**
 * Fetch search history for a user.
 * @param userId - The ID of the user.
 * @param limit - The maximum number of history items to fetch (default: 10).
 * @returns A promise resolving to the user's search history.
 */
export async function fetchSearchHistory(userId: string, limit: number = 10): Promise<{ query: string; searched_at: string }[]> {
    const response = await fetch(
        `${DASHBOARD_API_BASE_URL}/search/history?user_id=${encodeURIComponent(userId)}&limit=${limit}`
    );

    if (!response.ok) {
        throw new Error(`Failed to fetch search history: ${response.statusText}`);
    }

    const payload = (await response.json()) as { user_id: string; history: { query: string; searched_at: string }[] };
    return payload.history;
}

export interface WatchedVideo extends VideoItem {
  lastWatchedAt: string
  lastPositionSeconds: number
}

/**
 * Fetch watched video history for a user.
 * @param userId - The ID of the user.
 * @param limit - The maximum number of history items to fetch (default: 20).
 * @returns A promise resolving to the user's watched video history.
 */
export async function fetchWatchedHistory(userId: string, limit: number = 20): Promise<WatchedVideo[]> {
  const response = await fetch(
    `${DASHBOARD_API_BASE_URL}/user/history/watched?user_id=${encodeURIComponent(userId)}&limit=${limit}`,
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as {
    user_id: string
    videos: Array<VideoApiItem & { last_watched_at: string; last_position_seconds: number }>
  }
  return payload.videos.map((v) => ({
    ...mapVideoApiItemToVideoItem(v),
    lastWatchedAt: v.last_watched_at,
    lastPositionSeconds: v.last_position_seconds,
  }))
}

/**
 * Record or update a watch event for a user.
 * @param userId - The ID of the user.
 * @param videoId - The ID of the video.
 * @param positionSeconds - The watch position in seconds.
 */
export async function recordWatchEvent(userId: string, videoId: string, positionSeconds: number = 0): Promise<void> {
  const response = await fetch(
    `${DASHBOARD_API_BASE_URL}/user/history/watched?user_id=${encodeURIComponent(userId)}&video_id=${encodeURIComponent(videoId)}&position_seconds=${positionSeconds}`,
    { method: 'POST' },
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }
}

/**
 * Fetch subscription feed for a user.
 * @param userId - The ID of the user.
 * @param limit - The maximum number of videos to fetch (default: 20, max: 100).
 * @returns A promise resolving to videos from subscribed channels.
 */
export async function fetchSubscriptionsFeed(userId: string, limit: number = 20): Promise<VideoItem[]> {
  const response = await fetch(
    `${DASHBOARD_API_BASE_URL}/subscriptions/feed?user_id=${encodeURIComponent(userId)}&limit=${limit}`,
  )

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as { user_id: string; videos: VideoApiItem[] }
  return payload.videos.map(mapVideoApiItemToVideoItem)
}
