<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/icons/AppIcon.vue'
import type { NotificationItem } from '@/types/notification'
import { fetchNotifications, markNotificationsRead } from '@/services/notifications'

const authStore = useAuthStore()
const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const unreadOnly = ref(false)
const notifications = ref<NotificationItem[]>([])

const unreadCount = computed(() => notifications.value.filter((item) => !item.isRead).length)

function notifyBadgeRefresh() {
  window.dispatchEvent(new CustomEvent('notifications-updated'))
}

async function loadNotifications() {
  if (!authStore.currentUser) return

  loading.value = true
  errorMessage.value = ''

  try {
    notifications.value = await fetchNotifications({
      userId: authStore.currentUser.id,
      unreadOnly: unreadOnly.value,
      limit: 100,
      offset: 0,
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load notifications.'
  } finally {
    loading.value = false
    notifyBadgeRefresh()
  }
}

function formatType(type: NotificationItem['type']): string {
  if (type === 'new_video') return 'New video'
  return 'Subscription'
}

async function markOneAsRead(item: NotificationItem) {
  if (item.isRead || !authStore.currentUser) return

  try {
    await markNotificationsRead({
      notificationIds: [item.id],
      recipientUserId: authStore.currentUser.id,
    })
    item.isRead = true
    item.readAt = new Date().toISOString()
    notifyBadgeRefresh()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to mark notification as read.'
  }
}

async function openNotification(item: NotificationItem) {
  if (!authStore.currentUser) return

  if (!item.isRead) {
    await markOneAsRead(item)
  }

  if (item.videoId) {
    router.push({ name: 'video-player', params: { id: item.videoId } })
  }
}

async function markAllAsRead() {
  if (!authStore.currentUser) return

  const unreadIds = notifications.value.filter((item) => !item.isRead).map((item) => item.id)
  if (unreadIds.length === 0) return

  try {
    await markNotificationsRead({
      notificationIds: unreadIds,
      recipientUserId: authStore.currentUser.id,
    })

    const now = new Date().toISOString()
    notifications.value = notifications.value.map((item) => {
      if (unreadIds.includes(item.id)) {
        return {
          ...item,
          isRead: true,
          readAt: now,
        }
      }
      return item
    })

    notifyBadgeRefresh()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to mark all as read.'
  }
}

onMounted(() => {
  loadNotifications()
})
</script>

<template>
  <main class="notifications-page">
    <section class="inbox-shell">
      <header class="inbox-header">
        <div>
          <h1><AppIcon name="bell" :size="18" /> Notification Inbox</h1>
          <p>See new video alerts and subscription updates.</p>
        </div>

        <div class="header-actions">
          <button class="ghost" :class="{ active: unreadOnly }" @click="unreadOnly = !unreadOnly; loadNotifications()">
            <AppIcon name="filter" :size="14" />
            {{ unreadOnly ? 'Showing unread' : 'Show unread only' }}
          </button>
          <button @click="markAllAsRead" :disabled="unreadCount === 0">
            <AppIcon name="check" :size="14" /> Mark all as read
          </button>
        </div>
      </header>

      <section v-if="loading" class="status-box">Loading notifications...</section>

      <section v-else-if="errorMessage" class="status-box error-box">
        <p>{{ errorMessage }}</p>
        <button class="ghost" @click="loadNotifications">Retry</button>
      </section>

      <section v-else-if="notifications.length === 0" class="status-box">
        <AppIcon name="empty" :size="18" />
        <p>No notifications yet.</p>
      </section>

      <section v-else class="notification-list">
        <article
          v-for="item in notifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.isRead }"
          @click="openNotification(item)"
        >
          <div class="item-main">
            <p class="item-type">{{ formatType(item.type) }}</p>
            <h2>{{ item.title }}</h2>
            <p class="item-message">{{ item.message }}</p>
            <small>
              <AppIcon name="clock" :size="12" />
              {{ new Date(item.createdAt).toLocaleString() }}
            </small>
          </div>

          <div class="item-actions">
            <span v-if="!item.isRead" class="pill">Unread</span>
            <span v-else class="pill read">Read</span>
              <button class="ghost" :disabled="item.isRead" @click.stop="markOneAsRead(item)">
              <AppIcon name="check" :size="14" /> Mark read
            </button>
          </div>
        </article>
      </section>
    </section>
  </main>
</template>

<style scoped>
.notifications-page {
  max-width: 1060px;
  margin: 0 auto;
  padding: 20px 16px 34px;
}

.inbox-shell {
  border: 1px solid rgba(255, 255, 255, 0.13);
  border-radius: 16px;
  background: #171717;
  padding: 14px;
}

.inbox-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.inbox-header h1 {
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
}

.inbox-header p {
  color: #aeb4c0;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: 9px;
  padding: 8px 11px;
  color: #fff;
  background: linear-gradient(135deg, #dc2626, #ef4444);
  cursor: pointer;
}

button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

button.ghost {
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: transparent;
}

button.ghost.active {
  border-color: rgba(239, 68, 68, 0.75);
  background: rgba(220, 38, 38, 0.18);
}

.status-box {
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #d5dae3;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-box {
  justify-content: space-between;
}

.notification-list {
  display: grid;
  gap: 10px;
}

.notification-item {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  background: #1f1f1f;
  padding: 12px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: border-color 120ms ease, transform 120ms ease;
}

.notification-item:hover {
  border-color: rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

.notification-item.unread {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: inset 3px 0 0 rgba(220, 38, 38, 0.95);
}

.item-main h2 {
  color: #fff;
  font-size: 17px;
  line-height: 1.35;
}

.item-type {
  color: #fda4af;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.item-message {
  color: #c7ccd6;
  margin-top: 4px;
}

.item-main small {
  margin-top: 7px;
  color: #9ca3af;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.item-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.pill {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  border: 1px solid rgba(239, 68, 68, 0.65);
  color: #ffe4e6;
  background: rgba(220, 38, 38, 0.2);
}

.pill.read {
  border-color: rgba(255, 255, 255, 0.25);
  color: #d1d5db;
  background: rgba(255, 255, 255, 0.05);
}

@media (max-width: 820px) {
  .inbox-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .notification-item {
    flex-direction: column;
  }

  .item-actions {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
