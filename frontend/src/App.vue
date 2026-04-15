<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/icons/AppIcon.vue'
import { connectNotificationStream, fetchNotifications } from '@/services/notifications'
import { fetchSearchSuggestions, fetchSubscribedChannelIds } from '@/services/dashboard'
import { authService } from '@/services/auth'
import type { NotificationItem } from '@/types/notification'
import type { User } from '@/types/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const searchInput = ref('')
const suggestions = ref<string[]>([])
const showSuggestions = ref(false)
let suggestionsDebounce: ReturnType<typeof setTimeout> | null = null
const unreadNotificationCount = ref(0)
const notificationOpen = ref(false)
const notificationLoading = ref(false)
const recentNotifications = ref<NotificationItem[]>([])
const notificationCenterRef = ref<HTMLElement | null>(null)
let disconnectNotificationStream: (() => void) | null = null
let notificationStreamReconnectTimer: ReturnType<typeof setTimeout> | null = null
const notificationStreamUserId = ref<string | null>(null)
const notificationStreamShouldReconnect = ref(false)
let notificationFallbackPollTimer: ReturnType<typeof setInterval> | null = null
const allUsers = ref<User[]>([])

const QUICK_NOTIFICATION_TITLE_MAX_LENGTH = 72

const showSearch = computed(() => route.name !== 'login' && route.name !== 'register')

function truncateText(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength - 3).trimEnd()}...`
}

function quickNotificationTitle(value: string): string {
  return truncateText(value, QUICK_NOTIFICATION_TITLE_MAX_LENGTH)
}

async function refreshUserDirectory() {
  if (!authStore.currentUser) {
    allUsers.value = []
    return
  }
  allUsers.value = await authService.getAllUsers()
}

async function refreshSubscribedChannels() {
  const currentUser = authStore.currentUser
  if (!currentUser) return

  try {
    const channelIds = await fetchSubscribedChannelIds(currentUser.id)
    if (authStore.currentUser?.id === currentUser.id) {
      authStore.currentUser.subscribedTo = channelIds
    }
  } catch {
    // Keep existing values if sync fails.
  }
}

async function refreshUnreadNotifications() {
  if (!authStore.currentUser) {
    unreadNotificationCount.value = 0
    recentNotifications.value = []
    return
  }

  try {
    const items = await fetchNotifications({
      userId: authStore.currentUser.id,
      unreadOnly: true,
      limit: 200,
      offset: 0,
    })
    unreadNotificationCount.value = items.length
  } catch {
    unreadNotificationCount.value = 0
  }
}

const quickPeers = computed<User[]>(() => {
  const currentUser = authStore.currentUser
  if (!currentUser) return []

  const users = allUsers.value.filter((user) => user.id !== currentUser.id)
  const subscribed = new Set(currentUser.subscribedTo)
  const preferred = users.filter((user) => subscribed.has(user.id))
  const source = preferred.length > 0 ? preferred : users
  return source.slice(0, 4)
})

async function openNotificationCenter() {
  notificationOpen.value = true
  if (!authStore.currentUser) return

  notificationLoading.value = true
  try {
    const items = await fetchNotifications({
      userId: authStore.currentUser.id,
      unreadOnly: false,
      limit: 6,
      offset: 0,
    })
    recentNotifications.value = items
  } catch {
    recentNotifications.value = []
  } finally {
    notificationLoading.value = false
  }
}

function toggleNotificationCenter() {
  if (notificationOpen.value) {
    notificationOpen.value = false
    return
  }
  openNotificationCenter()
}

function closeNotificationCenterByOutsideClick(event: MouseEvent) {
  if (!notificationOpen.value || !notificationCenterRef.value) return
  const target = event.target as Node | null
  if (target && notificationCenterRef.value.contains(target)) return
  notificationOpen.value = false
}

function goToInbox() {
  notificationOpen.value = false
  router.push({ name: 'notifications' })
}

function goToMessages(peerId?: string) {
  notificationOpen.value = false
  if (peerId) {
    router.push({ name: 'messages', query: { peer: peerId } })
    return
  }
  router.push({ name: 'messages' })
}

function handleNotificationsUpdated() {
  refreshUnreadNotifications()
}

function stopNotificationStream() {
  if (disconnectNotificationStream) {
    disconnectNotificationStream()
    disconnectNotificationStream = null
  }
  if (notificationStreamReconnectTimer) {
    clearTimeout(notificationStreamReconnectTimer)
    notificationStreamReconnectTimer = null
  }
  notificationStreamShouldReconnect.value = false
  notificationStreamUserId.value = null
  if (notificationFallbackPollTimer) {
    clearInterval(notificationFallbackPollTimer)
    notificationFallbackPollTimer = null
  }
}

function startNotificationStream(userId: string) {
  stopNotificationStream()
  notificationStreamUserId.value = userId
  notificationStreamShouldReconnect.value = true

  const connect = () => {
    if (!notificationStreamShouldReconnect.value || notificationStreamUserId.value !== userId) return

    disconnectNotificationStream = connectNotificationStream({
      userId,
      onNotification: () => {
        refreshUnreadNotifications()
        if (notificationOpen.value) {
          openNotificationCenter()
        }
        window.dispatchEvent(new CustomEvent('notifications-updated'))
      },
      onStatusChange: (status) => {
        if (status === 'error' || status === 'disconnected') {
          if (!notificationStreamShouldReconnect.value || notificationStreamUserId.value !== userId) return
          if (notificationStreamReconnectTimer) clearTimeout(notificationStreamReconnectTimer)
          notificationStreamReconnectTimer = setTimeout(connect, 1500)
        }
      },
    })
  }

  connect()

  // Fallback: keep unread badge in sync even if WS is blocked/intermittent.
  if (notificationFallbackPollTimer) {
    clearInterval(notificationFallbackPollTimer)
  }
  notificationFallbackPollTimer = setInterval(() => {
    if (authStore.currentUser?.id !== userId) return
    refreshUnreadNotifications()
    if (notificationOpen.value) {
      openNotificationCenter()
    }
  }, 7000)
}

onMounted(() => {
  authStore.hydrate()
  refreshUnreadNotifications()
  refreshUserDirectory()
  refreshSubscribedChannels()
  window.addEventListener('notifications-updated', handleNotificationsUpdated)
  window.addEventListener('click', closeNotificationCenterByOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('notifications-updated', handleNotificationsUpdated)
  window.removeEventListener('click', closeNotificationCenterByOutsideClick)
  stopNotificationStream()
})

watch(
  () => authStore.currentUser?.id,
  (userId) => {
    refreshUnreadNotifications()
    if (!userId) {
      allUsers.value = []
      stopNotificationStream()
      return
    }
    startNotificationStream(userId)
    refreshUserDirectory()
    refreshSubscribedChannels()
  },
  { immediate: true },
)

function logout() {
  stopNotificationStream()
  authStore.logout()
  router.push('/login')
}

function onSearchInput() {
  const q = searchInput.value.trim()
  if (suggestionsDebounce) clearTimeout(suggestionsDebounce)
  if (!q) {
    suggestions.value = []
    showSuggestions.value = false
    return
  }
  suggestionsDebounce = setTimeout(async () => {
    try {
      suggestions.value = await fetchSearchSuggestions(q)
      showSuggestions.value = suggestions.value.length > 0
    } catch {
      suggestions.value = []
      showSuggestions.value = false
    }
  }, 200)
}

function selectSuggestion(s: string) {
  searchInput.value = s
  showSuggestions.value = false
  router.push({ name: 'search', query: { q: s } })
}

function submitSearch() {
  const keyword = searchInput.value.trim()
  if (!keyword) return
  showSuggestions.value = false
  router.push({ name: 'search', query: { q: keyword } })
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-icon" aria-hidden="true"><AppIcon name="play" :size="14" :stroke-width="1.9" /></span>
        <span>Media Hub</span>
      </RouterLink>

      <form v-if="showSearch" class="searchbar" @submit.prevent="submitSearch">
        <div class="search-input-wrap">
          <input
            v-model="searchInput"
            type="text"
            placeholder="Search videos"
            autocomplete="off"
            @input="onSearchInput"
            @blur="showSuggestions = false"
          />
          <ul v-if="showSuggestions" class="suggestions-list">
            <li
              v-for="s in suggestions"
              :key="s"
              @mousedown.prevent="selectSuggestion(s)"
            >{{ s }}</li>
          </ul>
        </div>
        <button type="submit" class="search-btn"><AppIcon name="search" :size="16" /> Search</button>
      </form>

      <nav class="topnav">
        <RouterLink to="/"><AppIcon name="home" :size="16" /> Home</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated" to="/upload"
          ><AppIcon name="upload" :size="16" /> Upload</RouterLink
        >
        <div v-if="authStore.isAuthenticated" ref="notificationCenterRef" class="notify-center">
          <button class="notify-trigger" @click.stop="toggleNotificationCenter">
            <span class="notify-icon-wrap">
              <AppIcon name="bell" :size="16" />
              <span v-if="unreadNotificationCount > 0" class="notify-badge">
                {{ unreadNotificationCount > 99 ? '99+' : unreadNotificationCount }}
              </span>
            </span>
            Notifications
          </button>

          <section v-if="notificationOpen" class="notify-dropdown" @click.stop>
            <header>
              <h3>Notification Center</h3>
              <button class="mini-btn" @click="goToInbox">Open inbox</button>
            </header>

            <div v-if="notificationLoading" class="dropdown-loading">Loading...</div>
            <div v-else-if="recentNotifications.length === 0" class="dropdown-loading">No recent notifications.</div>
            <div v-else class="dropdown-list">
              <article
                v-for="item in recentNotifications"
                :key="item.id"
                class="dropdown-item"
                :class="{ unread: !item.isRead }"
                @click="goToInbox"
              >
                <p>{{ quickNotificationTitle(item.title) }}</p>
                <small>{{ new Date(item.createdAt).toLocaleString() }}</small>
              </article>
            </div>

            <div class="dropdown-separator"></div>
            <header>
              <h3>Quick Chats</h3>
              <button class="mini-btn" @click="goToMessages()">Open messages</button>
            </header>
            <div v-if="quickPeers.length === 0" class="dropdown-loading">No contacts yet.</div>
            <div v-else class="peer-list">
              <button v-for="peer in quickPeers" :key="peer.id" class="peer-chip" @click="goToMessages(peer.id)">
                {{ peer.username }}
              </button>
            </div>
          </section>
        </div>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login"
          ><AppIcon name="login" :size="16" /> Login</RouterLink
        >
        <RouterLink v-if="!authStore.isAuthenticated" to="/register"
          ><AppIcon name="register" :size="16" /> Register</RouterLink
        >
        <RouterLink v-if="authStore.isAuthenticated" to="/profile"
          ><AppIcon name="user" :size="16" /> Profile</RouterLink
        >
        <RouterLink
          v-if="authStore.isAuthenticated && authStore.currentUser?.isAdmin"
          to="/admin"
          ><AppIcon name="admin" :size="16" /> Admin</RouterLink
        >
        <button v-if="authStore.isAuthenticated" class="logout-btn" @click="logout">
          <AppIcon name="logout" :size="16" /> Logout
        </button>
      </nav>
    </header>

    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  height: 68px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(8px);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--border-default);
}

.searchbar {
  flex: 1;
  max-width: 640px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin: 0 16px;
}

.search-input-wrap {
  position: relative;
}

.searchbar input {
  width: 100%;
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--bg-3);
  color: var(--text-main);
  padding: 9px 14px;
}

.suggestions-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-1);
  border: 1px solid var(--border-medium);
  border-radius: 12px;
  list-style: none;
  margin: 0;
  padding: 4px 0;
  z-index: 20;
  box-shadow: var(--shadow-dropdown);
}

.suggestions-list li {
  padding: 8px 14px;
  color: var(--text-subtle);
  font-size: 14px;
  cursor: pointer;
}

.suggestions-list li:hover {
  background: var(--overlay-hover);
  color: var(--text-main);
}

.searchbar button {
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--surface-raised);
  color: var(--text-main);
  padding: 9px 14px;
  cursor: pointer;
}

.search-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  color: var(--text-main);
  text-decoration: none;
  letter-spacing: 0.03em;
  font-weight: 700;
}

.brand-icon {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 11px;
  color: var(--text-inverse);
  background: linear-gradient(135deg, var(--accent), var(--accent-soft));
}

.topnav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topnav a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-subtle);
  text-decoration: none;
  font-size: 14px;
  padding: 8px 10px;
  border-radius: 8px;
}

.notify-link {
  position: relative;
}

.notify-center {
  position: relative;
}

.notify-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-subtle);
  border: none;
  background: transparent;
  font-size: 14px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
}

.notify-trigger:hover {
  background: var(--overlay-hover-mid);
  color: var(--text-main);
}

.notify-icon-wrap {
  position: relative;
  display: inline-flex;
}

.notify-badge {
  position: absolute;
  right: -10px;
  top: -9px;
  min-width: 18px;
  height: 18px;
  border-radius: 999px;
  padding: 0 5px;
  font-size: 11px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--text-inverse);
  border: 1px solid rgba(0, 0, 0, 0.45);
}

.notify-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 320px;
  border-radius: 12px;
  border: 1px solid var(--border-medium);
  background: var(--bg-2);
  padding: 10px;
  box-shadow: var(--shadow-dropdown-lg);
}

.notify-dropdown header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notify-dropdown h3 {
  color: var(--text-main);
  font-size: 14px;
}

.mini-btn {
  border: 1px solid var(--border-heavy);
  background: transparent;
  color: var(--text-main);
  border-radius: 7px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.dropdown-loading {
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 8px;
}

.dropdown-list {
  margin-top: 8px;
  display: grid;
  gap: 6px;
  max-height: 210px;
  overflow-y: auto;
  padding-right: 2px;
}

.dropdown-item {
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
}

.dropdown-item.unread {
  border-color: var(--accent-outline);
  background: var(--accent-wash);
}

.dropdown-item p {
  color: var(--text-body);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-item small {
  color: var(--text-muted);
  font-size: 11px;
}

.dropdown-separator {
  border-top: 1px solid var(--border-default);
  margin: 10px 0;
}

.peer-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.peer-chip {
  border: 1px solid var(--border-medium);
  background: var(--surface-chip);
  color: var(--text-body);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
}

.peer-chip:hover {
  border-color: var(--accent-outline-soft);
  background: var(--accent-wash-hover);
}

.topnav a.router-link-exact-active,
.topnav a:hover {
  background: var(--overlay-hover-mid);
  color: var(--text-main);
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--border-extra);
  background: transparent;
  color: var(--text-main);
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
}

@media (max-width: 740px) {
  .topbar {
    height: auto;
    padding: 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .searchbar {
    width: 100%;
    max-width: none;
    margin: 0;
  }

  .topnav {
    width: 100%;
    flex-wrap: wrap;
  }

  .notify-dropdown {
    right: auto;
    left: 0;
    width: min(92vw, 320px);
  }
}
</style>
