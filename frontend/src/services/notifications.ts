import {
  mapNotificationApiItemToNotificationItem,
  type NotificationItem,
  type NotificationListResponse,
} from '@/types/notification'

const DEFAULT_HOST =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? '127.0.0.1'
    : typeof window !== 'undefined'
      ? window.location.hostname
      : 'localhost'
const COMM_API_BASE_URL = (
  import.meta.env.VITE_COMM_API_BASE_URL || `http://${DEFAULT_HOST}:8002`
).replace(/\/$/, '')

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // Ignore JSON parse failures and use HTTP fallback below.
  }

  return `Request failed with status ${response.status}`
}

export async function fetchNotifications(options: {
  userId: string
  unreadOnly?: boolean
  limit?: number
  offset?: number
}): Promise<NotificationItem[]> {
  const params = new URLSearchParams({
    user_id: options.userId,
    unread_only: String(Boolean(options.unreadOnly)),
    limit: String(options.limit ?? 50),
    offset: String(options.offset ?? 0),
  })

  const response = await fetch(`${COMM_API_BASE_URL}/comm/notifications?${params.toString()}`)

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  const payload = (await response.json()) as NotificationListResponse
  return payload.notifications.map(mapNotificationApiItemToNotificationItem)
}

export async function markNotificationsRead(options: {
  notificationIds: string[]
  recipientUserId?: string
}): Promise<void> {
  const response = await fetch(`${COMM_API_BASE_URL}/comm/notifications/read`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      notification_ids: options.notificationIds,
      recipient_user_id: options.recipientUserId,
    }),
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }
}
