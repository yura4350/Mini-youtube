export interface UserNotification {
  id: string
  type: 'new_video' | 'subscription' | 'chat' | 'system'
  message: string
  timestamp: string
  read: boolean
  videoId?: string
}

export interface User {
  id: string
  username: string
  email: string
  bio: string
  avatar: string
  isAdmin: boolean
  subscribedTo: string[]
  notifications: UserNotification[]
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthResult {
  ok: boolean
  message: string
  user: User | null
}
