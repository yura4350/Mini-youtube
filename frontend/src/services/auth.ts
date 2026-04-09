import type { AuthResult, LoginPayload, RegisterPayload, User, BackendUser, BackendToken } from '@/types/auth'

// Use the environment variable of where the backend is hosted
const AUTH_API_BASE_URL = (
  import.meta.env.VITE_AUTH_API_BASE_URL || 'http://localhost:8003'
).replace(/\/$/, '')

// Simple String constants, names to save and retrieve data in the browser's localStorage
const ACCESS_TOKEN_KEY = 'media_frontend_access_token'
const CURRENT_USER_KEY = 'media_frontend_current_user'

// Maps the data returned by a backend to the frontend
function mapBackendUser(u: BackendUser): User {
  return {
    id: String(u.id),
    username: u.name,
    email: u.email,
    bio: '',
    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    isAdmin: u.role === 'admin',
    subscribedTo: [],
    notifications: [],
  }
}

// Wrappers around the browser's localStorage API
// NOTE: localStorage can only save text strings, when saving the user object, it uses JSON.stringify(user) to convert the object to a string. When getting the user back,
// it uses JSON.parse(raw) to turn the string back into a usable JavaScript object
function saveToken(token: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

function getToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

function saveCurrentUser(user: User | null) {
  if (!user) {
    localStorage.removeItem(CURRENT_USER_KEY)
    return
  }
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user))
}

function getCurrentUser(): User | null {
  const raw = localStorage.getItem(CURRENT_USER_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

// Takes a JWT token, attaches it to the HTTP headers as a Bearer token, and asks the backend for the current user's profile data
// If successful, it runs that data through the mapBackendUser function), saves the mapped user to localStorage, and returns it
async function fetchProfile(token: string): Promise<User | null> {
  const response = await fetch(`${AUTH_API_BASE_URL}/profile/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) return null

  const backendUser = (await response.json()) as BackendUser
  const mapped = mapBackendUser(backendUser)
  saveCurrentUser(mapped)
  return mapped
}

// login flow
async function login(payload: LoginPayload): Promise<AuthResult> {
  try {
    // OAuth2PasswordRequestForm expects x-www-form-urlencoded + "username"
    const form = new URLSearchParams()
    form.set('username', payload.email.trim())
    form.set('password', payload.password)

    const response = await fetch(`${AUTH_API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: form.toString(),
    })

    if (!response.ok) {
      return {
        ok: false,
        message: 'Invalid email or password.',
        user: null,
      }
    }

    const tokenBody = (await response.json()) as BackendToken
    saveToken(tokenBody.access_token)

    const user = await fetchProfile(tokenBody.access_token)
    if (!user) {
      logout()
      return {
        ok: false,
        message: 'Login succeeded but profile fetch failed.',
        user: null,
      }
    }

    return {
      ok: true,
      message: 'Login successful.',
      user,
    }
  } catch {
    return {
      ok: false,
      message: 'Unable to reach auth service.',
      user: null,
    }
  }
}

// register flow
async function register(payload: RegisterPayload): Promise<AuthResult> {
  try {
    const response = await fetch(`${AUTH_API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: payload.username, // backend expects "name"
        email: payload.email,
        role: 'user', // backend requires role - for now automatically hardcode to user
        password: payload.password,
      }),
    })

    if (!response.ok) {
      const err = (await response.json().catch(() => null)) as { detail?: string } | null
      return {
        ok: false,
        message: err?.detail ?? 'Registration failed.',
        user: null,
      }
    }

    // backend register returns user, not token -> auto-login
    return await login({
      email: payload.email,
      password: payload.password,
    })
  } catch {
    return {
      ok: false,
      message: 'Unable to reach auth service.',
      user: null,
    }
  }
}

// resume to restore the local session (Should be replaced with JWT?)
async function hydrateCurrentUser(): Promise<User | null> {
  const token = getToken()
  if (!token) return null

  const user = await fetchProfile(token)
  if (!user) logout()
  return user
}

// Keep compatibility with existing UI code that calls getAllUsers()
function getAllUsers(): User[] {
  const current = getCurrentUser()
  return current ? [current] : []
}

// Keep local profile update for now (backend endpoint currently expects full UserCreate)
function updateCurrentUser(update: Pick<User, 'username' | 'bio'>): AuthResult {
  const current = getCurrentUser()
  if (!current) {
    return {
      ok: false,
      message: 'No active user session.',
      user: null,
    }
  }

  const next: User = {
    ...current,
    username: update.username.trim(),
    bio: update.bio.trim(),
  }

  saveCurrentUser(next)
  return {
    ok: true,
    message: 'Profile updated locally.',
    user: next,
  }
}

// logout 
function logout() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(CURRENT_USER_KEY)
}

// bundle all the functions into the authService object and exports it, so that other parts of React/Vue app can use them
export const authService = {
  login,
  register,
  hydrateCurrentUser,
  getCurrentUser,
  getAllUsers,
  updateCurrentUser,
  logout,
}