<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/icons/AppIcon.vue'
import { fetchNotifications } from '@/services/notifications'
import { authService } from '@/services/auth'
import type { NotificationItem } from '@/types/notification'
import type { User } from '@/types/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const searchInput = ref('')
const unreadNotificationCount = ref(0)
const notificationOpen = ref(false)
const notificationLoading = ref(false)
const recentNotifications = ref<NotificationItem[]>([])
const notificationCenterRef = ref<HTMLElement | null>(null)

const showSearch = computed(() => route.name !== 'login' && route.name !== 'register')

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

  const users = authService.getAllUsers().filter((user) => user.id !== currentUser.id)
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

onMounted(() => {
  authStore.hydrate()
  refreshUnreadNotifications()
  window.addEventListener('notifications-updated', handleNotificationsUpdated)
  window.addEventListener('click', closeNotificationCenterByOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('notifications-updated', handleNotificationsUpdated)
  window.removeEventListener('click', closeNotificationCenterByOutsideClick)
})

watch(
  () => authStore.currentUser?.id,
  () => {
    refreshUnreadNotifications()
  },
)

function logout() {
  authStore.logout()
  router.push('/login')
}

function submitSearch() {
  const keyword = searchInput.value.trim()
  if (!keyword) return
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
        <input v-model="searchInput" type="text" placeholder="Search videos" />
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
                <p>{{ item.title }}</p>
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
  background: rgba(7, 8, 10, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.searchbar {
  flex: 1;
  max-width: 640px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin: 0 16px;
}

.searchbar input {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #121212;
  color: #fff;
  padding: 9px 14px;
}

.searchbar button {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: #202020;
  color: #fff;
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
  color: #fff;
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
  background: linear-gradient(135deg, #dc2626, #ef4444);
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
  color: #d4d7de;
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
  color: #d4d7de;
  border: none;
  background: transparent;
  font-size: 14px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
}

.notify-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
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
  background: #ef4444;
  color: #fff;
  border: 1px solid rgba(0, 0, 0, 0.45);
}

.notify-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 320px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: #141414;
  padding: 10px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.38);
}

.notify-dropdown header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notify-dropdown h3 {
  color: #fff;
  font-size: 14px;
}

.mini-btn {
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: transparent;
  color: #f3f4f6;
  border-radius: 7px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.dropdown-loading {
  color: #9ca3af;
  font-size: 13px;
  margin-top: 8px;
}

.dropdown-list {
  margin-top: 8px;
  display: grid;
  gap: 6px;
}

.dropdown-item {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
}

.dropdown-item.unread {
  border-color: rgba(239, 68, 68, 0.65);
  background: rgba(220, 38, 38, 0.16);
}

.dropdown-item p {
  color: #e5e7eb;
  font-size: 13px;
}

.dropdown-item small {
  color: #9ca3af;
  font-size: 11px;
}

.dropdown-separator {
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  margin: 10px 0;
}

.peer-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.peer-chip {
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: #1d1d1d;
  color: #e5e7eb;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
}

.peer-chip:hover {
  border-color: rgba(239, 68, 68, 0.75);
  background: rgba(220, 38, 38, 0.18);
}

.topnav a.router-link-exact-active,
.topnav a:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: transparent;
  color: #fff;
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
