import type { AuthResult, LoginPayload, RegisterPayload, User } from '@/types/auth'

const USERS_KEY = 'media_frontend_users'
const CURRENT_USER_KEY = 'media_frontend_current_user_id'

const seedUsers: User[] = [
  {
    id: '1',
    username: 'TechExplorer',
    email: 'tech@example.com',
    bio: 'Tech enthusiast sharing the latest in technology',
    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    isAdmin: false,
    subscribedTo: ['2', '3'],
    notifications: [],
  },
  {
    id: 'admin',
    username: 'admin',
    email: 'admin@example.com',
    bio: 'Platform Administrator',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
    isAdmin: true,
    subscribedTo: [],
    notifications: [],
  },
]

function readUsers(): User[] {
  const raw = localStorage.getItem(USERS_KEY)
  if (!raw) {
    localStorage.setItem(USERS_KEY, JSON.stringify(seedUsers))
    return [...seedUsers]
  }

  try {
    const parsed = JSON.parse(raw) as User[]
    if (!Array.isArray(parsed)) {
      return [...seedUsers]
    }
    return parsed
  } catch {
    return [...seedUsers]
  }
}

function writeUsers(users: User[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function findUserById(userId: string | null): User | null {
  if (!userId) return null
  const users = readUsers()
  return users.find((u) => u.id === userId) ?? null
}

function login(payload: LoginPayload): AuthResult {
  const users = readUsers()
  const matched = users.find((u) => u.email.toLowerCase() === payload.email.toLowerCase())

  if (!matched || payload.password.trim().length === 0) {
    return {
      ok: false,
      message: 'Invalid email or password.',
      user: null,
    }
  }

  localStorage.setItem(CURRENT_USER_KEY, matched.id)

  return {
    ok: true,
    message: 'Login successful.',
    user: matched,
  }
}

function register(payload: RegisterPayload): AuthResult {
  const users = readUsers()
  const exists = users.some((u) => u.email.toLowerCase() === payload.email.toLowerCase())

  if (exists) {
    return {
      ok: false,
      message: 'This email is already registered.',
      user: null,
    }
  }

  const newUser: User = {
    id: crypto.randomUUID(),
    username: payload.username,
    email: payload.email,
    bio: 'A brand new creator on the platform.',
    avatar: 'https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=150',
    isAdmin: false,
    subscribedTo: [],
    notifications: [],
  }

  users.push(newUser)
  writeUsers(users)
  localStorage.setItem(CURRENT_USER_KEY, newUser.id)

  return {
    ok: true,
    message: 'Registration successful.',
    user: newUser,
  }
}

function getCurrentUser(): User | null {
  const userId = localStorage.getItem(CURRENT_USER_KEY)
  return findUserById(userId)
}

function updateCurrentUser(update: Pick<User, 'username' | 'bio'>): AuthResult {
  const currentUser = getCurrentUser()
  if (!currentUser) {
    return {
      ok: false,
      message: 'No active user session.',
      user: null,
    }
  }

  const users = readUsers()
  const nextUsers = users.map((u) => {
    if (u.id !== currentUser.id) return u
    return {
      ...u,
      username: update.username.trim(),
      bio: update.bio.trim(),
    }
  })

  writeUsers(nextUsers)

  const refreshed = nextUsers.find((u) => u.id === currentUser.id) ?? null
  return {
    ok: true,
    message: 'Profile updated successfully.',
    user: refreshed,
  }
}

function logout() {
  localStorage.removeItem(CURRENT_USER_KEY)
}

export const authService = {
  login,
  register,
  getCurrentUser,
  updateCurrentUser,
  logout,
}
